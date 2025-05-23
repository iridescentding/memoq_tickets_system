from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import FileResponse, Http404
from django.conf import settings
import os

from ..models import Attachment, Ticket, Reply
from .serializers import AttachmentSerializer
from ..file_storage import TencentCOSStorage, SecureFileStorage  # 导入两种存储方式

# 根据配置选择存储后端
if settings.DEFAULT_FILE_STORAGE_BACKEND == "cos":
    storage_backend = TencentCOSStorage()
    print("Using Tencent COS for file storage.")
elif settings.DEFAULT_FILE_STORAGE_BACKEND == "local":
    storage_backend = SecureFileStorage()
    print("Using local file storage.")
else:
    # 默认或配置错误时回退到本地存储，并在日志中记录警告
    print(
        f"Warning: Unknown DEFAULT_FILE_STORAGE_BACKEND '{settings.DEFAULT_FILE_STORAGE_BACKEND}'. Falling back to local storage."
    )
    storage_backend = SecureFileStorage()


class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Attachment.objects.all()
        # 普通用户只能查看自己公司工单的附件
        if hasattr(user, "company") and user.company:
            return Attachment.objects.filter(ticket__company=user.company)
        return Attachment.objects.none()

    def perform_create(self, serializer):
        uploaded_file = self.request.data.get("file")
        if not uploaded_file:
            raise serializers.ValidationError("No file provided.")

        is_valid, error_message = storage_backend.validate_file(uploaded_file)
        if not is_valid:
            raise serializers.ValidationError(error_message)

        ticket_id = self.request.data.get("ticket")
        reply_id = self.request.data.get("reply", None)

        # 检查用户是否有权限为该工单/回复上传附件
        if ticket_id:
            try:
                ticket = Ticket.objects.get(id=ticket_id)
                if not (
                    self.request.user.is_staff
                    or self.request.user.company == ticket.company
                ):
                    raise permissions.PermissionDenied(
                        "You do not have permission to upload attachments to this ticket."
                    )
            except Ticket.DoesNotExist:
                raise serializers.ValidationError("Ticket not found.")

        if reply_id:
            try:
                reply = Reply.objects.get(id=reply_id)
                if not (
                    self.request.user.is_staff
                    or self.request.user.company == reply.ticket.company
                ):
                    raise permissions.PermissionDenied(
                        "You do not have permission to upload attachments to this reply."
                    )
            except Reply.DoesNotExist:
                raise serializers.ValidationError("Reply not found.")

        try:
            file_info = storage_backend.save_attachment(
                uploaded_file, ticket_id=ticket_id, reply_id=reply_id
            )
            serializer.save(
                uploaded_by=self.request.user,
                original_name=file_info["original_name"],
                file_name=file_info[
                    "file_name"
                ],  # 对于COS，这可能是unique_filename；对于本地，也是unique_filename
                file_path=file_info[
                    "file_path"
                ],  # 对于COS，这是cos_key；对于本地，这是相对路径
                file_size=file_info["file_size"],
                content_type=file_info["content_type"],
                storage_type=file_info["storage_type"],  # 保存存储类型
            )
        except Exception as e:
            # Log the exception e
            print(f"Error saving attachment: {str(e)}")
            raise serializers.ValidationError(f"Could not save file: {str(e)}")

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        attachment = self.get_object()

        # 权限检查：确保用户可以下载此附件
        user = request.user
        if not (
            user.is_staff
            or user.is_superuser
            or (hasattr(user, "company") and user.company == attachment.ticket.company)
        ):
            raise permissions.PermissionDenied(
                "You do not have permission to download this attachment."
            )

        if attachment.storage_type == "cos":
            # 获取预签名URL并重定向
            file_url = storage_backend.get_file_url(
                attachment.file_path
            )  # file_path is cos_key
            if file_url:
                attachment.download_count += 1
                attachment.save()
                return Response({"download_url": file_url}, status=status.HTTP_200_OK)
            else:
                raise Http404("File not found or URL generation failed.")
        elif attachment.storage_type == "local":
            if not storage_backend.file_exists(attachment.file_path):
                raise Http404("File not found on local storage.")

            file_full_path = storage_backend.get_file_path(attachment.file_path)
            try:
                response = FileResponse(
                    open(file_full_path, "rb"),
                    as_attachment=True,
                    filename=attachment.original_name,
                )
                attachment.download_count += 1
                attachment.save()
                return response
            except FileNotFoundError:
                raise Http404("File not found on local storage.")
            except Exception as e:
                print(f"Error serving local file: {str(e)}")
                raise Http404("Error serving file.")
        else:
            raise Http404(f"Unknown storage type: {attachment.storage_type}")

    def perform_destroy(self, instance):
        # 权限检查已由ModelViewSet的permission_classes处理，但可在此处添加更细致的逻辑
        if instance.storage_type == "cos":
            deleted = storage_backend.delete_file(
                instance.file_path
            )  # file_path is cos_key
            if not deleted:
                # 可以选择是否在此处引发错误，或者只是记录失败
                print(f"Failed to delete file {instance.file_path} from COS.")
        elif instance.storage_type == "local":
            deleted = storage_backend.delete_file(instance.file_path)
            if not deleted:
                print(f"Failed to delete file {instance.file_path} from local storage.")

        instance.delete()  # 从数据库中删除记录

    @action(
        detail=False, methods=["post"], parser_classes=(MultiPartParser, FormParser)
    )
    def bulk_upload(self, request, *args, **kwargs):
        files = request.FILES.getlist("files")  # 假设前端以 'files' 字段名传递多个文件
        ticket_id = request.data.get("ticket")
        reply_id = request.data.get("reply", None)

        if not files:
            return Response(
                {"error": "No files provided for bulk upload."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not ticket_id:
            return Response(
                {"error": "Ticket ID is required for bulk upload."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 检查用户是否有权限为该工单/回复上传附件
        try:
            ticket = Ticket.objects.get(id=ticket_id)
            if not (request.user.is_staff or request.user.company == ticket.company):
                raise permissions.PermissionDenied(
                    "You do not have permission to upload attachments to this ticket."
                )
        except Ticket.DoesNotExist:
            return Response(
                {"error": "Ticket not found."}, status=status.HTTP_404_NOT_FOUND
            )

        if reply_id:
            try:
                Reply.objects.get(id=reply_id, ticket=ticket)
            except Reply.DoesNotExist:
                return Response(
                    {"error": "Reply not found or does not belong to the ticket."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        results = []
        errors = []

        for uploaded_file in files:
            is_valid, error_message = storage_backend.validate_file(uploaded_file)
            if not is_valid:
                errors.append({"file_name": uploaded_file.name, "error": error_message})
                continue

            try:
                file_info = storage_backend.save_attachment(
                    uploaded_file, ticket_id=ticket_id, reply_id=reply_id
                )
                attachment = Attachment.objects.create(
                    ticket_id=ticket_id,
                    reply_id=reply_id,
                    uploaded_by=request.user,
                    original_name=file_info["original_name"],
                    file_name=file_info["file_name"],
                    file_path=file_info["file_path"],
                    file_size=file_info["file_size"],
                    content_type=file_info["content_type"],
                    storage_type=file_info["storage_type"],
                )
                results.append(AttachmentSerializer(attachment).data)
            except Exception as e:
                errors.append({"file_name": uploaded_file.name, "error": str(e)})

        return Response(
            {
                "success_count": len(results),
                "failure_count": len(errors),
                "results": results,
                "errors": errors,
            },
            status=status.HTTP_201_CREATED if results else status.HTTP_400_BAD_REQUEST,
        )
