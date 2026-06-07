import os
import cloudinary
import cloudinary.uploader


def configure_cloudinary():
    """
    Configures the Cloudinary SDK with credentials from environment variables.
    Must be called before any upload or delete operation.
    """
    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    )


def upload_file(file_bytes: bytes, document_id: str, filename: str) -> dict:
    """
    Uploads raw file bytes to Cloudinary.

    Returns a dict with:
    - secure_url: the public URL to access the file
    - public_id: the Cloudinary ID needed to delete the file later
    """
    configure_cloudinary()

    result = cloudinary.uploader.upload(
        file_bytes,
        public_id=f"documents/{document_id}",
        resource_type="raw",        # "raw" = non-image files (PDFs, TXTs)
        use_filename=False,         # use our document_id as the name, not the original filename
        overwrite=True,
    )

    return {
        "secure_url": result["secure_url"],
        "public_id": result["public_id"],
    }


def delete_file(public_id: str):
    """
    Deletes a file from Cloudinary using its public_id.
    """
    configure_cloudinary()
    cloudinary.uploader.destroy(public_id, resource_type="raw")