import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type {
  AcctIntel,
  DeviceProfile,
  GeoObservationResult,
  IntelEvidence,
  IntelFinding,
  InvIntel,
  IpObservationList,
  RiskIntelResult,
  TxnIntel,
} from "../lib/api";
import {
  DeviceBlock,
  GeoBlock,
  IntelSection,
  IpBlock,
} from "./intel-panels";

const { getDeviceMock, getIpObservationsMock, getGeoObservationsMock } =
  vi.hoisted(() => ({
    getDeviceMock: vi.fn(),
    getIpObservationsMock: vi.fn(),
    getGeoObservationsMock: vi.fn(),
  }));

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
  }: {
    href: string;
    children: React.ReactNode;
  }) => <a href={href}>{children}</a>,
}));

vi.mock("../lib/api", async (importOriginal) => ({
  ...((await importOriginal()) as object),
  getDevice: getDeviceMock,
  getIpObservations: getIpObservationsMock,
  getGeoObservations: getGeoObservationsMock,
}));

beforeEach(() => {
  getDeviceMock.mockReset();
  getIpObservationsMock.mockReset();
  getGeoObservationsMock.mockReset();
});

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

function profileFixture(): DeviceProfile {
  return {
    device_id: "dev_04",
    identity_status: "observed_only",
    disclaimer: "Synthetic fixture.",
    first_seen: "2026-10-27T10:00:00Z",
    last_seen: "2026-10-27T12:00:00Z",
    account_ids: ["acct_A", "acct_B"],
    txn_ids: ["txn_84721", "txn_90001"],
    observation_count: 3,
    shared: true,
    attributes: null,
    attributes_source: "none",
    observations: [],
    evidence_refs: { graph_edge_ids: ["edge_0002"], event_ids: [] },
  };
}

function ipListFixture(): IpObservationList {
  return {
    ip_label: "ip_02",
    address_status: "unknown",
    observations: [
      {
        obs_id: "obs_ip_9",
        ip_label: "ip_02",
        address: "10.9.9.9",
        address_status: "unknown",
        account_id: "acct_B",
        txn_id: "txn_90001",
        observed_at: "2026-10-27T11:00:00Z",
        source: "seed_event",
        source_ref: "evt_90001",
        synthetic: true,
      },
    ],
  };
}

function geoLookupFixture(): GeoObservationResult {
  return {
    identifier: "loc_01",
    kind: "lookup",
    lookup: {
      status: "resolved",
      country_code: "NG",
      city: "Lagos",
      confidence: "high",
      approximate_only: true,
      reason: "Seeded fixture lookup.",
    },
    observations: [],
  };
}

function acctBlockFixture(): AcctIntel {
  return {
    account_id: "acct_A",
    known_devices: ["dev_04"],
    known_ip_labels: ["ip_02"],
    known_geo_labels: ["loc_01"],
    first_seen: "2026-10-27T10:00:00Z",
    last_seen: "2026-10-27T12:00:00Z",
    shared_devices: [],
    shared_ips: [],
    transaction_count: 1,
    transaction_ids: ["txn_84721"],
    investigation_count: 1,
    investigation_ids: ["inv_84721"],
    provenance: { event_ids: ["evt_84721"] },
    synthetic: true,
    limitations: ["Synthetic fixture."],
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
  it("expands a device row into its label-level profile (GAP-013)", async () => {
    getDeviceMock.mockResolvedValue(profileFixture());
    render(<DeviceBlock intel={txnFixture()} />);
    expect(screen.queryByText(/acct_A, acct_B/)).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Show provenance" }));
    await waitFor(() => {
      expect(getDeviceMock).toHaveBeenCalledWith("dev_04");
    });
    expect(screen.getByText(/shared device/)).toBeTruthy();
    expect(screen.getByText(/observed_only/)).toBeTruthy();
    expect(screen.getByText(/acct_A, acct_B/)).toBeTruthy();
  });

  it("shows a retryable error when the device fetch fails", async () => {
    getDeviceMock.mockRejectedValue(new Error("down"));
    render(<DeviceBlock intel={txnFixture()} />);
    fireEvent.click(screen.getByRole("button", { name: "Show provenance" }));
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Retry" })).toBeTruthy();
    });
    expect(screen.getByRole("alert")).toBeTruthy();
  });

  it("expands an IP row with cross-transaction sightings (GAP-013)", async () => {
    getIpObservationsMock.mockResolvedValue(ipListFixture());
    render(<IpBlock intel={txnFixture()} />);
    fireEvent.click(screen.getByRole("button", { name: "Show provenance" }));
    await waitFor(() => {
      expect(screen.getByText(/txn_90001/)).toBeTruthy();
    });
    expect(getIpObservationsMock).toHaveBeenCalledWith("ip_02");
    const link = screen.getByRole("link", {
      name: /Open network explorer txn_90001/,
    });
    expect(link.getAttribute("href")).toBe("/network/txn_90001");
  });

  it("expands a geo row into its lookup result (GAP-013)", async () => {
    getGeoObservationsMock.mockResolvedValue(geoLookupFixture());
    render(<GeoBlock intel={txnFixture()} />);
    fireEvent.click(screen.getByRole("button", { name: "Show provenance" }));
    await waitFor(() => {
      expect(screen.getByText(/Lagos/)).toBeTruthy();
    });
    expect(screen.getByText(/Seeded fixture lookup/)).toBeTruthy();
  });

  it("renders per-account blocks with links when provided (GAP-012)", () => {
    render(
      <IntelSection
        intel={intelFixture()}
        evidence={evidenceFixture()}
        risk={riskOffFixture()}
        accounts={{ sender: acctBlockFixture(), receiver: null }}
      />
    );
    expect(screen.getByRole("heading", { name: "acct_A" })).toBeTruthy();
    expect(screen.getByText("Synthetic fixture.")).toBeTruthy();
    const invLink = screen.getByRole("link", {
      name: /Open investigation inv_84721/,
    });
    expect(invLink.getAttribute("href")).toBe("/investigations/inv_84721");
    const netLink = screen.getByRole("link", {
      name: /Open network explorer txn_84721/,
    });
    expect(netLink.getAttribute("href")).toBe("/network/txn_84721");
  });
  it("renders device, IP, geo, findings, and v2-off state", () => {
    render(
      <IntelSection
        intel={intelFixture()}
        evidence={evidenceFixture()}
        risk={riskOffFixture()}
      />
    );
    expect(screen.getByTestId("intel-status")).toHaveTextContent(
      "1 finding"
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
