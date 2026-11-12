import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type {
  ChannelsSummary,
  DetectionMatrix,
  DetectorList,
  SignalsSummary,
  SignalsTimeSeries,
  TxnSignals,
} from "../lib/api";
import {
  ChannelActivityPanel,
  DetectionSection,
  DetectorChannelMatrix,
  DetectorHealthPanel,
  SignalFrequencyPanel,
  TimeSeriesPanel,
  TxnSignalsPanel,
} from "./detection-panels";

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
  }: {
    href: string;
    children: React.ReactNode;
  }) => <a href={href}>{children}</a>,
}));

function summaryFixture(): SignalsSummary {
  return {
    total_signals: 5,
    unique_transactions_flagged: 3,
    unique_entities_flagged: 4,
    by_family: { RULE_MATCH: 3, VELOCITY: 2 },
    by_severity: { high: 1, medium: 4 },
    measurement_period: {
      start: "2026-10-27T10:00:00Z",
      end: "2026-10-27T12:00:00Z",
    },
    generated_at: "2026-11-05T20:00:00Z",
    tenant_scope: "org_primary",
    evaluation: {
      transactions_evaluated: 11,
      detector_version: "1.0",
      latency_ms: 3.5,
      unknown_location_txns: 10,
      note: "Derived on demand.",
    },
    note: "Zero means measured none.",
  };
}

function detectorsFixture(): DetectorList {
  return {
    detectors: [
      {
        family: "VELOCITY",
        version: "1.0",
        status: "OPERATIONAL",
        description: "2+ transfers in 120 minutes.",
        rules: ["R-002"],
      },
      {
        family: "ML_ANOMALY",
        version: "1.0",
        status: "NOT_IMPLEMENTED",
        description: "No model deployed.",
        rules: [],
      },
    ],
  };
}

function channelsFixture(): ChannelsSummary {
  return {
    channels: [
      {
        channel: "POS",
        transactions: 2,
        unique_transactions: 2,
        signals: 3,
        unique_flagged: 2,
        last_seen: "2026-10-27T11:00:00Z",
        integration: "SEED_FEED",
        note: "Seed feed.",
      },
      {
        channel: "TRANSFER",
        transactions: 0,
        unique_transactions: 0,
        signals: 0,
        unique_flagged: 0,
        last_seen: "",
        integration: "SEED_FEED",
        note: "No qualifying transactions recorded.",
      },
    ],
    unmapped_raw_codes: ["QR"],
    unmapped_alert: true,
    generated_at: "2026-11-05T20:00:00Z",
    tenant_scope: "org_primary",
  };
}

const MATRIX_CHANNELS = [
  "POS",
  "MOBILE_APP",
  "USSD",
  "NIP",
  "WEB",
  "ATM",
  "TRANSFER",
  "AGENT",
];

function matrixFixture(): DetectionMatrix {
  const cells = [];
  for (const family of ["RULE_MATCH", "ML_ANOMALY"]) {
    for (const channel of MATRIX_CHANNELS) {
      cells.push({
        family,
        channel,
        status:
          family === "ML_ANOMALY"
            ? "NOT_YET_IMPLEMENTED"
            : channel === "TRANSFER"
              ? "AWAITING_DATA_SOURCE"
              : "SUPPORTED_AND_ACTIVE",
        signals: family === "RULE_MATCH" && channel === "POS" ? 3 : 0,
        transactions: channel === "TRANSFER" ? 0 : 2,
        evidence_signal_id:
          family === "RULE_MATCH" && channel === "POS" ? "sig001" : "",
      });
    }
  }
  return {
    cells,
    generated_at: "2026-11-05T20:00:00Z",
    tenant_scope: "org_primary",
  };
}

describe("SignalFrequencyPanel", () => {
  it("renders totals, breakdowns, and honesty notes", () => {
    render(<SignalFrequencyPanel summary={summaryFixture()} />);
    expect(screen.getByText("Signal frequency")).toBeTruthy();
    expect(screen.getByText("5")).toBeTruthy();
    expect(screen.getByText("RULE_MATCH")).toBeTruthy();
    expect(screen.getByText("high")).toBeTruthy();
    expect(
      screen.getByText("Zero means measured none, not missing data.")
    ).toBeTruthy();
  });

  it("renders the measured-zero state", () => {
    render(
      <SignalFrequencyPanel
        summary={{ ...summaryFixture(), total_signals: 0, by_family: {} }}
      />
    );
    expect(
      screen.getByText("No qualifying signals recorded in this period.")
    ).toBeTruthy();
  });

  it("renders investigations and the false-positive basis when present", () => {
    render(
      <SignalFrequencyPanel
        summary={{
          ...summaryFixture(),
          unique_investigations_created: 2,
          false_positive_rate: 0.25,
          false_positive_basis: "1 dismissed of 4 reviewed",
        }}
      />
    );
    expect(screen.getByText(/2 investigations/)).toBeTruthy();
    expect(screen.getByText(/False-positive rate/)).toBeTruthy();
    expect(screen.getByText(/1 dismissed of 4 reviewed/)).toBeTruthy();
  });

  it("omits the false-positive row when no basis is recorded", () => {
    render(<SignalFrequencyPanel summary={summaryFixture()} />);
    expect(screen.queryByText(/False-positive rate/)).toBeNull();
  });
});

describe("TimeSeriesPanel", () => {
  function seriesFixture(): SignalsTimeSeries {
    return {
      granularity: "day",
      buckets: [
        { bucket: "2026-10-27", signals: 3, unique_txns: 2 },
        { bucket: "2026-10-28", signals: 0, unique_txns: 0 },
      ],
      total_signals: 3,
      measurement_period: {
        start: "2026-10-27T10:00:00Z",
        end: "2026-10-27T12:00:00Z",
      },
      generated_at: "2026-11-05T20:00:00Z",
      tenant_scope: "org_primary",
    };
  }

  it("renders buckets as an accessible chart plus a text list", () => {
    render(<TimeSeriesPanel series={seriesFixture()} />);
    expect(screen.getByText(/Signal time series/)).toBeTruthy();
    expect(
      screen.getByRole("img", { name: /3 signals in 2 buckets/ })
    ).toBeTruthy();
    expect(screen.getByText("2026-10-27")).toBeTruthy();
    expect(screen.getByText("2026-10-28")).toBeTruthy();
  });

  it("renders the measured-zero state", () => {
    render(
      <TimeSeriesPanel
        series={{ ...seriesFixture(), buckets: [], total_signals: 0 }}
      />
    );
    expect(
      screen.getByText("No qualifying signals recorded in this period.")
    ).toBeTruthy();
  });
});

describe("DetectorHealthPanel", () => {
  it("labels unimplemented detectors honestly", () => {
    render(<DetectorHealthPanel detectors={detectorsFixture().detectors} />);
    expect(screen.getByText("Detector families")).toBeTruthy();
    expect(screen.getByText("VELOCITY")).toBeTruthy();
    expect(screen.getByText("OPERATIONAL")).toBeTruthy();
    expect(screen.getByText("ML_ANOMALY")).toBeTruthy();
    expect(
      screen.getByText("Not implemented: no model deployed.")
    ).toBeTruthy();
  });
});

describe("ChannelActivityPanel", () => {
  it("renders rows, zero notes, and the unmapped alert", () => {
    render(<ChannelActivityPanel summary={channelsFixture()} />);
    expect(screen.getByText("Channel activity")).toBeTruthy();
    expect(screen.getByText("POS")).toBeTruthy();
    expect(screen.getByText("TRANSFER")).toBeTruthy();
    expect(
      screen.getByText("No qualifying transactions recorded.")
    ).toBeTruthy();
    const alert = screen.getByRole("alert");
    expect(alert.textContent).toContain("QR");
    expect(
      screen.getByText("Seed feed: no live channel integration.")
    ).toBeTruthy();
  });
});

describe("DetectorChannelMatrix", () => {
  it("renders an accessible table with honest statuses", () => {
    render(<DetectorChannelMatrix matrix={matrixFixture()} />);
    expect(screen.getByText("Detector by channel")).toBeTruthy();
    const table = screen.getByRole("table");
    expect(table.textContent).toContain("NOT_YET_IMPLEMENTED");
    expect(table.textContent).toContain("AWAITING_DATA_SOURCE");
    expect(table.textContent).toContain("SUPPORTED_AND_ACTIVE");
    expect(
      screen.getAllByRole("columnheader").map((h) => h.textContent)
    ).toContain("TRANSFER");
    expect(
      screen.getAllByRole("rowheader").map((h) => h.textContent)
    ).toContain("ML_ANOMALY");
  });
});

describe("TxnSignalsPanel", () => {
  function txnFixture(): TxnSignals {
    return {
      transaction_id: "txn_84721",
      signals: [
        {
          signal_id: "sig001",
          detector_family: "VELOCITY",
          detector_version: "1.0",
          rule_id: "R-002",
          rule_version: "1.0",
          transaction_id: "txn_84721",
          channel: "POS",
          severity: "medium",
          occurred_at: "2026-10-27T10:00:00Z",
          tenant_id: "org_primary",
          entities: { sender: "acct_A", receiver: "acct_B" },
          reason: "R-002 fired",
          evidence: {},
          outcome: "PENDING",
        },
      ],
      signal_count: 1,
      investigation: {
        investigation_id: "inv_84721",
        alert_id: "alert_84721",
        transaction_id: "txn_84721",
        status: "OPEN",
      },
      case: null,
      audits: [],
      tenant_scope: "org_primary",
    };
  }

  it("lists signals and links the investigation", () => {
    render(<TxnSignalsPanel data={txnFixture()} />);
    expect(screen.getByText("Transaction signals")).toBeTruthy();
    expect(screen.getByText("VELOCITY")).toBeTruthy();
    const link = screen.getByRole("link", { name: /Open investigation/ });
    expect(link.getAttribute("href")).toBe("/investigations/inv_84721");
  });

  it("handles zero signals and no linked investigation", () => {
    render(
      <TxnSignalsPanel
        data={{ ...txnFixture(), signals: [], signal_count: 0, investigation: null }}
      />
    );
    expect(
      screen.getByText("No qualifying signals recorded in this period.")
    ).toBeTruthy();
    expect(screen.getByText("No linked investigation.")).toBeTruthy();
  });
});

describe("DetectionSection", () => {
  it("composes all four panels", () => {
    render(
      <DetectionSection
        bundle={{
          summary: summaryFixture(),
          channels: channelsFixture(),
          detectors: detectorsFixture(),
          matrix: matrixFixture(),
        }}
      />
    );
    expect(screen.getByText("Detection intelligence")).toBeTruthy();
    expect(screen.getByText("Signal frequency")).toBeTruthy();
    expect(screen.getByText("Detector families")).toBeTruthy();
    expect(screen.getByText("Channel activity")).toBeTruthy();
    expect(screen.getAllByText("Detector by channel").length).toBeGreaterThan(0);
  });
});
