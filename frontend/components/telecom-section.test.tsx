import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { TelecomSummary } from "../lib/api";
import { TelecomSection } from "./telecom-section";

const { summaryMock, verificationMock, requestMock } = vi.hoisted(() => ({
  summaryMock: vi.fn(),
  verificationMock: vi.fn(),
  requestMock: vi.fn(),
}));

vi.mock("../lib/api", async (importOriginal) => ({
  ...((await importOriginal()) as object),
  getTelecomSummary: summaryMock,
  getTelecomVerification: verificationMock,
  requestTelecomVerification: requestMock,
}));

beforeEach(() => {
  summaryMock.mockReset();
  verificationMock.mockReset();
  requestMock.mockReset();
});

function summaryFixture(): TelecomSummary {
  return {
    history: [
      {
        verification_id: "tvrf_000001",
        verify_type: "carrier_identification",
        state: "PARTIALLY_VERIFIED",
        verified_at: "2026-11-07T08:00:00Z",
        stale: false,
      },
    ],
    co_signals: {
      devices: ["dev_04"],
      accounts: ["acct_A", "acct_B"],
      beneficiaries: ["acct_B"],
      geo_labels: ["loc_01"],
      transaction_count: 2,
    },
    history_count: 1,
    subject_masked: "+234******67",
    allocation: {
      operator_id: "mtn-ng",
      country: "NG",
      basis: "ncc-allocation-prefix:0803",
      limitation: "allocation range only",
    },
    phone_label: "phn_01",
  };
}

describe("TelecomSection", () => {
  it("stays closed until expanded, then shows allocation", async () => {
    summaryMock.mockResolvedValue(summaryFixture());
    render(<TelecomSection phoneLabel="phn_01" />);
    expect(summaryMock).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { expanded: false }));
    await waitFor(() => expect(summaryMock).toHaveBeenCalledTimes(1));
    expect(await screen.findByText("mtn-ng")).toBeTruthy();
    expect(screen.getByText(/allocation range only/)).toBeTruthy();
  });

  it("renders history states verbatim with stale flag", async () => {
    const fixture = summaryFixture();
    fixture.history[0].stale = true;
    summaryMock.mockResolvedValue(fixture);
    render(<TelecomSection phoneLabel="phn_01" />);
    fireEvent.click(screen.getByRole("button", { expanded: false }));
    expect(await screen.findByText(/PARTIALLY_VERIFIED/)).toBeTruthy();
    expect(screen.getByText(/STALE/)).toBeTruthy();
  });

  it("renders co-signals without verdicts", async () => {
    summaryMock.mockResolvedValue(summaryFixture());
    render(<TelecomSection phoneLabel="phn_01" />);
    fireEvent.click(screen.getByRole("button", { expanded: false }));
    expect(await screen.findByText("dev_04")).toBeTruthy();
    expect(screen.queryByText(/fraud/i)).toBeNull();
  });

  it("shows error with retry on failure", async () => {
    summaryMock.mockRejectedValueOnce(new Error("down"));
    summaryMock.mockResolvedValue(summaryFixture());
    render(<TelecomSection phoneLabel="phn_01" />);
    fireEvent.click(screen.getByRole("button", { expanded: false }));
    expect(await screen.findByRole("alert")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /retry/i }));
    await waitFor(() => expect(summaryMock).toHaveBeenCalledTimes(2));
  });

  it("expands verification detail on demand", async () => {
    summaryMock.mockResolvedValue(summaryFixture());
    verificationMock.mockResolvedValue({
      verification_id: "tvrf_000001",
      state: "PARTIALLY_VERIFIED",
      previous_state: "",
      source: "INFERRED",
      provider: "none",
      provider_ref: "",
      api: "",
      api_version: "",
      confidence: "MEDIUM",
      verified_at: "2026-11-07T08:00:00Z",
      integrity: "ok",
      limitations: ["allocation range only"],
    });
    render(<TelecomSection phoneLabel="phn_01" />);
    fireEvent.click(screen.getByRole("button", { expanded: false }));
    const toggles = await screen.findAllByRole("button", {
      expanded: false,
    });
    fireEvent.click(toggles[toggles.length - 1]);
    await waitFor(() =>
      expect(verificationMock).toHaveBeenCalledWith("tvrf_000001")
    );
    expect(await screen.findByText("INFERRED")).toBeTruthy();
  });

  it("submits verification requests and refreshes", async () => {
    summaryMock.mockResolvedValue(summaryFixture());
    requestMock.mockResolvedValue({
      state: "PARTIALLY_VERIFIED",
      subject_masked: "+234******67",
      limitations: ["allocation range only"],
    });
    render(<TelecomSection />);
    fireEvent.click(screen.getByRole("button", { expanded: false }));
    await screen.findByText("mtn-ng");
    fireEvent.click(screen.getByRole("button", { name: /request/i }));
    fireEvent.change(screen.getByPlaceholderText(/234803/i), {
      target: { value: "+2348031234567" },
    });
    fireEvent.change(screen.getByPlaceholderText(/fraud-investigation/i), {
      target: { value: "fraud-investigation-case-9" },
    });
    fireEvent.click(screen.getByRole("button", { name: /^verify$/i }));
    await waitFor(() => expect(requestMock).toHaveBeenCalledTimes(1));
    expect(requestMock.mock.calls[0][0]).toMatchObject({
      verify_type: "carrier_identification",
      e164: "+2348031234567",
      purpose: "fraud-investigation-case-9",
    });
  });
});
