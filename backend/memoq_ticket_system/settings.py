"""
Django settings for memoq_ticket_system project.
"""

from pathlib import Path
import os
import dotenv  # 添加dotenv导入

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# 加载 .env 文件中的环境变量
dotenv_path = BASE_DIR / ".env"
if os.path.exists(dotenv_path):
    dotenv.load_dotenv(dotenv_path)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY", "django-insecure-memoq-ticket-system-dev-key"
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DJANGO_DEBUG", "True") == "True"

ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 第三方应用
    "rest_framework",
    "corsheaders",
    "rest_framework_simplejwt",  # 添加到 INSTALLED_APPS
    # 项目应用
    "memoq_ticket_system.api",  # 确保 api 应用被注册
    "memoq_ticket_system",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "memoq_ticket_system.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "memoq_ticket_system.wsgi.application"

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = os.getenv("STATIC_URL", "/static/")
STATIC_ROOT = os.getenv("STATIC_ROOT", os.path.join(BASE_DIR, "static"))
# Media files (User uploaded files)
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# 自定义用户模型
AUTH_USER_MODEL = "memoq_ticket_system.User"

# REST Framework 设置
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}

# JWT 配置
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# CORS 设置
CORS_ALLOW_ALL_ORIGINS = DEBUG  # 开发环境下允许所有来源，生产环境应配置具体来源
CORS_ALLOWED_ORIGINS = os.getenv(
    "DJANGO_CORS_ALLOWED_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080"
).split(",")

# 文件上传设置
FILE_UPLOAD_MAX_MEMORY_SIZE = int(
    os.getenv("DJANGO_FILE_UPLOAD_MAX_MEMORY_SIZE", 10 * 1024 * 1024)
)  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = int(
    os.getenv("DJANGO_DATA_UPLOAD_MAX_MEMORY_SIZE", 10 * 1024 * 1024)
)  # 10MB
MAX_ATTACHMENT_SIZE = FILE_UPLOAD_MAX_MEMORY_SIZE
ALLOWED_ATTACHMENT_EXTENSIONS = [
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".txt",
    ".zip",
    ".rar",
]

# 腾讯云COS配置
TENCENT_COS_SECRET_ID = os.getenv("TENCENT_COS_SECRET_ID", None)
TENCENT_COS_SECRET_KEY = os.getenv("TENCENT_COS_SECRET_KEY", None)
TENCENT_COS_REGION = os.getenv("TENCENT_COS_REGION", None)
TENCENT_COS_BUCKET = os.getenv("TENCENT_COS_BUCKET", None)
TENCENT_COS_BASE_URL = os.getenv(
    "TENCENT_COS_BASE_URL",
    (
        f"https://{TENCENT_COS_BUCKET}.cos.{TENCENT_COS_REGION}.myqcloud.com"
        if TENCENT_COS_BUCKET and TENCENT_COS_REGION
        else None
    ),
)

# 文件存储后端选择 ('local' 或 'cos')
# 默认为 'local'，如果COS配置完整则可以考虑切换为 'cos'
DEFAULT_FILE_STORAGE_BACKEND = os.getenv("DEFAULT_FILE_STORAGE_BACKEND", "local")

if DEFAULT_FILE_STORAGE_BACKEND == "cos" and not all(
    [
        TENCENT_COS_SECRET_ID,
        TENCENT_COS_SECRET_KEY,
        TENCENT_COS_REGION,
        TENCENT_COS_BUCKET,
    ]
):
    print(
        "警告: DEFAULT_FILE_STORAGE_BACKEND 设置为 'cos' 但腾讯云COS配置不完整，将回退到本地存储。"
    )
    DEFAULT_FILE_STORAGE_BACKEND = "local"

# 日志配置 (可选，用于调试COS上传)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "qcloud_cos": {
            "handlers": ["console"],
            "level": "DEBUG",  # 可以设置为INFO或WARNING以减少日志量
            "propagate": False,
        },
    },
}
