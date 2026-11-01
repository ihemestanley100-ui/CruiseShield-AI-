"""P2 integration: snapshot -> produce -> verify -> restore, real adapters.

B2Target runs against an in-memory S3 client that raises genuine
botocore ClientErrors; GitTarget runs against a stateful
httpx.MockTransport. No network, no real credentials, ephemeral keys.
"""
import base64
import hashlib
import io

import httpx
import pytest
from botocore.exceptions import ClientError
from botocore.response import StreamingBody

import backup_fakes as fakes
from backups import produce as produce_mod
from backups import restore as restore_mod
from backups import targets as targets_mod

FAKE = "TEST-ONLY-NOT-A-CREDENTIAL"


class RecordingS3Client:
    """In-memory S3 with real ClientError shapes (no network)."""

    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], bytes] = {}
        self.calls: list[str] = []

    def put_object(self, *, Bucket, Key, Body):
        self.calls.append(f"put:{Key}")
        data = bytes(Body)
        self.objects[(Bucket, Key)] = data
        return {"ETag": f'"{hashlib.md5(data).hexdigest()}"'}

    def get_object(self, *, Bucket, Key):
        self.calls.append(f"get:{Key}")
        try:
            data = self.objects[(Bucket, Key)]
        except KeyError:
            raise ClientError(
                {"Error": {"Code": "NoSuchKey", "Message": "nf"},
                 "ResponseMetadata": {"HTTPStatusCode": 404}},
                "GetObject") from None
        return {"Body": StreamingBody(io.BytesIO(data), len(data))}

    def head_object(self, *, Bucket, Key):
        self.calls.append(f"head:{Key}")
        if (Bucket, Key) not in self.objects:
            raise ClientError(
                {"Error": {"Code": "404", "Message": "nf"},
                 "ResponseMetadata": {"HTTPStatusCode": 404}},
                "HeadObject") from None
        return {}


class GitRemote:
    """Stateful contents-API handler behind httpx.MockTransport."""

    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}
        self.calls: list[str] = []

    def handler(self, request):
        path = request.url.path.split("/contents/", 1)[1]
        if request.method == "GET":
            self.calls.append(f"get:{path}")
            if path not in self.files:
                return httpx.Response(404, json={"message": "nf"})
            return httpx.Response(200, json={
                "sha": hashlib.sha256(self.files[path]).hexdigest(),
                "content": base64.b64encode(self.files[path]).decode()})
        payload = request.read().decode()
        self.calls.append(f"put:{path}")
        import json as json_mod
        body = json_mod.loads(payload)
        self.files[path] = base64.b64decode(body["content"])
        return httpx.Response(201, json={
            "content": {"sha": hashlib.sha256(self.files[path]).hexdigest()}})


def _targets():
    s3 = RecordingS3Client()
    git = GitRemote()
    c2 = targets_mod.B2Target(bucket="bk", prefix="p/", endpoint_url="e",
                              key_id=FAKE, app_key=FAKE, client=s3)
    transport = httpx.MockTransport(git.handler)
    client = httpx.Client(transport=transport,
                          base_url="https://api.github.com")
    c3 = targets_mod.GitTarget(repo="o/r", token=FAKE, client=client)
    return {"c2": c2, "c3": c3}, s3, git


def test_end_to_end_two_generations_with_chain():
    targets, s3, git = _targets()
    keys = fakes.ephemeral_keys()
    snapshot = fakes.make_snapshot()
    first, _ = fakes.produce_once(targets, keys=keys, snapshot=snapshot)
    assert first["promoted"] is True
    second_id = "csbk-20261030-030000Z"
    second, _ = fakes.produce_once(
        targets, keys=keys, snapshot=snapshot, backup_id=second_id,
        created_at="20261030-030000Z",
        previous_manifest=first["manifest"])
    assert second["checks"]["chain_ok"] is True
    for backup_id in (fakes.BACKUP_ID, second_id):
        report = restore_mod.verify_backup_set(
            targets=targets, backup_id=backup_id, verify_key=keys[3],
            logger=fakes.null_logger())
        assert report["verified"] is True
        assert report["cross_copy_ok"] is True
    plan = restore_mod.plan_restore(
        target=targets["c2"], target_name="c2", backup_id=second_id,
        verify_key=keys[3], private_key=keys[0],
        logger=fakes.null_logger())
    assert plan.plaintext == snapshot.dump
    assert plan.checks["chain_ok"] is True
    assert ("bk", f"p/{second_id}/dump.csbk1") in s3.objects
    assert f"{second_id}/manifest.json" in git.files


def test_end_to_end_from_stub_snapshotter():
    targets, _, _ = _targets()
    conn = fakes.StubConnection(fakes.canned_scratch_db())
    snapshotter = produce_mod.PostgresSnapshotter(connect=lambda: conn)
    snapshot = snapshotter.capture()
    keys = fakes.ephemeral_keys()
    report, _ = fakes.produce_once(targets, keys=keys, snapshot=snapshot)
    assert report["promoted"] is True
    plan = restore_mod.plan_restore(
        target=targets["c3"], target_name="c3",
        backup_id=fakes.BACKUP_ID, verify_key=keys[3],
        private_key=keys[0], logger=fakes.null_logger())
    assert plan.plaintext == snapshot.dump
    assert conn.commits == 0  # snapshot never writes


def test_missing_key_maps_to_not_found_on_both_adapters():
    targets, _, _ = _targets()
    for name, target in targets.items():
        with pytest.raises(targets_mod.NotFoundError):
            target.get("no-such-backup/dump.csbk1")
        assert target.exists("no-such-backup/dump.csbk1") is False
