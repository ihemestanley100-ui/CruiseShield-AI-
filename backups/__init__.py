"""Backup tooling: manifests (5.4C) + P1 crypto (5.4F) + P2 producer (5.4F).

P1 scope: crypto, signing, shamir (ceremony-only), targets, integrity.
P2 scope: logutil, produce, restore. No schedules run anywhere: the
three GitHub workflows are disabled by default and require an explicit
manual enable plus secrets that are not installed. No real keys,
provider connections, or execution happen from this package alone.
"""
from __future__ import annotations
