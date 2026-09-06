"""S3-compatible object storage adapter (including Cloudflare R2)."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from .artifact import ArtifactMetadata


class S3ArtifactStore:
    """Thin S3-compatible adapter with a lazy boto3 dependency.

    Cloudflare R2 works through its S3-compatible endpoint. Install the optional
    ``storage`` dependency before constructing this class.
    """

    def __init__(self, bucket: str, *, endpoint_url: str | None = None, region_name: str = "auto", client: Any | None = None) -> None:
        if not bucket.strip():
            raise ValueError("bucket is required")
        if client is None:
            try:
                import boto3
            except ImportError as exc:
                raise RuntimeError("S3ArtifactStore requires the 'storage' optional dependency") from exc
            client = boto3.client("s3", endpoint_url=endpoint_url, region_name=region_name)
        self.bucket = bucket
        self.client = client

    def put(self, key: str, data: bytes, *, content_type: str = "application/octet-stream", data_class: str = "PRIVATE_CLOUD") -> ArtifactMetadata:
        key = key.strip("/")
        if not key:
            raise ValueError("artifact key must be non-empty")
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type, Metadata={"data-class": data_class})
        return ArtifactMetadata(
            key=key, content_type=content_type, size_bytes=len(data), created_at=datetime.now(timezone.utc),
            sha256=hashlib.sha256(data).hexdigest(), data_class=data_class,
        )

    def get(self, key: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=key.strip("/"))
        return bytes(response["Body"].read())

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=key.strip("/"))
        except Exception as exc:
            error = getattr(exc, "response", {}).get("Error", {})
            if error.get("Code") in {"404", "NoSuchKey", "NotFound"}:
                return False
            raise
        return True

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key.strip("/"))

    def list(self, prefix: str = "") -> list[str]:
        response = self.client.list_objects_v2(Bucket=self.bucket, Prefix=prefix.strip("/"))
        return sorted(str(item["Key"]) for item in response.get("Contents", []))
