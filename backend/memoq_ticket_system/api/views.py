from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.contrib.auth import get_user_model
from django.db.models import Q, F, ExpressionWrapper, fields, Prefetch, Case, When, Value, BooleanField
from django.db.models.functions import Now
from django.shortcuts import get_object_or_404
from django.conf import settings
from urllib.parse import urlencode # For building query strings

from rest_framework import viewsets, permissions, status, filters, generics
from rest_framework.decorators import action, api_view, permission_classes as drf_permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from memoq_ticket_system.models import (
    Company, CompanyConfig, Ticket, TicketReply, TicketStatusHistory,
    NotificationConfig, NotificationLog, Attachment, CustomerTypeTag,
    # WebhookTemplate, # REMOVED THIS LINE - WebhookTemplate was superseded
    TicketType, TicketLabel, TicketTransferHistory,
    CompanySSOProvider, NotificationTemplate, TicketSatisfactionRating
)
from .serializers import (
    CompanySerializer, CompanyConfigSerializer, UserSerializer,
    TicketSerializer, TicketReplySerializer, TicketStatusHistorySerializer,
    NotificationConfigSerializer, NotificationLogSerializer, AttachmentSerializer,
    TicketAssignmentSerializer, SupportStaffTicketStatsSerializer,
    CustomerTypeTagSerializer, TicketTypeSerializer, TicketLabelSerializer, TicketTransferHistorySerializer,
    CompanySSOProviderSerializer, NotificationTemplateSerializer, TicketSatisfactionRatingSerializer,
    AdminTicketDashboardSerializer,
    PublicCompanyDetailsSerializer
)
from .permissions import (
    IsSystemAdminRole, IsTechnicalSupportAdminRole, IsSupportRole, IsCompanyMember,
    IsSupportOrTechnicalSupportAdminOrSystemAdmin, IsTechnicalSupportAdminOrSystemAdmin,
    CanManageCompany, CanManageSupportUsers, IsOwnerOrSupportOrAdmin,
    IsTicketFollowerOrCreator, CanViewCompanyTickets, CanManageTicketTypes,
    CanManageTicketLabels, CanTransferTicket, CanPauseTicket
    # Add CanAssignTicket and CanViewTicketOrReplyAttachment if they are custom
)
from .pagination_integration import (
    StandardResultsSetPagination, SmallResultsSetPagination, MediumResultsSetPagination
)
from ..notifications import NotificationManager
# from ..utils import render_template_string_with_context # Assuming this exists

User = get_user_model()


# --- New Serializer for Public Company Details ---
# Already defined in the previous version, ensure it's correctly placed if not in a separate file
# class PublicCompanyDetailsSerializer(serializers.ModelSerializer): ...

# --- New Public View for Company Branding ---
class PublicCompanyDetailsBySlugView(generics.RetrieveAPIView):
    queryset = Company.objects.filter(is_active=True)
    serializer_class = PublicCompanyDetailsSerializer
    permission_classes = [AllowAny]
    lookup_field = 'ticket_submission_url_slug'
    lookup_url_kwarg = 'slug'

# --- New View for OAuth Initiation ---
class OAuthInitiateView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    OAUTH_PROVIDER_URLS = {
        'feishu': 'https://passport.feishu.cn/suite/passport/oauth/authorize',
        'enterprise_wechat': 'https://open.work.weixin.qq.com/wwopen/sso/qrConnect',
        'wechat': 'https://open.weixin.qq.com/connect/qrconnect',
    }

    def get(self, request, platform, *args, **kwargs):
        company_slug = request.query_params.get('company_slug')
        frontend_redirect_uri = request.query_params.get('frontend_redirect_uri')

        if not platform or platform not in self.OAUTH_PROVIDER_URLS:
            return Response({"error": "不支持的SSO平台或平台未指定。"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not frontend_redirect_uri:
            return Response({"error": "缺少前端回调URI参数 (frontend_redirect_uri)。"}, status=status.HTTP_400_BAD_REQUEST)

        company = None
        sso_config = None

        if company_slug:
            company = get_object_or_404(Company, ticket_submission_url_slug=company_slug, is_active=True)
            try:
                sso_config = CompanySSOProvider.objects.get(company=company, provider_type=platform, is_enabled=True)
            except CompanySSOProvider.DoesNotExist:
                return Response({"error": f"公司 '{company.name}' 未启用或未配置 {platform} SSO。"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "缺少公司标识 (company_slug)。"}, status=status.HTTP_400_BAD_REQUEST)

        if not sso_config or not sso_config.app_id:
            return Response({"error": f"{platform} SSO的App ID未配置。"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        backend_callback_uri = request.build_absolute_uri(
             # The platform is now part of the query string for the callback view
            f'/api/auth/oauth/callback/?platform={platform}&company_slug={company_slug}&frontend_redirect_uri={frontend_redirect_uri}'
        )
        
        params = {}
        if platform == 'feishu':
            params = {
                'app_id': sso_config.app_id,
                'redirect_uri': backend_callback_uri,
                'response_type': 'code',
            }
        elif platform == 'enterprise_wechat':
            params = {
                'appid': sso_config.app_id, 
                'agentid': sso_config.agent_id, 
                'redirect_uri': backend_callback_uri,
                'response_type': 'code',
                'scope': 'snsapi_base', 
            }
        elif platform == 'wechat':
            params = {
                'appid': sso_config.app_id,
                'redirect_uri': backend_callback_uri,
                'response_type': 'code',
                'scope': 'snsapi_login',
            }
        else:
            return Response({"error": f"平台 {platform} 的OAuth参数构建逻辑未实现。"}, status=status.HTTP_501_NOT_IMPLEMENTED)

        authorization_url = f"{self.OAUTH_PROVIDER_URLS[platform]}?{urlencode(params)}"
        return HttpResponseRedirect(authorization_url)


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            username = request.data.get('username')
            try:
                # Attempt to find user by username or email
                user = User.objects.get(Q(username=username) | Q(email=username), is_deleted=False, is_active=True)
                response.data['user'] = UserSerializer(user, context={'request': request}).data
            except User.DoesNotExist:
                # This case should ideally be caught by SimpleJWT's authentication if user doesn't exist or password mismatch
                # If user exists but is inactive/deleted, SimpleJWT should also prevent login.
                # This block is more of a fallback or for adding extra info if needed.
                pass 
            except User.MultipleObjectsReturned:
                # Handle cases where email might not be unique if username is the primary login field
                # Or if username is not unique across non-deleted active users (should not happen with default User model)
                pass 
        return response

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsTechnicalSupportAdminOrSystemAdmin] 

    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.role == User.ROLE_SYSTEM_ADMIN:
            return User.all_objects.all().order_by('id') 
        return User.objects.none() # Should not be reached due to permission class

    @action(detail=True, methods=['post'], permission_classes=[IsTechnicalSupportAdminOrSystemAdmin])
    def soft_delete_user(self, request, pk=None):
        user = get_object_or_404(User.all_objects, pk=pk)
        if user == request.user:
            return Response({"detail": "您不能软删除自己的账户。"}, status=status.HTTP_400_BAD_REQUEST)
        user.soft_delete()
        return Response({"detail": f"用户 {user.username} 已被软删除。"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsTechnicalSupportAdminOrSystemAdmin])
    def restore_user(self, request, pk=None):
        user = get_object_or_404(User.all_objects, pk=pk)
        user.restore()
        return Response({"detail": f"用户 {user.username} 已被恢复。"}, status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        # Hard delete, ensure permissions are very strict
        if not (self.request.user.is_superuser or self.request.user.role == User.ROLE_SYSTEM_ADMIN):
            raise PermissionDenied("您没有权限硬删除用户。请使用软删除。")
        # Consider logging this action or having a two-step confirmation for hard deletes.
        super().perform_destroy(instance)


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.prefetch_related('sso_providers', 'customer_types').all().order_by('name')
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated, IsTechnicalSupportAdminOrSystemAdmin]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'contact_person', 'contact_email']
    ordering_fields = ['name', 'created_at', 'importance']

class CompanySSOProviderViewSet(viewsets.ModelViewSet):
    queryset = CompanySSOProvider.objects.select_related('company').all().order_by('company__name', 'provider_type')
    serializer_class = CompanySSOProviderSerializer
    permission_classes = [IsAuthenticated, IsTechnicalSupportAdminOrSystemAdmin]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['company__name', 'provider_type', 'app_id']
    ordering_fields = ['company__name', 'provider_type', 'is_enabled']

    def get_queryset(self):
        queryset = super().get_queryset()
        company_id = self.request.query_params.get('company_id')
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        return queryset

    def perform_create(self, serializer):
        company_id = self.request.data.get('company') # Assuming company ID is passed in request data
        if not company_id:
             # If company is part of the URL (e.g., nested router), get it from there
            company_id = self.kwargs.get('company_pk') # Example if using nested router
        
        if not company_id:
            raise ValidationError({"company": "必须提供公司ID。"})

        company = get_object_or_404(Company, pk=company_id)
        provider_type = serializer.validated_data.get('provider_type')

        if CompanySSOProvider.objects.filter(company=company, provider_type=provider_type).exists():
            raise ValidationError(f"{company.name} 的 {provider_type} SSO配置已存在。")
        serializer.save(company=company) # Explicitly pass company object

    def perform_update(self, serializer):
        # Prevent changing company or provider_type if they form a unique constraint that's hard to manage on update
        # For simplicity, assume they are not changed or handle unique_together validation carefully.
        serializer.save()


class CompanyConfigViewSet(viewsets.ModelViewSet):
    queryset = CompanyConfig.objects.select_related('company').all()
    serializer_class = CompanyConfigSerializer
    permission_classes = [IsAuthenticated, IsTechnicalSupportAdminOrSystemAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ['company__name']

class TicketTypeViewSet(viewsets.ModelViewSet):
    queryset = TicketType.objects.filter(is_active=True).order_by('tree_id', 'lft')
    serializer_class = TicketTypeSerializer
    permission_classes = [IsAuthenticated, CanManageTicketTypes]
    pagination_class = SmallResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

class TicketLabelViewSet(viewsets.ModelViewSet):
    queryset = TicketLabel.objects.all().order_by('name')
    serializer_class = TicketLabelSerializer
    permission_classes = [IsAuthenticated, CanManageTicketLabels]
    pagination_class = SmallResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']


class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated] 
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['id', 'title', 'description', 'company__name', 'created_by__username', 'assigned_to__username', 'ticket_type__name', 'labels__name']
    ordering_fields = ['created_at', 'last_activity_at', 'priority', 'status', 'urgency', 'sla_ir_deadline', 'sla_resolution_deadline']

    def get_queryset(self):
        user = self.request.user
        queryset = Ticket.objects.select_related(
            'company', 'company__config', 'created_by', 'submitted_by', 'assigned_to', 'ticket_type', 'satisfaction_rating'
        ).prefetch_related(
            'labels', 'followers', 'attachments',
            Prefetch('replies', queryset=TicketReply.objects.select_related('user').prefetch_related('attachments').order_by('created_at')),
            Prefetch('status_history', queryset=TicketStatusHistory.objects.select_related('changed_by').order_by('created_at')),
            Prefetch('transfer_history', queryset=TicketTransferHistory.objects.select_related('transferred_by', 'transferred_from', 'transferred_to').order_by('created_at'))
        ).distinct()

        if user.role == User.ROLE_SYSTEM_ADMIN or user.role == User.ROLE_TECHNICAL_SUPPORT_ADMIN:
            pass
        elif user.role == User.ROLE_SUPPORT:
            queryset = queryset.filter(Q(assigned_to=user) | Q(status='pending_assignment')) 
        elif user.role == User.ROLE_CUSTOMER:
            if not user.company: return Ticket.objects.none()
            queryset = queryset.filter(Q(company=user.company)).distinct()
        else:
            return Ticket.objects.none()
        
        status_param = self.request.query_params.get('status')
        if status_param: queryset = queryset.filter(status=status_param)
        company_id_param = self.request.query_params.get('company_id')
        if company_id_param: queryset = queryset.filter(company_id=company_id_param)
        assigned_to_param = self.request.query_params.get('assigned_to_id')
        if assigned_to_param:
            if assigned_to_param == 'unassigned': queryset = queryset.filter(assigned_to__isnull=True)
            else: queryset = queryset.filter(assigned_to_id=assigned_to_param)
        return queryset.order_by('-last_activity_at')

    def perform_create(self, serializer):
        ticket = serializer.save(created_by=self.request.user, submitted_by=self.request.user)
        # Notification via signal

    def perform_update(self, serializer):
        original_ticket = self.get_object()
        original_status = original_ticket.status
        # Assuming 'updated_by' field exists on Ticket model or handled by a mixin
        # For now, we'll just update last_activity_at
        ticket = serializer.save(last_activity_at=timezone.now()) 
        if ticket.status != original_status:
            TicketStatusHistory.objects.create(
                ticket=ticket, changed_by=self.request.user,
                old_status=original_status, new_status=ticket.status,
                reason=self.request.data.get("status_change_reason", "")
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsTechnicalSupportAdminOrSystemAdmin]) # More specific permission
    def assign(self, request, pk=None):
        ticket = self.get_object()
        serializer = TicketAssignmentSerializer(data=request.data) # Ensure this serializer exists
        if serializer.is_valid():
            assigned_to_id = serializer.validated_data['assigned_to_id']
            user_to_assign = get_object_or_404(User, pk=assigned_to_id)
            if user_to_assign.role not in [User.ROLE_SUPPORT, User.ROLE_TECHNICAL_SUPPORT_ADMIN]:
                return Response({"detail": "只能分配给技术支持或技术支持管理员。"}, status=status.HTTP_400_BAD_REQUEST)
            
            original_assigned_to = ticket.assigned_to
            ticket.assigned_to = user_to_assign
            if ticket.status == 'pending_assignment' or ticket.status == 'new_issue':
                ticket.status = 'in_progress'
            ticket.last_activity_at = timezone.now()
            ticket.save(update_fields=['assigned_to', 'status', 'last_activity_at'])

            if original_assigned_to != user_to_assign:
                 TicketTransferHistory.objects.create(
                    ticket=ticket, transferred_by=request.user,
                    transferred_from=original_assigned_to, transferred_to=user_to_assign,
                    reason=request.data.get("assignment_reason", "工单分配")
                )
            return Response(TicketSerializer(ticket, context={'request': request}).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanTransferTicket])
    def transfer(self, request, pk=None):
        ticket = self.get_object()
        # Assuming TicketAssignmentSerializer can be reused or a specific TransferSerializer exists
        serializer = TicketAssignmentSerializer(data=request.data, context={'field_name': 'transferred_to_id'}) 
        if serializer.is_valid():
            transferred_to_id = serializer.validated_data['assigned_to_id'] # Adjust if field name is different
            user_to_transfer = get_object_or_404(User, pk=transferred_to_id)
            if user_to_transfer.role not in [User.ROLE_SUPPORT, User.ROLE_TECHNICAL_SUPPORT_ADMIN]:
                 return Response({"detail": "只能转移给技术支持或技术支持管理员。"}, status=status.HTTP_400_BAD_REQUEST)
            
            original_assigned_to = ticket.assigned_to
            if original_assigned_to == user_to_transfer:
                return Response({"detail": "工单已分配给此用户。"}, status=status.HTTP_400_BAD_REQUEST)

            ticket.assigned_to = user_to_transfer
            ticket.last_activity_at = timezone.now()
            ticket.save(update_fields=['assigned_to', 'last_activity_at'])
            TicketTransferHistory.objects.create(
                ticket=ticket, transferred_by=request.user,
                transferred_from=original_assigned_to, transferred_to=user_to_transfer,
                reason=request.data.get("transfer_reason", "工单转移") # Ensure frontend sends this
            )
            # Trigger notification for transfer
            return Response(TicketSerializer(ticket, context={'request': request}).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanPauseTicket])
    def pause(self, request, pk=None):
        ticket = self.get_object()
        if ticket.status == 'paused':
            return Response({"detail": "工单已处于暂停状态。"}, status=status.HTTP_400_BAD_REQUEST)
        pause_reason = request.data.get('pause_reason')
        if not pause_reason:
            return Response({"detail": "必须提供暂停原因。"}, status=status.HTTP_400_BAD_REQUEST)
        
        original_status = ticket.status
        ticket.status = 'paused'
        ticket.pause_reason = pause_reason
        ticket.paused_at = timezone.now()
        ticket.last_activity_at = timezone.now() # Pausing is an activity
        ticket.save(update_fields=['status', 'pause_reason', 'paused_at', 'last_activity_at'])
        TicketStatusHistory.objects.create(
            ticket=ticket, changed_by=request.user,
            old_status=original_status, new_status='paused', reason=f"暂停: {pause_reason}"
        )
        # Trigger notification for pause
        return Response(TicketSerializer(ticket, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanPauseTicket]) # Same permission for resume
    def resume(self, request, pk=None):
        ticket = self.get_object()
        if ticket.status != 'paused':
            return Response({"detail": "工单未处于暂停状态。"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Determine status to revert to.
        # Logic: Find the last non-paused status from history, or a sensible default.
        last_meaningful_status_entry = TicketStatusHistory.objects.filter(ticket=ticket).exclude(new_status='paused').order_by('-created_at').first()
        previous_status_before_pause = last_meaningful_status_entry.old_status if last_meaningful_status_entry and last_meaningful_status_entry.new_status == 'paused' else 'in_progress'
        if not previous_status_before_pause or previous_status_before_pause == 'paused': # Fallback
            previous_status_before_pause = 'in_progress' if ticket.assigned_to else 'pending_assignment'


        original_status = ticket.status # Should be 'paused'
        ticket.status = previous_status_before_pause
        ticket.pause_reason = None 
        ticket.paused_at = None
        ticket.last_activity_at = timezone.now()
        ticket.save(update_fields=['status', 'pause_reason', 'paused_at', 'last_activity_at'])
        TicketStatusHistory.objects.create(
            ticket=ticket, changed_by=request.user,
            old_status=original_status, new_status=ticket.status, reason="工单恢复"
        )
        # Trigger notification for resume
        return Response(TicketSerializer(ticket, context={'request': request}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsTicketFollowerOrCreator])
    def add_reply(self, request, pk=None):
        ticket = self.get_object()
        serializer = TicketReplySerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            if ticket.status in ['closed', 'resolved'] and not request.user.is_staff:
                 return Response({"detail": "已关闭或已解决的工单不能回复。"}, status=status.HTTP_400_BAD_REQUEST)
            serializer.save(user=request.user, ticket=ticket)
            # Notification for new reply handled by signals.py
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated]) 
    def rate_ticket(self, request, pk=None):
        ticket = self.get_object()
        if ticket.status not in ['closed', 'resolved']: # Only rate after resolution/closure
            return Response({"detail": "只能对已关闭或已解决的工单进行评价。"}, status=status.HTTP_400_BAD_REQUEST)
        if TicketSatisfactionRating.objects.filter(ticket=ticket).exists():
            return Response({"detail": "此工单已被评价。"}, status=status.HTTP_400_BAD_REQUEST)
        
        is_creator_or_submitter = request.user == ticket.created_by or request.user == ticket.submitted_by
        if not is_creator_or_submitter:
             raise PermissionDenied("只有工单创建者或提交者可以评价。")

        serializer = TicketSatisfactionRatingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(ticket=ticket, rated_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[IsTechnicalSupportAdminOrSystemAdmin])
    def pending_assignment_tickets(self, request):
        tickets = self.get_queryset().filter(status__in=['new_issue', 'pending_assignment']).order_by('created_at')
        page = self.paginate_queryset(tickets)
        serializer_context = {'request': request}
        if page is not None:
            serializer = AdminTicketDashboardSerializer(page, many=True, context=serializer_context)
            return self.get_paginated_response(serializer.data)
        serializer = AdminTicketDashboardSerializer(tickets, many=True, context=serializer_context)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsTechnicalSupportAdminOrSystemAdmin])
    def sla_ir_monitoring(self, request):
        now = timezone.now()
        warning_hours_before = int(request.query_params.get('warning_hours', 1))
        warning_threshold = now + timedelta(hours=warning_hours_before)
        base_queryset = self.get_queryset().exclude(status__in=['closed', 'resolved', 'paused'])

        approaching_ir = base_queryset.filter(
            first_replied_at__isnull=True, sla_ir_deadline__isnull=False,
            sla_ir_deadline__gt=now, sla_ir_deadline__lte=warning_threshold
        ).order_by('sla_ir_deadline')

        missed_ir = base_queryset.filter(
            Q(first_replied_at__isnull=True, sla_ir_deadline__isnull=False, sla_ir_deadline__lt=now) |
            Q(first_replied_at__isnull=False, sla_ir_deadline__isnull=False, first_replied_at__gt=F('sla_ir_deadline'))
        ).order_by('sla_ir_deadline')

        serializer_context = {'request': request}
        # For simplicity, not paginating dashboard widgets here, but could be added
        return Response({
            "approaching_ir_sla": AdminTicketDashboardSerializer(approaching_ir, many=True, context=serializer_context).data,
            "missed_ir_sla": AdminTicketDashboardSerializer(missed_ir, many=True, context=serializer_context).data,
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsTechnicalSupportAdminOrSystemAdmin])
    def sla_resolution_monitoring(self, request):
        now = timezone.now()
        warning_hours_before = int(request.query_params.get('warning_hours', 24))
        warning_threshold = now + timedelta(hours=warning_hours_before)
        base_queryset = self.get_queryset().exclude(status__in=['closed', 'resolved', 'paused'])

        approaching_resolution = base_queryset.filter(
            resolved_at__isnull=True, sla_resolution_deadline__isnull=False,
            sla_resolution_deadline__gt=now, sla_resolution_deadline__lte=warning_threshold
        ).order_by('sla_resolution_deadline')

        missed_resolution = base_queryset.filter(
            Q(resolved_at__isnull=True, sla_resolution_deadline__isnull=False, sla_resolution_deadline__lt=now) |
            Q(resolved_at__isnull=False, sla_resolution_deadline__isnull=False, resolved_at__gt=F('sla_resolution_deadline'))
        ).order_by('sla_resolution_deadline')
        
        serializer_context = {'request': request}
        return Response({
            "approaching_resolution_sla": AdminTicketDashboardSerializer(approaching_resolution, many=True, context=serializer_context).data,
            "missed_resolution_sla": AdminTicketDashboardSerializer(missed_resolution, many=True, context=serializer_context).data,
        })

    @action(detail=False, methods=['get'], permission_classes=[IsTechnicalSupportAdminOrSystemAdmin])
    def idle_tickets_monitoring(self, request):
        idle_days_threshold = int(request.query_params.get('idle_days', 3)) 
        idle_since_date = timezone.now() - timedelta(days=idle_days_threshold)
        
        idle_tickets = self.get_queryset().filter(
            last_activity_at__lt=idle_since_date,
        ).exclude(status__in=['closed', 'resolved', 'paused']).order_by('last_activity_at') 

        serializer_context = {'request': request}
        return Response({
            "idle_tickets": AdminTicketDashboardSerializer(idle_tickets, many=True, context=serializer_context).data,
        })


class TicketReplyViewSet(viewsets.ModelViewSet):
    queryset = TicketReply.objects.select_related('user', 'ticket').prefetch_related('attachments').all().order_by('created_at')
    serializer_class = TicketReplySerializer
    permission_classes = [IsAuthenticated, IsOwnerOrSupportOrAdmin]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        ticket_id = self.request.query_params.get('ticket_id')
        if ticket_id:
            ticket = get_object_or_404(Ticket, pk=ticket_id)
            if not (user.is_staff or user.role in [User.ROLE_SYSTEM_ADMIN, User.ROLE_TECHNICAL_SUPPORT_ADMIN, User.ROLE_SUPPORT] or 
                    (user.role == User.ROLE_CUSTOMER and user.company == ticket.company)):
                raise PermissionDenied("您没有权限查看此工单的回复。")
            return super().get_queryset().filter(ticket_id=ticket_id)
        
        if user.is_staff or user.role in [User.ROLE_SYSTEM_ADMIN, User.ROLE_TECHNICAL_SUPPORT_ADMIN, User.ROLE_SUPPORT]:
            return super().get_queryset()
        elif user.role == User.ROLE_CUSTOMER and user.company:
            return super().get_queryset().filter(ticket__company=user.company)
        return TicketReply.objects.none()

    def perform_create(self, serializer):
        ticket_id = self.request.data.get('ticket')
        ticket = get_object_or_404(Ticket, pk=ticket_id)
        
        can_reply = False
        if self.request.user.is_staff or self.request.user.role in [User.ROLE_SYSTEM_ADMIN, User.ROLE_TECHNICAL_SUPPORT_ADMIN, User.ROLE_SUPPORT]:
            can_reply = True
        elif self.request.user == ticket.created_by or self.request.user == ticket.submitted_by:
            can_reply = True
        elif self.request.user in ticket.followers.all():
            can_reply = True
        elif ticket.company and self.request.user.company == ticket.company:
            can_reply = True
        
        if not can_reply:
            raise PermissionDenied("您没有权限回复此工单。")
        if ticket.status in ['closed', 'resolved'] and not self.request.user.is_staff:
             raise ValidationError("已关闭或已解决的工单不能回复。")

        reply = serializer.save(user=self.request.user, ticket=ticket)
        # Notification for new reply is handled by signals.py

class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.select_related('uploaded_by', 'ticket', 'reply').all()
    serializer_class = AttachmentSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated] 

    # Define CanViewTicketOrReplyAttachment permission class
    # class CanViewTicketOrReplyAttachment(permissions.BasePermission):
    #     def has_object_permission(self, request, view, obj_attachment):
    #         # ... (implementation as sketched before)
    #         pass

    # def get_permissions(self):
    #     if self.action == 'download':
    #         return [IsAuthenticated(), CanViewTicketOrReplyAttachment()]
    #     return super().get_permissions()
    # ... (perform_create and download actions - ensure storage_backend is used)

class NotificationConfigViewSet(viewsets.ModelViewSet):
    queryset = NotificationConfig.objects.all()
    serializer_class = NotificationConfigSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == User.ROLE_SYSTEM_ADMIN:
            return NotificationConfig.objects.all()
        return NotificationConfig.objects.filter(user=user)

class NotificationTemplateViewSet(viewsets.ModelViewSet):
    queryset = NotificationTemplate.objects.select_related('company').all().order_by('company__name', 'name')
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAuthenticated, IsTechnicalSupportAdminOrSystemAdmin]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'company__name', 'event_type', 'channel']
    ordering_fields = ['name', 'company__name', 'event_type', 'channel', 'is_active']

    def get_queryset(self):
        queryset = super().get_queryset()
        company_id = self.request.query_params.get('company_id')
        if company_id:
            queryset = queryset.filter(Q(company_id=company_id) | Q(company__isnull=True))
        elif not (self.request.user.is_superuser or self.request.user.role == User.ROLE_SYSTEM_ADMIN):
             if self.request.user.company:
                 queryset = queryset.filter(Q(company=self.request.user.company) | Q(company__isnull=True))
             else: 
                 queryset = queryset.filter(company__isnull=True)
        return queryset

class NotificationLogViewSet(viewsets.ReadOnlyModelViewSet): 
    queryset = NotificationLog.objects.select_related('user', 'company', 'ticket').all().order_by('-created_at')
    serializer_class = NotificationLogSerializer
    permission_classes = [IsAuthenticated, IsTechnicalSupportAdminOrSystemAdmin]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['ticket__id', 'user__username', 'company__name', 'notification_type', 'status', 'recipient_info']
    ordering_fields = ['created_at', 'sent_at', 'status', 'notification_type']

class TicketSatisfactionRatingViewSet(viewsets.ModelViewSet):
    queryset = TicketSatisfactionRating.objects.select_related('ticket', 'rated_by').all()
    serializer_class = TicketSatisfactionRatingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == User.ROLE_SYSTEM_ADMIN:
            return TicketSatisfactionRating.objects.all().order_by('-created_at')
        if user.company:
            return TicketSatisfactionRating.objects.filter(
                Q(rated_by=user) | Q(ticket__company=user.company)
            ).order_by('-created_at')
        return TicketSatisfactionRating.objects.filter(rated_by=user).order_by('-created_at')

    def perform_create(self, serializer):
        ticket_id = self.request.data.get('ticket')
        ticket = get_object_or_404(Ticket, pk=ticket_id)
        
        if ticket.status not in ['closed', 'resolved']:
             raise ValidationError("只能对已关闭或已解决的工单进行评价。")
        if TicketSatisfactionRating.objects.filter(ticket=ticket).exists():
             raise ValidationError("此工单已被评价。")
        
        is_creator_or_submitter = self.request.user == ticket.created_by or self.request.user == ticket.submitted_by
        if not is_creator_or_submitter:
            raise PermissionDenied("只有工单创建者或提交者可以评价。")

        serializer.save(rated_by=self.request.user, ticket=ticket)

class CustomerTypeTagViewSet(viewsets.ModelViewSet):
    queryset = CustomerTypeTag.objects.all().order_by('name')
    serializer_class = CustomerTypeTagSerializer
    permission_classes = [IsAuthenticated, IsTechnicalSupportAdminOrSystemAdmin]

def home(request):
    return HttpResponse("<h1>MemoQ Ticket System API</h1><p>欢迎来到 MemoQ 工单系统 API.</p>")

