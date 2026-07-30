"""MinIO (S3-compatible) object storage adapter using httpx (S4-STORAGE-001).

This adapter uses the S3 REST API directly over httpx so no additional
package dependency is required (handbook §4.4 — prefer existing deps).
Presigned URL generation uses HMAC-SHA256 AWS Signature Version 4.

For production usage configure via env/settings:
  MINIO_ENDPOINT  = "http://localhost:9000"
  MINIO_ACCESS_KEY = "minioadmin"
  MINIO_SECRET_KEY = "minioadmin"
  MINIO_REGION     = "us-east-1"  (MinIO ignores the value but needs one)
"""

from __future__ import annotations

import hashlib
import hmac
import urllib.parse
from datetime import UTC, datetime

import httpx

from fictional_world.application.ports.storage import (
    ObjectMetadata,
    PutResult,
    StorageConflictError,
    StorageNotFoundError,
)

# ---------------------------------------------------------------------------
# AWS Signature V4 helpers (minimal, for PUT/GET/HEAD/DELETE)
# ---------------------------------------------------------------------------


def _sign(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode(), hashlib.sha256).digest()


def _signing_key(secret_key: str, date_str: str, region: str, service: str) -> bytes:
    k_date = _sign(f"AWS4{secret_key}".encode(), date_str)
    k_region = _sign(k_date, region)
    k_service = _sign(k_region, service)
    k_signing = _sign(k_service, "aws4_request")
    return k_signing


def _canonical_headers(headers: dict[str, str]) -> tuple[str, str]:
    sorted_keys = sorted(k.lower() for k in headers)
    canon = "\n".join(f"{k}:{headers[k].strip()}" for k in sorted_keys) + "\n"
    signed = ";".join(sorted_keys)
    return canon, signed


def _build_auth_headers(
    method: str,
    url: str,
    *,
    access_key: str,
    secret_key: str,
    region: str,
    payload: bytes = b"",
    extra_headers: dict[str, str] | None = None,
) -> dict[str, str]:
    now = datetime.now(UTC)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_str = now.strftime("%Y%m%d")

    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc

    payload_hash = hashlib.sha256(payload).hexdigest()

    headers: dict[str, str] = {
        "Host": host,
        "x-amz-date": amz_date,
        "x-amz-content-sha256": payload_hash,
    }
    if extra_headers:
        headers.update(extra_headers)

    canonical_headers, signed_headers = _canonical_headers(headers)
    canonical_uri = parsed.path or "/"
    canonical_qs = parsed.query

    canonical_request = "\n".join(
        [method, canonical_uri, canonical_qs, canonical_headers, signed_headers, payload_hash]
    )

    credential_scope = f"{date_str}/{region}/s3/aws4_request"
    string_to_sign = "\n".join(
        [
            "AWS4-HMAC-SHA256",
            amz_date,
            credential_scope,
            hashlib.sha256(canonical_request.encode()).hexdigest(),
        ]
    )

    signing_key = _signing_key(secret_key, date_str, region, "s3")
    signature = hmac.new(signing_key, string_to_sign.encode(), hashlib.sha256).hexdigest()

    auth_value = (
        f"AWS4-HMAC-SHA256 "
        f"Credential={access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, "
        f"Signature={signature}"
    )
    headers["Authorization"] = auth_value
    return headers


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------


class MinioObjectStore:
    """httpx-based S3/MinIO adapter — satisfies ObjectStoragePort.

    All I/O is performed with a shared AsyncClient; callers must not hold a
    DB transaction open while calling any method (handbook §4.3 / §11).
    """

    def __init__(
        self,
        *,
        endpoint: str,
        access_key: str,
        secret_key: str,
        region: str = "us-east-1",
        timeout: float = 30.0,
    ) -> None:
        self._endpoint = endpoint.rstrip("/")
        self._access_key = access_key
        self._secret_key = secret_key
        self._region = region
        self._client = httpx.AsyncClient(timeout=timeout)

    def _url(self, bucket: str, key: str) -> str:
        return f"{self._endpoint}/{bucket}/{urllib.parse.quote(key, safe='/')}"

    def _bucket_url(self, bucket: str) -> str:
        return f"{self._endpoint}/{bucket}"

    async def put(
        self,
        bucket: str,
        key: str,
        data: bytes,
        *,
        content_type: str = "application/octet-stream",
        extra_meta: dict[str, str] | None = None,
    ) -> PutResult:
        url = self._url(bucket, key)
        checksum = hashlib.sha256(data).hexdigest()
        meta_headers = {f"x-amz-meta-{k}": v for k, v in (extra_meta or {}).items()}
        extra = {"Content-Type": content_type, **meta_headers}
        headers = _build_auth_headers(
            "PUT",
            url,
            access_key=self._access_key,
            secret_key=self._secret_key,
            region=self._region,
            payload=data,
            extra_headers=extra,
        )
        headers["Content-Type"] = content_type

        resp = await self._client.put(url, content=data, headers=headers)
        if resp.status_code == 409:
            raise StorageConflictError(bucket, key)
        resp.raise_for_status()
        return PutResult(bucket=bucket, key=key, byte_size=len(data), checksum_sha256=checksum)

    async def get(self, bucket: str, key: str) -> bytes:
        url = self._url(bucket, key)
        headers = _build_auth_headers(
            "GET",
            url,
            access_key=self._access_key,
            secret_key=self._secret_key,
            region=self._region,
        )
        resp = await self._client.get(url, headers=headers)
        if resp.status_code == 404:
            raise StorageNotFoundError(bucket, key)
        resp.raise_for_status()
        return resp.content

    async def head(self, bucket: str, key: str) -> ObjectMetadata:
        url = self._url(bucket, key)
        headers = _build_auth_headers(
            "HEAD",
            url,
            access_key=self._access_key,
            secret_key=self._secret_key,
            region=self._region,
        )
        resp = await self._client.head(url, headers=headers)
        if resp.status_code == 404:
            raise StorageNotFoundError(bucket, key)
        resp.raise_for_status()
        content_length = int(resp.headers.get("content-length", "0"))
        content_type = resp.headers.get("content-type", "application/octet-stream")
        sha = resp.headers.get("x-amz-meta-checksum_sha256", "")
        raw_meta = {
            k[len("x-amz-meta-") :]: v
            for k, v in resp.headers.items()
            if k.lower().startswith("x-amz-meta-")
        }
        return ObjectMetadata(
            bucket=bucket,
            key=key,
            byte_size=content_length,
            content_type=content_type,
            checksum_sha256=sha,
            extra_meta=raw_meta,
        )

    async def delete(self, bucket: str, key: str) -> None:
        url = self._url(bucket, key)
        headers = _build_auth_headers(
            "DELETE",
            url,
            access_key=self._access_key,
            secret_key=self._secret_key,
            region=self._region,
        )
        resp = await self._client.delete(url, headers=headers)
        if resp.status_code not in (204, 404):
            resp.raise_for_status()

    async def exists(self, bucket: str, key: str) -> bool:
        url = self._url(bucket, key)
        headers = _build_auth_headers(
            "HEAD",
            url,
            access_key=self._access_key,
            secret_key=self._secret_key,
            region=self._region,
        )
        resp = await self._client.head(url, headers=headers)
        if resp.status_code == 404:
            return False
        resp.raise_for_status()
        return True

    async def ensure_bucket(self, bucket: str) -> None:
        url = self._bucket_url(bucket)
        headers = _build_auth_headers(
            "PUT",
            url,
            access_key=self._access_key,
            secret_key=self._secret_key,
            region=self._region,
        )
        resp = await self._client.put(url, headers=headers)
        if resp.status_code not in (200, 409):
            resp.raise_for_status()

    async def aclose(self) -> None:
        await self._client.aclose()
