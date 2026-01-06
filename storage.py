# storage.py
import os
import uuid
import boto3

USE_S3 = True   # 🔥 toggle here if needed
S3_BUCKET = "national-scaffolding-uploads"

s3 = boto3.client("s3")


def save_image(file_obj):
    """
    Saves image to S3 (or local if USE_S3=False)
    Returns URL/path to store in DB
    """
    filename = f"{uuid.uuid4().hex}_{file_obj.filename}"

    if USE_S3:
        s3.upload_fileobj(
            file_obj,
            S3_BUCKET,
            filename,
            ExtraArgs={"ContentType": file_obj.content_type}
        )
        return f"https://{S3_BUCKET}.s3.amazonaws.com/{filename}"

    # fallback: local storage (optional)
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    path = os.path.join(upload_dir, filename)
    file_obj.save(path)
    return f"uploads/{filename}"


def delete_image(image_url):
    """
    Deletes image from S3 or local
    """
    if USE_S3 and image_url.startswith("https://"):
        key = image_url.split(".com/")[-1]
        s3.delete_object(Bucket=S3_BUCKET, Key=key)
        return

    if os.path.exists(image_url):
        os.remove(image_url)
