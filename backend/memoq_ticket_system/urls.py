from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from memoq_ticket_system.api.views import home  # Import the home view

urlpatterns = [
    path("", home, name="home"),  # Add a route for the root path
    path("admin/", admin.site.urls),
    path("api/", include("memoq_ticket_system.api.urls")),
    path("api-auth/", include("rest_framework.urls")),
]

# 添加媒体文件的URL配置
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
