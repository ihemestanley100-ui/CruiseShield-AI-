import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type {
  IntelEvidence,
  IntelFinding,
  InvIntel,
  RiskIntelResult,
  TxnIntel,
} from "../lib/api";
import { IntelSection } from "./intel-panels";

function txnFixture(): TxnIntel {
  return {
    transaction_id: "txn_84721",
    source_account_id: "acct_A",
    destination_account_id: "acct_B",
    transaction_time: "2026-10-27T10:00:00Z",
    device_observations: [
      {
        obs_id: "o1",
        device_id: "dev_04",
        account_id: "acct_A",
        txn_id: "txn_84721",
        observed_at: "2026-10-27T10:00:00Z",
        source: "seed_event",
        source_ref: "evt_1",
        synthetic: true,
      },
    ],
    ip_observations: [
      {
        obs_id: "o2",
        ip_label: "ip_02",
        address: null,
        address_status: "unknown",
        account_id: "acct_A",
        txn_id: "txn_84721",
        observed_at: "2026-10-27T10:00:00Z",
        source: "seed_event",
        source_ref: "evt_1",
        synthetic: true,
      },
    ],
    geolocation_observations: [
      {
        obs_id: "o3",
        location_label: "loc_01",
        geo_status: "unavailable",
        reason: "no_provider_data",
        account_id: "acct_A",
        txn_id: "txn_84721",
        observed_at: "2026-10-27T10:00:00Z",
        source_ref: "evt_1",
        synthetic: true,
      },
    ],
    device_graph_refs: { dev_04: ["edge_1"] },
    observation_first_seen: "2026-10-27T10:00:00Z",
    observation_last_seen: "2026-10-27T10:00:00Z",
    provenance: { event_ids: ["evt_1"] },
    synthetic: true,
    limitations: ["fixture-derived"],
  };
}

function intelFixture(): InvIntel {
  return {
    investigation_id: "inv_84721",
    transaction_id: "txn_84721",
    transaction_intel: txnFixture(),
    isolation: "own-transaction only",
    synthetic: true,
    limitations: [],
  };
}

function findingFixture(): IntelFinding {
  return {
    finding_id: "DIF-DEV-KNOWN-dev_04-000",
    category: "DEVICE",
    signal_id: "DEV-KNOWN-dev_04",
    status: "PRESENT",
    subject_type: "investigation",
    subject_ref: "inv_84721",
    transaction_ref: "txn_84721",
    account_ref: "unknown",
    investigation_ref: "inv_84721",
    source_observation_ids: ["o1"],
    source_event_ids: ["evt_1"],
    source_edge_ids: [],
    observed_at: "2026-10-27T10:00:00Z",
    processed_at: "2026-10-30T10:00:00Z",
    evidence_refs: ["edge_1"],
    provenance: "DERIVED_FROM_SYNTHETIC",
    confidence: "low",
    freshness: "stale",
    synthetic: true,
    derivation_method: "di08_signal_translation_v1",
    explanation: "Device label observed.",
    limitations: ["Label only."],
    human_review: "required_before_any_action",
  };
}

function evidenceFixture(): IntelEvidence {
  return {
    investigation_id: "inv_84721",
    findings: [findingFixture()],
    trace: {
      investigation_id: "inv_84721",
      transaction_id: "txn_84721",
      findings: [],
      synthetic: true,
    },
    synthetic: true,
  };
}

function riskOffFixture(): RiskIntelResult {
  return {
    engine: "risk-intelligence-v2-candidate",
    enabled: false,
    status: "disabled_by_flag",
    detail: "v1 authoritative",
  };
}

describe("IntelSection", () => {
  it("renders device, IP, geo, findings, and v2-off state", () => {
    render(
      <IntelSection
        intel={intelFixture()}
        evidence={evidenceFixture()}
        risk={riskOffFixture()}
      />
    );
    expect(screen.getByTestId("intel-status")).toHaveTextContent(
      "1 finding(s)"
    );
    expect(screen.getAllByText(/dev_04/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("ip_02")).toBeTruthy();
    expect(screen.getByText("loc_01")).toBeTruthy();
    expect(screen.getByText(/NOT_CONFIGURED/)).toBeTruthy();
    expect(screen.getByText(/never proof of physical/)).toBeTruthy();
    expect(
      screen.getAllByText(/DIF-DEV-KNOWN-dev_04-000/).length
    ).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/DERIVED_FROM_SYNTHETIC/)).toBeTruthy();
    expect(
      screen.getByText(/candidate engine.*is OFF \(default\)/i)
    ).toBeTruthy();
  });

  it("masks raw IPs and never invents provider results", () => {
    const intel = intelFixture();
    const txn = intel.transaction_intel as TxnIntel;
    txn.ip_observations = [
      { ...txn.ip_observations[0], address: "192.168.1.10" },
    ];
    render(
      <IntelSection intel={intel} evidence={evidenceFixture()} risk={null} />
    );
    expect(screen.getByText(/192\.168\.1\.\u2022/)).toBeTruthy();
    expect(screen.queryByText("192.168.1.10")).toBeNull();
    expect(screen.queryByText(/att\/verizon/i)).toBeNull();
  });

  it("shows honest empty states for missing observations", () => {
    const intel = intelFixture();
    const txn = intel.transaction_intel as TxnIntel;
    txn.device_observations = [];
    txn.ip_observations = [];
    txn.geolocation_observations = [];
    render(
      <IntelSection
        intel={intel}
        evidence={{ ...evidenceFixture(), findings: [] }}
        risk={null}
      />
    );
    expect(screen.getByText(/No device observations/)).toBeTruthy();
    expect(screen.getByText(/No IP observations/)).toBeTruthy();
    expect(screen.getByText(/No location observations/)).toBeTruthy();
    expect(screen.getByText(/insufficient evidence/)).toBeTruthy();
  });

  it("shows an unavailable section when intel fetch failed", () => {
    render(<IntelSection intel={null} evidence={null} risk={null} />);
    expect(screen.getByTestId("intel-status")).toHaveTextContent(
      "Intelligence unavailable for this investigation."
    );
  });
});
