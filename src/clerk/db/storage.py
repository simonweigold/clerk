"""Supabase Storage integration for resource files."""

from pathlib import Path
from uuid import UUID

from .config import get_supabase_client

BUCKET_NAME = "reasoning-kits"


class StorageService:
    """Service for managing files in Supabase Storage.

    Files are organized as:
        {kit_id}/{version_id}/resources/{filename}
    """

    def __init__(self, use_service_key: bool = False) -> None:
        """Initialize storage service.

        Args:
            use_service_key: Use service role key for admin operations.
        """
        self.client = get_supabase_client(use_service_key)
        self.bucket = self.client.storage.from_(BUCKET_NAME)

    def upload_resource(
        self,
        kit_id: UUID,
        version_id: UUID,
        filename: str,
        file_path: Path,
    ) -> str:
        """Upload a resource file to storage.

        Args:
            kit_id: The reasoning kit ID
            version_id: The kit version ID
            filename: The filename to use in storage
            file_path: Local path to the file

        Returns:
            Storage path for the uploaded file
        """
        storage_path = f"{kit_id}/{version_id}/resources/{filename}"

        with open(file_path, "rb") as f:
            file_content = f.read()

        # Upload file (will overwrite if exists)
        self.bucket.upload(
            path=storage_path,
            file=file_content,
            file_options={"upsert": "true"},
        )

        return storage_path

    def upload_resource_bytes(
        self,
        kit_id: UUID,
        version_id: UUID,
        filename: str,
        content: bytes,
        content_type: str | None = None,
    ) -> str:
        """Upload resource content directly from bytes.

        Args:
            kit_id: The reasoning kit ID
            version_id: The kit version ID
            filename: The filename to use in storage
            content: File content as bytes
            content_type: MIME type of the content

        Returns:
            Storage path for the uploaded file
        """
        storage_path = f"{kit_id}/{version_id}/resources/{filename}"

        file_options = {"upsert": "true"}
        if content_type:
            file_options["contentType"] = content_type

        self.bucket.upload(
            path=storage_path,
            file=content,
            file_options=file_options,  # type: ignore[arg-type]
        )

        return storage_path

    def download_resource(self, storage_path: str) -> bytes:
        """Download a resource file from storage.

        Args:
            storage_path: Path to the file in storage

        Returns:
            File content as bytes
        """
        return self.bucket.download(storage_path)

    def download_resource_text(self, storage_path: str, encoding: str = "utf-8") -> str:
        """Download a resource file and decode as text.

        Args:
            storage_path: Path to the file in storage
            encoding: Text encoding to use

        Returns:
            File content as string
        """
        content = self.download_resource(storage_path)
        return content.decode(encoding)

    def get_public_url(self, storage_path: str) -> str:
        """Get public URL for a resource (if bucket is public).

        Args:
            storage_path: Path to the file in storage

        Returns:
            Public URL for the file
        """
        return self.bucket.get_public_url(storage_path)

    def get_signed_url(self, storage_path: str, expires_in: int = 3600) -> str:
        """Get a signed URL for temporary access to a resource.

        Args:
            storage_path: Path to the file in storage
            expires_in: URL expiration time in seconds (default: 1 hour)

        Returns:
            Signed URL for the file
        """
        response = self.bucket.create_signed_url(storage_path, expires_in)
        return response["signedURL"]

    def delete_resource(self, storage_path: str) -> None:
        """Delete a single resource from storage.

        Args:
            storage_path: Path to the file in storage
        """
        self.bucket.remove([storage_path])

    def delete_version_resources(self, kit_id: UUID, version_id: UUID) -> None:
        """Delete all resources for a version.

        Args:
            kit_id: The reasoning kit ID
            version_id: The kit version ID
        """
        prefix = f"{kit_id}/{version_id}/resources/"

        # List all files in the version's resources folder
        files = self.bucket.list(prefix)

        if files:
            # Build list of paths to delete
            paths_to_delete = [f"{prefix}{f['name']}" for f in files]
            self.bucket.remove(paths_to_delete)

    def delete_kit_resources(self, kit_id: UUID) -> None:
        """Delete all resources for a kit (all versions).

        Args:
            kit_id: The reasoning kit ID
        """
        prefix = f"{kit_id}/"

        # List all files recursively
        files = self.bucket.list(prefix)

        if files:
            paths_to_delete = [f"{prefix}{f['name']}" for f in files]
            self.bucket.remove(paths_to_delete)

    def list_version_resources(
        self, kit_id: UUID, version_id: UUID
    ) -> list[dict[str, str]]:
        """List all resources for a version.

        Args:
            kit_id: The reasoning kit ID
            version_id: The kit version ID

        Returns:
            List of file metadata dicts with 'name', 'id', etc.
        """
        prefix = f"{kit_id}/{version_id}/resources/"
        return self.bucket.list(prefix)

    def resource_exists(self, storage_path: str) -> bool:
        """Check if a resource exists in storage.

        Args:
            storage_path: Path to the file in storage

        Returns:
            True if the file exists
        """
        try:
            # Try to get file info - will raise if not found
            self.bucket.download(storage_path)
            return True
        except Exception:
            return False


def ensure_bucket_exists(use_service_key: bool = True) -> None:
    """Ensure the reasoning-kits bucket exists.

    Creates the bucket if it doesn't exist. Requires service role key
    for bucket creation.

    Args:
        use_service_key: Must be True to create buckets
    """
    client = get_supabase_client(use_service_key=use_service_key)

    # List existing buckets
    buckets = client.storage.list_buckets()
    bucket_names = [b.name for b in buckets]

    if BUCKET_NAME not in bucket_names:
        # Create the bucket with public access for reading
        client.storage.create_bucket(
            BUCKET_NAME,
            options={
                "public": True,  # Allow public read access
                "file_size_limit": 52428800,  # 50MB max file size
                "allowed_mime_types": [
                    "text/plain",
                    "text/csv",
                    "application/pdf",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "application/vnd.ms-excel",
                    "application/json",
                ],
            },
        )
        print(f"Created storage bucket: {BUCKET_NAME}")
    else:
        print(f"Storage bucket already exists: {BUCKET_NAME}")
