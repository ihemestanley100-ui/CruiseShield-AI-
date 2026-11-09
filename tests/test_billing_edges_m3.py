"""M3 billing edge semantics: lifecycle corners that D-040 pins down."""
from app import billing as billing_mod


def test_double_cancel_is_stable(tmp_store):
    billing_mod.start_subscription(tmp_store, "amy", "starter", "order-1")
    first = billing_mod.cancel_subscription(tmp_store, "amy")
    assert first["status"] == "cancelled"
    second = billing_mod.cancel_subscription(tmp_store, "amy")
    assert second["status"] == "cancelled"


def test_resubscribe_after_cancel_reactivates(tmp_store):
    billing_mod.start_subscription(tmp_store, "amy", "starter", "order-1")
    billing_mod.cancel_subscription(tmp_store, "amy")
    rec = billing_mod.start_subscription(tmp_store, "amy", "business",
                                         "order-2")
    assert (rec["plan"], rec["status"]) == ("business", "active")
    assert rec["evidence"] == "order-2"


def test_payment_event_overwrites_last_outcome(tmp_store):
    billing_mod.start_subscription(tmp_store, "amy", "starter", "order-1")
    billing_mod.record_payment_event(tmp_store, "amy", "recon-1", ok=False)
    assert tmp_store.subscription_for("amy")["status"] == "past_due"
    rec = billing_mod.record_payment_event(tmp_store, "amy", "recon-2",
                                           ok=True)
    assert rec["status"] == "active"
    assert rec["last_payment"]["reference"] == "recon-2"


def test_payment_event_on_cancelled_plan_documents_resurrect(tmp_store):
    billing_mod.start_subscription(tmp_store, "amy", "starter", "order-1")
    billing_mod.cancel_subscription(tmp_store, "amy")
    rec = billing_mod.record_payment_event(tmp_store, "amy", "recon-9",
                                           ok=True)
    # Reference-only recording follows the provider outcome verbatim;
    # reconciliation disputes are resolved out-of-band, not by guessing.
    assert rec["status"] == "active"


def test_founder_match_is_exact_username(tmp_store):
    assert billing_mod.founder_active(tmp_store, "boss", "boss") is True
    assert billing_mod.founder_active(tmp_store, "boss", "  ") is False
    assert billing_mod.founder_active(tmp_store, "boss", "") is False
    assert billing_mod.founder_active(tmp_store, " boss", "boss") is False
    assert billing_mod.founder_active(tmp_store, "BOSS", "boss") is False


def test_metering_only_honours_active_subscriptions(tmp_store):
    billing_mod.start_subscription(tmp_store, "past", "starter", "o-1")
    billing_mod.record_payment_event(tmp_store, "past", "r-1", ok=False)
    billed = billing_mod.metered_action(tmp_store, "past", "", True)
    assert billed is not None and billed["credits"] == 1
    billing_mod.start_subscription(tmp_store, "gone", "starter", "o-2")
    billing_mod.cancel_subscription(tmp_store, "gone")
    billed = billing_mod.metered_action(tmp_store, "gone", "", True)
    assert billed is not None and billed["credits"] == 1
