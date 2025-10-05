from datetime import timedelta
from fastapi import UploadFile
from minio import Minio
from core import config
from werkzeug.utils import secure_filename

class FileServices:

    def _get_minio_client(self):
        """Get MinIO client instance
        :rtype: Minio
        """
        minio_client = Minio(
            config.APIConfig.MINIO_HOSTNAME,
            access_key=config.APIConfig.MINIO_ACCESS_KEY,
            secret_key=config.APIConfig.MINIO_SECRET_KEY,
            secure=config.APIConfig.MINIO_SECURE
        )
        return minio_client
    
    def upload_file(self, org_id: str, category: str, file: UploadFile):
        """Upload file to MinIO bucket
        :param org_id: ID of the organization
        :param category: Category of the file (e.g., 'media', 'data')
        :param file: File to upload
        :return: URL of the uploaded file
        """
        minio_client = self._get_minio_client()
        prefix = f"{org_id.split('-')[0]}"
        # Ensure the bucket exists
        bucket_name = "data" if category == "data" else "media"
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)

        # Upload the file
        file_name = secure_filename(file.filename)
        object_name = f"{prefix}/{file_name}"
        file_size = file.file.seek(0, 2)  # Get the file size
        file.file.seek(0)
        minio_client.put_object(
            bucket_name,
            object_name,
            file.file,
            file_size
        )

        return file_name

    def get_file_url(self, org_id: str, category: str, file_name: str):
        """Get the URL of a file in MinIO bucket
        :param org_id: ID of the organization
        :param category: Category of the file (e.g., 'media', 'data')
        :param file_name: Name of the file
        :return: URL of the file
        """
        minio_client = self._get_minio_client()
        prefix = f"{org_id.split('-')[0]}"
        bucket_name = "data" if category == "data" else "media"
        
        # Generate a presigned URL for the file
        object_name = f"{prefix}/{file_name}"
        url = minio_client.presigned_get_object(
            bucket_name,
            object_name,
            expires=timedelta(days=1),
        )
        
        return url
    

    def upload_local_file(self, org_id: str, category: str, file_path: str):
        """Upload a local file to MinIO bucket"""
        minio_client = self._get_minio_client()
        prefix = f"{org_id.split('-')[0]}"
        # Ensure the bucket exists
        bucket_name = "data" if category == "data" else "media"
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)

        # Upload the file
        file_name = secure_filename(file_path.split("/")[-1])
        object_name = f"{prefix}/{file_name}"
        minio_client.fput_object(
            bucket_name,
            object_name,
            file_path,
        )

        return file_name
    

    def upload_avatar(self, user_id: str, file: UploadFile):
        """Upload avatar to MinIO bucket
        :param user_id: ID of the user
        :param file: File to upload
        :return: URL of the uploaded file
        """
        minio_client = self._get_minio_client()
        prefix = f"{user_id.split('-')[0]}"
        # Ensure the bucket exists
        bucket_name = "media"
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)

        # Upload the file
        file_name = secure_filename(file.filename)
        object_name = f"avatars/{prefix}/{file_name}"
        file_size = file.file.seek(0, 2)  # Get the file size
        file.file.seek(0)
        minio_client.put_object(
            bucket_name,
            object_name,
            file.file,
            file_size
        )

        return file_name


    def get_avatar_url(self, user_id: str, file_name: str):
        """Get the URL of a file in MinIO bucket
        :param user_id: ID of the user
        :param file_name: Name of the file
        :return: URL of the file
        """
        minio_client = self._get_minio_client()
        prefix = f"{user_id.split('-')[0]}"
        bucket_name = "media"
        
        # Generate a presigned URL for the file
        object_name = f"avatars/{prefix}/{file_name}"
        url = minio_client.presigned_get_object(
            bucket_name,
            object_name,
            expires=timedelta(days=7),
        )
        
        return url