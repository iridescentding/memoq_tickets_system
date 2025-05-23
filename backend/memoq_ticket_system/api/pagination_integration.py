from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPageNumberPagination(PageNumberPagination):
    """
    自定义分页类，支持前端指定每页大小
    """
    page_size = 10  # 默认每页大小
    page_size_query_param = 'page_size'  # 前端可通过此参数指定每页大小
    max_page_size = 100  # 每页最大条数限制
    
    def get_paginated_response(self, data):
        """
        自定义分页响应格式，包含更多分页信息
        """
        return Response({
            'count': self.page.paginator.count,  # 总记录数
            'next': self.get_next_link(),  # 下一页链接
            'previous': self.get_previous_link(),  # 上一页链接
            'current_page': self.page.number,  # 当前页码
            'total_pages': self.page.paginator.num_pages,  # 总页数
            'page_size': self.get_page_size(self.request),  # 当前每页大小
            'results': data  # 当前页数据
        })


class TicketListPagination(CustomPageNumberPagination):
    """
    工单列表分页类
    """
    page_size = 20  # 默认每页显示20条


class AdminPendingTicketsPagination(CustomPageNumberPagination):
    """
    管理员仪表盘待分配工单分页类
    """
    page_size = 10  # 默认每页显示10条


class AdminMissIRTicketsPagination(CustomPageNumberPagination):
    """
    管理员仪表盘即将miss IR和已miss IR工单分页类
    """
    page_size = 15  # 默认每页显示15条


class AdminIdleTicketsPagination(CustomPageNumberPagination):
    """
    管理员仪表盘即将idle和已idle工单分页类
    """
    page_size = 15  # 默认每页显示15条


class SupportUsersPagination(CustomPageNumberPagination):
    """
    技术支持账号列表分页类
    """
    page_size = 20  # 默认每页显示20条


class CompanyListPagination(CustomPageNumberPagination):
    """
    公司列表分页类
    """
    page_size = 20  # 默认每页显示20条
