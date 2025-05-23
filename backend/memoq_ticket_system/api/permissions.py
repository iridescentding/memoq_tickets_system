from rest_framework import permissions

class IsSystemAdminRole(permissions.BasePermission):
    """
    Custom permission to only allow system administrators to access an endpoint.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "system_admin"

class IsTechnicalSupportAdminRole(permissions.BasePermission):
    """
    Custom permission to only allow Technical Support Admins to access an endpoint.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "technical_support_admin"

class IsSupportRole(permissions.BasePermission):
    """
    Custom permission to only allow Support staff to access an endpoint.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "support"

class IsCompanyMember(permissions.BasePermission):
    """
    Custom permission to ensure users can only access resources of their own company.
    Support staff, Technical Support Admins, and System Admins can access all resources.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Support, Technical Support Admins, and System Admins can access all resources
        if request.user.role in ["support", "technical_support_admin", "system_admin"]:
            return True

        # Determine the company associated with the object
        company_of_object = None
        if hasattr(obj, 'company') and obj.company is not None:
            company_of_object = obj.company
        elif hasattr(obj, 'ticket') and hasattr(obj.ticket, 'company') and obj.ticket.company is not None:
            company_of_object = obj.ticket.company
        elif hasattr(obj, 'user') and hasattr(obj.user, 'company') and obj.user.company is not None:
            # This case is for objects that are users themselves or related to a user
            company_of_object = obj.user.company
        elif isinstance(obj, request.user.__class__) and hasattr(obj, 'company') and obj.company is not None:
            # If the object itself is a User instance
            company_of_object = obj.company
        else:
            # If the object doesn't have a direct or indirect company link, deny access for non-privileged users
            return False
        
        # Check if the requesting user belongs to that company
        return request.user.company == company_of_object

class IsSupportOrTechnicalSupportAdminOrSystemAdmin(permissions.BasePermission):
    """
    Custom permission to allow access only to Support, Technical Support Admins, or System Admins.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ["support", "technical_support_admin", "system_admin"]

class IsTechnicalSupportAdminOrSystemAdmin(permissions.BasePermission):
    """
    Custom permission for actions that can be performed by Technical Support Admin or System Admin.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ["technical_support_admin", "system_admin"]

class CanManageCompany(permissions.BasePermission):
    """
    Permission for Technical Support Admin or System Admin to manage company details.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ["technical_support_admin", "system_admin"]

    def has_object_permission(self, request, view, obj):
        # Object-level permission can be more granular if needed, but for now, role check is enough
        return self.has_permission(request, view)

class CanManageSupportUsers(permissions.BasePermission):
    """
    Permission for Technical Support Admin to manage support user accounts.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role == "technical_support_admin"

    def has_object_permission(self, request, view, obj):
        # Object is a User instance (a support staff member)
        # Technical Support Admin can manage any user with 'support' role or other 'technical_support_admin' (e.g. for editing)
        # They should not be able to escalate a support user to system_admin via this permission.
        if not request.user.is_authenticated:
            return False
        if request.user.role == "technical_support_admin":
            # Allow if the target user is 'support' or another 'technical_support_admin'
            # Prevent editing 'system_admin' or 'customer' roles through this permission
            if hasattr(obj, 'role') and obj.role in ['support', 'technical_support_admin']:
                 return True
            # Allow creation of new support users (no specific object yet)
            if view.action == 'create' or request.method == 'POST': # POST for create
                # Further checks can be done in the view if request.data specifies role
                return True
        return False

class IsOwnerOrSupportOrAdmin(permissions.BasePermission):
    """
    Allows access if the user is the owner of the object, or is support/admin staff.
    Typically used for objects like Tickets or TicketReplies where 'created_by' or 'user' field exists.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Support, Technical Support Admins, and System Admins can access all
        if request.user.role in ["support", "technical_support_admin", "system_admin"]:
            return True

        # Check for ownership
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True
        if hasattr(obj, 'user') and obj.user == request.user: # For TicketReply user
            return True
        
        # If the object is a ticket, and the user is part of the ticket's company
        if hasattr(obj, 'ticket') and hasattr(obj.ticket, 'company') and obj.ticket.company == request.user.company:
            return True # User from same company can view replies to their company's ticket
        if hasattr(obj, 'company') and obj.company == request.user.company:
             return True # User from same company can view their company's ticket

        return False

# 新增：工单关注人权限
class IsTicketFollowerOrCreator(permissions.BasePermission):
    """
    允许工单创建者或关注人访问和回复工单
    """
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # 支持人员和管理员可以访问所有工单
        if request.user.role in ["support", "technical_support_admin", "system_admin"]:
            return True

        # 检查是否为工单创建者
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True
        
        # 检查是否为工单提交者
        if hasattr(obj, 'submitted_by') and obj.submitted_by == request.user:
            return True
            
        # 检查是否为工单关注人
        if hasattr(obj, 'followers') and request.user in obj.followers.all():
            return True
            
        # 如果是回复，检查是否为关联工单的创建者或关注人
        if hasattr(obj, 'ticket'):
            if obj.ticket.created_by == request.user:
                return True
            if obj.ticket.submitted_by == request.user:
                return True
            if request.user in obj.ticket.followers.all():
                return True
                
        return False

# 新增：公司内工单查看权限
class CanViewCompanyTickets(permissions.BasePermission):
    """
    允许公司用户查看本公司所有工单
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated
        
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # 支持人员和管理员可以访问所有工单
        if request.user.role in ["support", "technical_support_admin", "system_admin"]:
            return True
            
        # 检查用户是否属于工单所属公司
        if hasattr(obj, 'company') and obj.company == request.user.company:
            return True
            
        # 如果是回复，检查是否属于同一公司的工单
        if hasattr(obj, 'ticket') and hasattr(obj.ticket, 'company') and obj.ticket.company == request.user.company:
            return True
            
        return False

# 新增：工单类型管理权限
class CanManageTicketTypes(permissions.BasePermission):
    """
    允许系统管理员、技术支持管理员和技术支持人员管理工单类型
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ["support", "technical_support_admin", "system_admin"]
        
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)

# 新增：工单标签管理权限
class CanManageTicketLabels(permissions.BasePermission):
    """
    允许系统管理员、技术支持管理员和技术支持人员管理工单标签
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ["support", "technical_support_admin", "system_admin"]
        
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)

# 新增：工单转移权限
class CanTransferTicket(permissions.BasePermission):
    """
    允许技术支持人员转移自己负责的工单
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ["support", "technical_support_admin", "system_admin"]
        
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # 管理员可以转移任何工单
        if request.user.role in ["technical_support_admin", "system_admin"]:
            return True
            
        # 技术支持人员只能转移分配给自己的工单
        if request.user.role == "support" and hasattr(obj, 'assigned_to') and obj.assigned_to == request.user:
            return True
            
        return False

# 新增：工单暂停权限
class CanPauseTicket(permissions.BasePermission):
    """
    允许技术支持人员和工单提出人暂停工单
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated
        
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        # 管理员和技术支持人员可以暂停任何工单
        if request.user.role in ["support", "technical_support_admin", "system_admin"]:
            return True
            
        # 工单创建者和提交者可以暂停工单
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True
        if hasattr(obj, 'submitted_by') and obj.submitted_by == request.user:
            return True
            
        return False
