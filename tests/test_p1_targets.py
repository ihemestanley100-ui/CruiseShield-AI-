"""P1 target adapter tests. Stubbed transports only; zero network.

B2 uses botocore Stubber against a real client; GitHub uses
httpx.MockTransport. Fake credentials are non-secret placeholders.
"""
import base64
import io

import boto3
import httpx
import pytest
from botocore.response import StreamingBody
from botocore.stub import Stubber

from backups import targets as targets_mod

FAKE = "TEST-ONLY-NOT-A-CREDENTIAL"


def _b2_client(stub_responses):
    client = boto3.client(
        "s3", endpoint_url="https://s3.test.invalid",
        aws_access_key_id="x", aws_secret_access_key="y",
        region_name="us-east-1")
    stubber = Stubber(client)
    for method, response in stub_responses:
        stubber.add_response(method, response)
    stubber.activate()
    return client


def test_b2_put_get_exists_round_trip():
    body = StreamingBody(io.BytesIO(b"ciphertext"), 10)
    client = _b2_client([
        ("put_object", {"ETag": '"abc123"'}),
        ("get_object", {"Body": body}),
        ("head_object", {}),
    ])
    target = targets_mod.B2Target(bucket="b", prefix="p/", endpoint_url="e",
                                  key_id=FAKE, app_key=FAKE, client=client)
    assert target.put("k/pgdump.age", b"ciphertext") == '"abc123"'
    assert target.get("k/pgdump.age") == b"ciphertext"
    assert target.exists("k/pgdump.age") is True


def test_b2_get_missing_maps_to_not_found():
    client = boto3.client(
        "s3", endpoint_url="https://s3.test.invalid",
        aws_access_key_id="x", aws_secret_access_key="y",
        region_name="us-east-1")
    stubber = Stubber(client)
    stubber.add_client_error("get_object", service_error_code="NoSuchKey",
                             http_status_code=404)
    stubber.activate()
    target = targets_mod.B2Target(bucket="b", endpoint_url="e", key_id=FAKE,
                                  app_key=FAKE, client=client)
    with pytest.raises(targets_mod.NotFoundError):
        target.get("missing.age")
    assert target.exists("missing.age") is False


def test_b2_errors_carry_no_credentials():
    client = boto3.client(
        "s3", endpoint_url="https://s3.test.invalid",
        aws_access_key_id="x", aws_secret_access_key="y",
        region_name="us-east-1")
    stubber = Stubber(client)
    stubber.add_client_error("put_object", http_status_code=403)
    stubber.activate()
    target = targets_mod.B2Target(bucket="b", endpoint_url="e", key_id=FAKE,
                                  app_key=FAKE, client=client)
    with pytest.raises(targets_mod.TargetError) as excinfo:
        target.put("k", b"v")
    assert FAKE not in str(excinfo.value)


def test_targets_expose_no_delete():
    for cls in (targets_mod.B2Target, targets_mod.GitTarget,
                targets_mod.BackupTarget):
        assert not hasattr(cls, "delete")
        assert not hasattr(cls, "remove")
        assert not hasattr(cls, "purge")


def _git_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler),
                        base_url="https://api.github.com")


def test_git_put_new_file_posts_without_sha():
    seen: dict = {}

    def handler(request):
        if request.method == "GET":
            return httpx.Response(404, json={"message": "nf"})
        seen["body"] = request.read().decode()
        return httpx.Response(201, json={"content": {"sha": "newsha"}})

    target = targets_mod.GitTarget(
        repo="o/r", token=FAKE, client=_git_client(handler))
    assert target.put("bk/m.age", b"data") == "newsha"
    assert '"sha"' not in seen["body"]


def test_git_put_existing_file_includes_sha():
    def handler(request):
        if request.method == "GET":
            return httpx.Response(200, json={"sha": "oldsha"})
        return httpx.Response(200, json={"content": {"sha": "updsha"}})

    target = targets_mod.GitTarget(
        repo="o/r", token=FAKE, client=_git_client(handler))
    assert target.put("bk/m.age", b"data") == "updsha"


def test_git_get_decodes_and_missing_maps():
    payload = base64.b64encode(b"stored-bytes").decode("ascii")

    def handler(request):
        path = request.url.path
        if path.endswith("present.age"):
            return httpx.Response(200, json={"content": payload,
                                             "sha": "s"})
        return httpx.Response(404, json={"message": "nf"})

    target = targets_mod.GitTarget(
        repo="o/r", token=FAKE, client=_git_client(handler))
    assert target.get("present.age") == b"stored-bytes"
    assert target.exists("present.age") is True
    with pytest.raises(targets_mod.NotFoundError):
        target.get("absent.age")
    assert target.exists("absent.age") is False


def test_git_errors_carry_no_token():
    def handler(request):
        return httpx.Response(401, json={"message": "bad"})

    target = targets_mod.GitTarget(
        repo="o/r", token=FAKE, client=_git_client(handler))
    with pytest.raises(targets_mod.TargetError) as excinfo:
        target.get("x.age")
    assert FAKE not in str(excinfo.value)
