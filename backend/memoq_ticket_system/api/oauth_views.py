from django.conf import settings
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth import login
from django.utils.crypto import get_random_string
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
import requests
import json

from ..models import User

# Placeholder for actual App IDs, Secrets, and Redirect URIs
# These should be stored securely, e.g., in environment variables or Django settings
THIRD_PARTY_CONFIG = {
    "wecom": {
        "APP_ID": getattr(settings, "WECOM_APP_ID", "YOUR_WECOM_APP_ID"),
        "APP_SECRET": getattr(settings, "WECOM_APP_SECRET", "YOUR_WECOM_APP_SECRET"),
        "USER_INFO_URL": "https://qyapi.weixin.qq.com/cgi-bin/auth/getuserinfo",
        "TOKEN_URL": "https://qyapi.weixin.qq.com/cgi-bin/gettoken",
        # For WeCom, getting user info often involves a different flow (e.g. agent config, user_ticket)
        # This is a simplified placeholder. The actual implementation might be more complex.
        # Typically, for internal apps, you get userid directly from code.
    },
    "wechat": {
        "APP_ID": getattr(
            settings, "WECHAT_APP_ID", "YOUR_WECHAT_APP_ID"
        ),  # For website applications
        "APP_SECRET": getattr(settings, "WECHAT_APP_SECRET", "YOUR_WECHAT_APP_SECRET"),
        "TOKEN_URL": "https://api.weixin.qq.com/sns/oauth2/access_token",
        "USER_INFO_URL": "https://api.weixin.qq.com/sns/userinfo",
    },
    "feishu": {
        "APP_ID": getattr(settings, "FEISHU_APP_ID", "YOUR_FEISHU_APP_ID"),
        "APP_SECRET": getattr(settings, "FEISHU_APP_SECRET", "YOUR_FEISHU_APP_SECRET"),
        "TOKEN_URL": "https://passport.feishu.cn/suite/passport/oauth/token",
        "USER_INFO_URL": "https://passport.feishu.cn/suite/passport/oauth/userinfo",
        "APP_ACCESS_TOKEN_URL": "https://passport.feishu.cn/suite/passport/oauth/app_access_token",
    },
}


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


class OAuthCallbackView(APIView):
    def post(self, request, *args, **kwargs):
        platform = request.data.get("platform")
        code = request.data.get("code")

        if not platform or not code:
            return Response(
                {"error": "Platform and code are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if platform not in THIRD_PARTY_CONFIG:
            return Response(
                {"error": "Invalid platform."}, status=status.HTTP_400_BAD_REQUEST
            )

        config = THIRD_PARTY_CONFIG[platform]
        user_data = None
        third_party_user_id = None
        email_from_third_party = None  # Attempt to get email if available

        try:
            if platform == "wecom":
                # Enterprise WeChat (OAuth2 for members, simplified)
                # 1. Get access_token (corp level, not user level for this specific call)
                # This part is tricky as WeCom's user auth flow varies based on app type.
                # Assuming 'code' is for fetching user identity directly.
                # token_params = {
                #     'corpid': config['APP_ID'],
                #     'corpsecret': config['APP_SECRET'],
                # }
                # token_res = requests.get(config['TOKEN_URL'], params=token_params)
                # token_res.raise_for_status()
                # app_access_token = token_res.json().get('access_token')
                # if not app_access_token:
                #     return Response({'error': 'Failed to get WeCom app access token'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                # For member identity, the code is usually exchanged for userid directly
                # This requires proper agent configuration and permissions.
                # The URL is https://qyapi.weixin.qq.com/cgi-bin/auth/getuserinfo?access_token=ACCESS_TOKEN&code=CODE
                # However, the access_token here is the *webpage authorization access_token*, not app_access_token.
                # Let's assume a simplified flow where 'code' can directly give us some user info or we need a different token exchange.
                # For now, this is a placeholder as WeCom's full flow is complex and context-dependent.
                # A common approach for internal apps is to get userid via JS-SDK or from a redirect with code.
                # Let's simulate getting a userid if the frontend could pass it or a user_ticket.
                # This part needs to be carefully implemented based on the specific WeCom app setup.
                # For this example, we'll assume a placeholder that we get a 'UserId' or 'OpenId'.
                # user_info_params = {'access_token': app_access_token, 'code': code} # This is NOT the right access_token for getuserinfo with code
                # For a real scenario: you'd exchange code for a user-specific access_token first, or use a user_ticket.
                # This is a common point of confusion with WeCom APIs.
                # Let's assume for now we have a way to get `UserId` from the `code` or a `user_ticket`.
                # This is a placeholder and needs to be replaced with actual WeCom API calls.
                # For instance, if using https://developer.work.weixin.qq.com/document/path/91023 (getuserinfo3rd)
                # Or https://developer.work.weixin.qq.com/document/path/91868 (member auth)
                # For simplicity, we'll mock this part.
                # third_party_user_id = f"wecom_user_{get_random_string(8)}" # Mocked
                # user_data = {'UserId': third_party_user_id, 'name': 'WeCom User'}
                return Response(
                    {
                        "error": "WeCom login not fully implemented in this example due to complexity. Please use other methods or complete implementation."
                    },
                    status=status.HTTP_501_NOT_IMPLEMENTED,
                )

            elif platform == "wechat":
                # 1. Exchange code for access_token and openid
                token_params = {
                    "appid": config["APP_ID"],
                    "secret": config["APP_SECRET"],
                    "code": code,
                    "grant_type": "authorization_code",
                }
                token_res = requests.get(config["TOKEN_URL"], params=token_params)
                token_res.raise_for_status()
                token_data = token_res.json()
                access_token = token_data.get("access_token")
                openid = token_data.get("openid")
                if not access_token or not openid:
                    return Response(
                        {"error": "Failed to get WeChat access token or openid"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

                third_party_user_id = openid

                # 2. Get user info (if scope is snsapi_userinfo)
                user_info_params = {
                    "access_token": access_token,
                    "openid": openid,
                    "lang": "zh_CN",
                }
                user_info_res = requests.get(
                    config["USER_INFO_URL"], params=user_info_params
                )
                user_info_res.raise_for_status()
                user_data = user_info_res.json()
                # user_data will contain nickname, headimgurl, etc.

            elif platform == "feishu":
                # 1. Get app_access_token (tenant_access_token or app_access_token depending on app type)
                # For user login, we typically need user_access_token directly from code.
                # The Feishu docs say: obtain user_access_token by calling 'Get user_access_token' API with code.
                # This requires 'Authorization': 'Bearer <app_access_token>' in header for the token exchange call.

                # First, get app_access_token (internal app)
                app_token_payload = {
                    "app_id": config["APP_ID"],
                    "app_secret": config["APP_SECRET"],
                }
                app_token_res = requests.post(
                    config["APP_ACCESS_TOKEN_URL"], json=app_token_payload
                )
                app_token_res.raise_for_status()
                app_access_token = app_token_res.json().get(
                    "app_access_token"
                )  # or tenant_access_token
                if not app_access_token:
                    return Response(
                        {"error": "Failed to get Feishu app access token"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

                # 2. Exchange code for user_access_token
                user_token_payload = {"grant_type": "authorization_code", "code": code}
                user_token_headers = {
                    "Authorization": f"Bearer {app_access_token}",
                    "Content-Type": "application/json",
                }
                user_token_res = requests.post(
                    config["TOKEN_URL"],
                    headers=user_token_headers,
                    json=user_token_payload,
                )
                user_token_res.raise_for_status()
                user_token_data = user_token_res.json().get("data", {})
                access_token = user_token_data.get("access_token")
                # open_id = user_token_data.get('open_id') # This is the user's unique ID in Feishu
                if not access_token:
                    return Response(
                        {"error": "Failed to get Feishu user access token"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

                # 3. Get user info
                user_info_headers = {"Authorization": f"Bearer {access_token}"}
                user_info_res = requests.get(
                    config["USER_INFO_URL"], headers=user_info_headers
                )
                user_info_res.raise_for_status()
                user_data = user_info_res.json().get("data", {})
                third_party_user_id = user_data.get("open_id")
                email_from_third_party = user_data.get("email")

        except requests.exceptions.RequestException as e:
            return Response(
                {"error": f"Failed to communicate with {platform}: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not third_party_user_id:
            return Response(
                {
                    "error": f"Could not retrieve user ID from {platform}. Data: {user_data}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Try to find user by third-party ID
        user = None
        if platform == "wecom":
            user = User.objects.filter(enterprise_wechat_id=third_party_user_id).first()
        elif platform == "wechat":
            user = User.objects.filter(wechat_id=third_party_user_id).first()
        elif platform == "feishu":
            user = User.objects.filter(feishu_id=third_party_user_id).first()

        # If not found by third-party ID, try by email if available (especially for Feishu)
        if not user and email_from_third_party:
            user = User.objects.filter(email=email_from_third_party).first()
            if user:  # If found by email, link the third-party ID
                if platform == "wecom":
                    user.enterprise_wechat_id = third_party_user_id
                elif platform == "wechat":
                    user.wechat_id = third_party_user_id
                elif platform == "feishu":
                    user.feishu_id = third_party_user_id
                user.save()

        if not user:
            # Create a new user if one doesn't exist
            # For a real application, you might want to redirect to a registration completion page
            # or require company association.
            username = (
                f"{platform}_{third_party_user_id[:10]}"  # Generate a unique username
            )
            # Ensure username is unique
            while User.objects.filter(username=username).exists():
                username = (
                    f"{platform}_{third_party_user_id[:8]}_{get_random_string(4)}"
                )

            create_data = {"username": username}
            if email_from_third_party:
                create_data["email"] = email_from_third_party
            else:  # Create a dummy email if not provided, or handle differently
                create_data["email"] = f"{username}@example.com"

            if platform == "wecom":
                create_data["enterprise_wechat_id"] = third_party_user_id
            elif platform == "wechat":
                create_data["wechat_id"] = third_party_user_id
            elif platform == "feishu":
                create_data["feishu_id"] = third_party_user_id

            # Default role, company needs to be handled, perhaps based on domain or a later step
            user = User.objects.create_user(**create_data)
            # Potentially assign a default company or require user to select one post-login

        # Log the user in and generate JWT tokens
        login(request, user)  # This updates last_login
        tokens = get_tokens_for_user(user)

        response_data = {
            "message": "Login successful",
            "token": tokens["access"],  # Send JWT token to frontend
            "refresh_token": tokens["refresh"],
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "company_id": user.company_id if user.company else None,
                "third_party_userid": third_party_user_id,  # Send this back for frontend confirmation/storage
            },
        }

        # Set a secure, HttpOnly cookie containing the third_party_user_id (or a session identifier)
        # This is an example; for production, use session framework or more robust cookie management.
        # The JWT token itself is usually sent in Authorization header by frontend.
        # Storing third_party_user_id in a cookie might be for specific client-side needs.
        # For security, it's better if the backend manages the session via JWT or Django sessions.
        # If a cookie is strictly for the third_party_user_id, ensure it's HttpOnly and Secure in production.

        response = Response(response_data)
        # Example of setting a cookie for third_party_user_id. Consider security implications.
        # This cookie is accessible by JavaScript if HttpOnly is False.
        response.set_cookie(
            key="third_party_session_id",  # Or a more generic session ID
            value=third_party_user_id,  # Or a hashed/session-mapped value
            max_age=settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds(),
            secure=settings.SESSION_COOKIE_SECURE,  # True in production (HTTPS)
            httponly=True,  # Make HttpOnly for security
            samesite=settings.SESSION_COOKIE_SAMESITE,
        )
        return response
