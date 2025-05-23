from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views # Main views
from .oauth_views import OAuthCallbackView # Specific import for OAuth callback
from .views import CustomTokenObtainPairView, PublicCompanyDetailsBySlugView, OAuthInitiateView # Import new views

router = DefaultRouter()
router.register(r"users", views.UserViewSet, basename="user")
router.register(r"companies", views.CompanyViewSet, basename="company")
router.register(r"company-sso-providers", views.CompanySSOProviderViewSet, basename="companyssoprovider")
router.register(r"company-configs", views.CompanyConfigViewSet, basename="companyconfig")
router.register(r"tickets", views.TicketViewSet, basename="ticket")
router.register(r"ticket-replies", views.TicketReplyViewSet, basename="ticketreply")
router.register(r"ticket-types", views.TicketTypeViewSet, basename="tickettype")
router.register(r"ticket-labels", views.TicketLabelViewSet, basename="ticketlabel")
# router.register(r"ticket-transfer-histories", views.TicketTransferHistoryViewSet, basename="tickettransferhistory") # Create if needed
router.register(r"ticket-satisfaction-ratings", views.TicketSatisfactionRatingViewSet, basename="ticketsatisfactionrating")
router.register(r"attachments", views.AttachmentViewSet, basename="attachment")
router.register(r"notification-configs", views.NotificationConfigViewSet, basename="notificationconfig")
router.register(r"notification-templates", views.NotificationTemplateViewSet, basename="notificationtemplate")
router.register(r"notification-logs", views.NotificationLogViewSet, basename="notificationlog")
router.register(r"customer-type-tags", views.CustomerTypeTagViewSet, basename="customertypetag")


urlpatterns = [
    path("", include(router.urls)), # All DRF router URLs are under /api/

    # Authentication
    path("auth/login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    # path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'), # If using JWT refresh

    # OAuth Endpoints
    # 1. Frontend redirects here to start the OAuth flow with a provider
    path("auth/oauth/initiate/<str:platform>/", OAuthInitiateView.as_view(), name="oauth_initiate"),
    # 2. OAuth provider redirects here after user authentication
    path("auth/oauth/callback/", OAuthCallbackView.as_view(), name="oauth_callback"), # Platform is now a query param

    # Public Endpoints (should be outside /api/ if it's for general public access without /api/ prefix)
    # For now, keeping it under /api/public/ for structure, adjust if needed.
    path("public/company-details-by-slug/<slug:slug>/", PublicCompanyDetailsBySlugView.as_view(), name="public_company_details_by_slug"),
]
