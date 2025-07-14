import os
import uuid
import base64
import json
from minio import Minio
from minio.error import S3Error
from io import BytesIO
from datetime import timedelta

# Get MinIO configuration from environment variables
MINIO_HOST = os.getenv("MINIO_HOST", "localhost")
MINIO_PORT = os.getenv("MINIO_PORT", "9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "screenshots")
EXTERNAL_URL = os.getenv("EXTERNAL_URL", "http://localhost:8080").rstrip('/')

# Initialize MinIO client with the internal service name for storage operations
minio_client = Minio(
    f"{MINIO_HOST}:{MINIO_PORT}",
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False  # Set to True if using HTTPS
)

# Define public read policy
public_read_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"AWS": "*"},
            "Action": ["s3:GetObject"],
            "Resource": [f"arn:aws:s3:::{MINIO_BUCKET}/*"]
        }
    ]
}

# Ensure bucket exists with public read access
try:
    if not minio_client.bucket_exists(MINIO_BUCKET):
        minio_client.make_bucket(MINIO_BUCKET)
    # Set bucket policy for public read access
    minio_client.set_bucket_policy(MINIO_BUCKET, json.dumps(public_read_policy))
except S3Error as e:
    print(f"Error initializing MinIO bucket: {e}")

def save_base64_image(base64_data: str) -> str:
    """
    Save a base64 encoded image to MinIO and return its object name/path
    """
    try:
        # Generate a unique object name
        object_name = f"screenshot_{uuid.uuid4().hex}.png"
        
        # Convert base64 to bytes
        image_data = base64.b64decode(base64_data)
        image_stream = BytesIO(image_data)
        
        # Upload to MinIO
        minio_client.put_object(
            MINIO_BUCKET,
            object_name,
            image_stream,
            length=len(image_data),
            content_type="image/png"
        )
        
        return object_name
    except S3Error as e:
        print(f"Error saving image to MinIO: {e}")
        return None

def get_image_url(object_name: str) -> str:
    """
    Get a URL for accessing an image through the nginx proxy
    """
    try:
        # Construct URL using the nginx proxy path
        return f"{EXTERNAL_URL}/minio/{MINIO_BUCKET}/{object_name}"
    except Exception as e:
        print(f"Error generating URL: {e}")
        return None 