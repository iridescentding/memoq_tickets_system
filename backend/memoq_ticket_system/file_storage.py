from django.conf import settings
from django.utils import timezone
import os
import uuid
import mimetypes
import logging
from qcloud_cos import CosConfig, CosS3Client

logger = logging.getLogger(__name__)


class TencentCOSStorage:
    """
    腾讯云COS文件存储类，用于处理文件上传、存储和访问
    """

    def __init__(self):
        self.secret_id = getattr(settings, "TENCENT_COS_SECRET_ID", None)
        self.secret_key = getattr(settings, "TENCENT_COS_SECRET_KEY", None)
        self.region = getattr(settings, "TENCENT_COS_REGION", None)
        self.bucket = getattr(settings, "TENCENT_COS_BUCKET", None)
        self.cos_base_url = getattr(
            settings,
            "TENCENT_COS_BASE_URL",
            f"https://{self.bucket}.cos.{self.region}.myqcloud.com",
        )

        if not all([self.secret_id, self.secret_key, self.region, self.bucket]):
            logger.error("腾讯云COS配置不完整，请检查settings.py")
            raise ValueError("腾讯云COS配置不完整")

        config = CosConfig(
            Region=self.region, SecretId=self.secret_id, SecretKey=self.secret_key
        )
        self.client = CosS3Client(config)

    def save_attachment(self, file, ticket_id=None, reply_id=None):
        """
        保存附件文件到腾讯云COS

        Args:
            file: 上传的文件对象 (in-memory uploaded file or similar)
            ticket_id: 关联的工单ID (可选)
            reply_id: 关联的回复ID (可选)

        Returns:
            dict: 包含文件信息的字典
        """
        original_name = file.name
        file_ext = os.path.splitext(original_name)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"

        today = timezone.now().strftime("%Y/%m/%d")
        cos_key = f"attachments/{today}/{unique_filename}"

        try:
            # 对于UploadedFile对象，需要读取其内容
            file_content = file.read()
            response = self.client.put_object(
                Bucket=self.bucket,
                Body=file_content,
                Key=cos_key,
                StorageClass="STANDARD",
                ContentType=mimetypes.guess_type(original_name)[0]
                or "application/octet-stream",
            )
            logger.info(
                f"文件已上传至腾讯云COS: {cos_key}, ETag: {response.get('ETag')}"
            )
        except Exception as e:
            logger.error(f"上传文件至腾讯云COS失败: {cos_key}, 错误: {str(e)}")
            raise

        file_size = len(file_content)  # 获取文件大小
        content_type, _ = mimetypes.guess_type(original_name)
        if not content_type:
            content_type = "application/octet-stream"

        return {
            "original_name": original_name,
            "file_name": unique_filename,  # COS中的文件名部分
            "file_path": cos_key,  # COS中的完整路径 (Key)
            "file_size": file_size,
            "content_type": content_type,
            "ticket_id": ticket_id,
            "reply_id": reply_id,
            "upload_date": timezone.now(),
            "storage_type": "cos",  # 标记存储类型
        }

    def get_file_url(self, cos_key, expires=3600):
        """
        获取腾讯云COS文件的预签名URL

        Args:
            cos_key: 文件在COS中的Key
            expires: URL有效期（秒），默认为1小时

        Returns:
            str: 文件的预签名URL
        """
        try:
            url = self.client.get_presigned_url(
                Bucket=self.bucket, Key=cos_key, Method="GET", Expired=expires
            )
            return url
        except Exception as e:
            logger.error(f"获取COS文件预签名URL失败: {cos_key}, 错误: {str(e)}")
            # Fallback to public URL if presigned URL fails and it's configured
            # This is a simplified fallback, in reality, you'd check if the bucket is public
            return f"{self.cos_base_url}/{cos_key}"

    def delete_file(self, cos_key):
        """
        从腾讯云COS删除文件

        Args:
            cos_key: 文件在COS中的Key

        Returns:
            bool: 删除成功返回True，否则返回False
        """
        try:
            self.client.delete_object(Bucket=self.bucket, Key=cos_key)
            logger.info(f"文件已从腾讯云COS删除: {cos_key}")
            return True
        except Exception as e:
            logger.error(f"从腾讯云COS删除文件失败: {cos_key}, 错误: {str(e)}")
            return False

    def validate_file(self, file):
        """
        验证文件是否符合要求

        Args:
            file: 上传的文件对象

        Returns:
            tuple: (是否有效, 错误信息)
        """
        max_size = getattr(
            settings, "MAX_ATTACHMENT_SIZE", 10 * 1024 * 1024
        )  # 默认10MB
        if file.size > max_size:
            return False, f"文件大小超过限制 ({file.size} > {max_size} 字节)"

        allowed_extensions = getattr(
            settings,
            "ALLOWED_ATTACHMENT_EXTENSIONS",
            [
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
            ],
        )

        file_ext = os.path.splitext(file.name)[1].lower()
        if allowed_extensions and file_ext not in allowed_extensions:
            return False, f"不支持的文件类型: {file_ext}"

        return True, ""


# 保留 SecureFileStorage 以便在需要时回退或用于其他本地文件操作
class SecureFileStorage:
    """
    安全文件存储类，用于处理文件上传、存储和访问 (本地)
    """

    def __init__(self):
        from django.core.files.storage import FileSystemStorage

        self.storage = FileSystemStorage(
            location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL
        )
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        self.attachments_dir = os.path.join(settings.MEDIA_ROOT, "attachments")
        os.makedirs(self.attachments_dir, exist_ok=True)

    def save_attachment(self, file, ticket_id=None, reply_id=None):
        original_name = file.name
        file_ext = os.path.splitext(original_name)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        today = timezone.now().strftime("%Y/%m/%d")
        relative_path = os.path.join("attachments", today)
        full_upload_path = os.path.join(settings.MEDIA_ROOT, relative_path)
        os.makedirs(full_upload_path, exist_ok=True)
        file_path = os.path.join(relative_path, unique_filename)
        full_file_path = os.path.join(settings.MEDIA_ROOT, file_path)
        with open(full_file_path, "wb+") as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        file_size = os.path.getsize(full_file_path)
        content_type, _ = mimetypes.guess_type(original_name)
        if not content_type:
            content_type = "application/octet-stream"
        return {
            "original_name": original_name,
            "file_name": unique_filename,
            "file_path": file_path,
            "file_size": file_size,
            "content_type": content_type,
            "ticket_id": ticket_id,
            "reply_id": reply_id,
            "upload_date": timezone.now(),
            "storage_type": "local",
        }

    def get_file_path(self, file_path):
        return os.path.join(settings.MEDIA_ROOT, file_path)

    def get_file_url(self, file_path):
        return f"{settings.MEDIA_URL}{file_path}"

    def file_exists(self, file_path):
        full_path = self.get_file_path(file_path)
        return os.path.exists(full_path)

    def delete_file(self, file_path):
        if self.file_exists(file_path):
            full_path = self.get_file_path(file_path)
            os.remove(full_path)
            return True
        return False

    def validate_file(self, file):
        max_size = getattr(settings, "MAX_ATTACHMENT_SIZE", 10 * 1024 * 1024)
        if file.size > max_size:
            return False, f"文件大小超过限制 ({file.size} > {max_size} 字节)"
        allowed_extensions = getattr(
            settings,
            "ALLOWED_ATTACHMENT_EXTENSIONS",
            [
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
            ],
        )
        file_ext = os.path.splitext(file.name)[1].lower()
        if allowed_extensions and file_ext not in allowed_extensions:
            return False, f"不支持的文件类型: {file_ext}"
        return True, ""
