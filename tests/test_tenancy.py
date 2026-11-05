"""Tenant scoping tests: isolation + default-tenant back-compat."""
import pytest

from app import tenancy
from app.tenancy import (DEFAULT_TENANT, TenantContext, TenantDeniedError,
                         enforce_read, enforce_write, filter_visible,
                         known_tenants, register_tenant, stamp, tenant_of)

ALPHA = TenantContext(tenant_id=DEFAULT_TENANT, actor="alice")
BETA = TenantContext(tenant_id="org_beta", actor="bob")


@pytest.fixture(autouse=True)
def _beta():
    register_tenant("org_beta")
    yield


def _case(owner):
    record = {"case_id": "c1", "title": "t"}
    if owner is not None:
        record["tenant_id"] = owner
    return record


def test_default_tenant_back_compat():
    assert tenant_of(_case(None)) == DEFAULT_TENANT
    assert enforce_read(_case(None), ALPHA) is not None


def test_cross_tenant_read_is_not_found():
    assert enforce_read(_case("org_beta"), ALPHA) is None
    assert enforce_read(_case(DEFAULT_TENANT), BETA) is None


def test_same_tenant_read_ok():
    record = _case("org_beta")
    assert enforce_read(record, BETA) is record


def test_cross_tenant_write_denied():
    with pytest.raises(TenantDeniedError):
        enforce_write(_case("org_beta"), ALPHA)


def test_same_tenant_write_ok():
    enforce_write(_case("org_beta"), BETA)  # must not raise


def test_enumeration_excludes_foreign():
    rows = [_case(DEFAULT_TENANT), _case("org_beta"), _case(None)]
    got = filter_visible(rows, BETA)
    assert [tenant_of(r) for r in got] == ["org_beta"]


def test_stamp_tags_new_records():
    record = stamp({"case_id": "new"}, BETA)
    assert record["tenant_id"] == "org_beta"


def test_unknown_tenant_id_falls_back_to_default():
    assert tenant_of(_case("org_nope")) == DEFAULT_TENANT


def test_register_rejects_bad_ids():
    for bad in ("", "UPPER", "has space", "x" * 65, "../evil"):
        with pytest.raises(ValueError):
            register_tenant(bad)


def test_known_tenants_lists_both():
    assert {DEFAULT_TENANT, "org_beta"} <= set(known_tenants())


def test_pg_tenancy_migration_covers_load_order():
    from app import models_pg

    for table in models_pg.TENANT_TABLES:
        assert table in models_pg.LOAD_ORDER
        assert ("ALTER TABLE %s ADD COLUMN IF NOT EXISTS tenant_id"
                % table) in models_pg.MIGRATION_5_2_TENANCY
    assert models_pg.MIGRATION_5_2_TENANCY.count(
        "DEFAULT 'org_primary'") == len(models_pg.TENANT_TABLES)
