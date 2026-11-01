"""P1 shamir unit tests. Synthetic secrets only; ceremony semantics."""
import itertools

import pytest

from backups import shamir as shamir_mod

SECRET = b"test-only-secret-32-bytes-012345"


def test_two_of_four_all_pairs_combine():
    assert len(SECRET) == 32
    shares = shamir_mod.split_secret(SECRET, threshold=2, share_count=4)
    assert len(shares) == 4
    for pair in itertools.combinations(shares, 2):
        assert shamir_mod.combine_shares(list(pair)) == SECRET


def test_single_share_cannot_combine():
    shares = shamir_mod.split_secret(SECRET, threshold=2, share_count=4)
    with pytest.raises(shamir_mod.ShareError, match="COMBINE_FAILED"):
        shamir_mod.combine_shares([shares[0]])


def test_tampered_share_rejected():
    shares = shamir_mod.split_secret(SECRET, threshold=2, share_count=4)
    words = shares[0].split(" ")
    words[-1] = "abandon" if words[-1] != "abandon" else "ability"
    with pytest.raises(shamir_mod.ShareError, match="COMBINE_FAILED"):
        shamir_mod.combine_shares([" ".join(words), shares[1]])


def test_duplicate_share_rejected():
    shares = shamir_mod.split_secret(SECRET, threshold=2, share_count=4)
    with pytest.raises(shamir_mod.ShareError, match="COMBINE_FAILED"):
        shamir_mod.combine_shares([shares[0], shares[0]])
    with pytest.raises(shamir_mod.ShareError, match="COMBINE_FAILED"):
        shamir_mod.combine_shares([shares[2], shares[2], shares[2]])


def test_invalid_mnemonics_rejected():
    with pytest.raises(shamir_mod.ShareError, match="COMBINE_FAILED"):
        shamir_mod.combine_shares(["not a mnemonic at all"])
    with pytest.raises(shamir_mod.ShareError, match="NO_SHARES"):
        shamir_mod.combine_shares([])


def test_bad_parameters_rejected():
    with pytest.raises(shamir_mod.ShareError, match="BAD_THRESHOLD"):
        shamir_mod.split_secret(SECRET, threshold=5, share_count=4)
    with pytest.raises(shamir_mod.ShareError, match="BAD_THRESHOLD"):
        shamir_mod.split_secret(SECRET, threshold=0, share_count=4)
    with pytest.raises(shamir_mod.ShareError, match="BAD_SECRET_LEN"):
        shamir_mod.split_secret(b"short", threshold=2, share_count=4)


def test_shares_reveal_nothing_alone():
    shares = shamir_mod.split_secret(SECRET, threshold=2, share_count=4)
    assert len(set(shares)) == 4
    for share in shares:
        assert SECRET.hex() not in share


def test_ceremony_only_no_automation_imports():
    """Producer-adjacent modules must never import the ceremony module."""
    import ast
    import pathlib

    root = pathlib.Path(__file__).resolve().parent.parent / "backups"
    for name in ("crypto.py", "signing.py", "targets.py", "integrity.py",
                 "manifest.py", "logutil.py", "produce.py", "restore.py"):
        tree = ast.parse((root / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                mods = [node.module or ""] + [alias.name
                                              for alias in node.names]
            else:
                continue
            bad = [mod for mod in mods
                   if mod == "shamir" or mod.endswith(".shamir")]
            assert not bad, f"{name} must not import shamir: {bad}"
