"""Backup target abstraction + C2/C3 adapters (Phase 5.4F/P1).

Least privilege is enforced in CODE: targets expose put/get/exists only.
There is deliberately no delete, overwrite-bypass, or retention API here.

- B2Target: Backblaze B2 via the S3-compatible API (boto3). Tested with
  botocore stubs; no network in tests.
- GitTarget: private GitHub repository via the contents REST API (httpx).
  Tested with httpx.MockTransport; no network in tests.

Credentials are constructor arguments, never logged, and never included
in error messages.
"""
from __future__ import annotations

import base64
from abc import ABC, abstractmethod
from typing import Any


class TargetError(Exception):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code


class NotFoundError(TargetError):
    def __init__(self, path: str) -> None:
        super().__init__("NOT_FOUND", path)


class BackupTarget(ABC):
    """Put/get/exists only. No delete exists on any target, by design."""

    @abstractmethod
    def put(self, path: str, data: bytes) -> str:
        """Store data; returns a version/etag receipt."""

    @abstractmethod
    def get(self, path: str) -> bytes:
        """Fetch data; raises NotFoundError when absent."""

    @abstractmethod
    def exists(self, path: str) -> bool:
        """True when the path is stored."""


def _is_not_found(exc: Exception) -> bool:
    """True for S3 no-such-key responses (structured, no string scraping)."""
    response = getattr(exc, "response", None)
    if isinstance(response, dict):
        if response.get("Error", {}).get("Code") == "NoSuchKey":
            return True
        metadata = response.get("ResponseMetadata", {})
        if metadata.get("HTTPStatusCode") == 404:
            return True
    return False


class B2Target(BackupTarget):
    """C2 Backblaze B2 over the S3-compatible API."""

    def __init__(self, *, bucket: str, prefix: str = "",
                 endpoint_url: str, key_id: str, app_key: str,
                 client: Any = None) -> None:
        import boto3

        self._bucket = bucket
        self._prefix = prefix
        self._client = client or boto3.client(
            "s3", endpoint_url=endpoint_url, aws_access_key_id=key_id,
            aws_secret_access_key=app_key)

    def _key(self, path: str) -> str:
        return f"{self._prefix}{path}"

    def put(self, path: str, data: bytes) -> str:
        try:
            response = self._client.put_object(
                Bucket=self._bucket, Key=self._key(path), Body=data)
        except Exception as exc:
            raise TargetError("B2_PUT_FAILED",
                              type(exc).__name__) from None
        return str(response.get("ETag", ""))

    def get(self, path: str) -> bytes:
        try:
            response = self._client.get_object(
                Bucket=self._bucket, Key=self._key(path))
            return bytes(response["Body"].read())
        except Exception as exc:
            if _is_not_found(exc):
                raise NotFoundError(path) from None
            raise TargetError("B2_GET_FAILED",
                              type(exc).__name__) from None

    def exists(self, path: str) -> bool:
        try:
            self._client.head_object(Bucket=self._bucket,
                                     Key=self._key(path))
            return True
        except Exception:
            return False


class GitTarget(BackupTarget):
    """C3 private GitHub repository over the contents REST API."""

    _API = "https://api.github.com"

    def __init__(self, *, repo: str, token: str, branch: str = "main",
                 client: Any = None) -> None:
        import httpx

        self._repo = repo
        self._branch = branch
        self._client = client or httpx.Client(
            base_url=self._API,
            headers={"Authorization": f"Bearer {token}",
                     "Accept": "application/vnd.github+json",
                     "X-GitHub-Api-Version": "2022-11-28"})

    def _contents_url(self, path: str) -> str:
        return f"/repos/{self._repo}/contents/{path}"

    def put(self, path: str, data: bytes) -> str:
        import httpx

        body: dict[str, Any] = {
            "message": f"backup: store {path}",
            "content": base64.b64encode(data).decode("ascii"),
            "branch": self._branch,
        }
        try:
            current = self._client.get(self._contents_url(path),
                                       params={"ref": self._branch})
            if current.status_code == 200:
                body["sha"] = current.json().get("sha")
            response = self._client.put(self._contents_url(path), json=body)
            response.raise_for_status()
        except NotFoundError:
            raise
        except httpx.HTTPStatusError as exc:
            raise TargetError("GIT_PUT_FAILED",
                              str(exc.response.status_code)) from None
        except Exception as exc:
            raise TargetError("GIT_PUT_FAILED",
                              type(exc).__name__) from None
        return str(response.json().get("content", {}).get("sha", ""))

    def get(self, path: str) -> bytes:
        import httpx

        try:
            response = self._client.get(self._contents_url(path),
                                        params={"ref": self._branch})
            if response.status_code == 404:
                raise NotFoundError(path)
            response.raise_for_status()
            payload = response.json()
        except NotFoundError:
            raise
        except httpx.HTTPStatusError as exc:
            raise TargetError("GIT_GET_FAILED",
                              str(exc.response.status_code)) from None
        except Exception as exc:
            raise TargetError("GIT_GET_FAILED",
                              type(exc).__name__) from None
        content = payload.get("content", "")
        try:
            return base64.b64decode("".join(content.split()))
        except Exception:
            raise TargetError("GIT_BAD_CONTENT", path) from None

    def exists(self, path: str) -> bool:
        try:
            response = self._client.get(self._contents_url(path),
                                        params={"ref": self._branch})
            return response.status_code == 200
        except Exception:
            return False
