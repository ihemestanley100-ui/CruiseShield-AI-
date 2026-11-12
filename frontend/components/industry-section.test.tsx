import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { IndustrySection } from "./industry-section";

const { listMock, coverageMock, readinessMock } = vi.hoisted(() => ({
  listMock: vi.fn(),
  coverageMock: vi.fn(),
  readinessMock: vi.fn(),
}));

vi.mock("../lib/api", async (importOriginal) => ({
  ...((await importOriginal()) as object),
  getIndustries: listMock,
  getIndustryCoverage: coverageMock,
  getIndustryReadiness: readinessMock,
}));

beforeEach(() => {
  listMock.mockReset();
  coverageMock.mockReset();
  readinessMock.mockReset();
});

describe("IndustrySection", () => {
  it("stays closed until expanded, then lists registry statuses", async () => {
    listMock.mockResolvedValue({
      industries: [
        { id: "banking", name: "Banking", status: "NOT_STARTED" },
        { id: "retail", name: "Retail", status: "NOT_STARTED" },
      ],
      count: 2,
    });
    render(<IndustrySection />);
    expect(listMock).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Show industries" }));
    await waitFor(() => expect(listMock).toHaveBeenCalled());
    expect(await screen.findByText("2 registered industries.")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Banking" })).toBeTruthy();
  });

  it("shows coverage and NOT_READY readiness verbatim", async () => {
    listMock.mockResolvedValue({
      industries: [{ id: "banking", name: "Banking", status: "NOT_STARTED" }],
      count: 1,
    });
    coverageMock.mockResolvedValue({
      industry_id: "banking",
      name: "Banking",
      registry_status: "NOT_STARTED",
      risk_taxonomy_codes: ["BNK-VEL"],
      threat_scenarios: 2,
      typologies: ["T-01"],
      test_file: "tests/test_industry_banking.py",
      test_present: true,
    });
    readinessMock.mockResolvedValue({
      industry_id: "banking",
      registry_status: "NOT_STARTED",
      checks: {
        profile_present: true,
        tests_present: true,
        typologies_mapped: true,
        typologies_measured: false,
        status_gate: false,
      },
      typologies_measured: 0,
      overall: "NOT_READY",
      note: "evidence only",
    });
    render(<IndustrySection />);
    fireEvent.click(screen.getByRole("button", { name: "Show industries" }));
    fireEvent.click(await screen.findByRole("button", { name: "Banking" }));
    expect(await screen.findByText("NOT_READY")).toBeTruthy();
    expect(screen.getByText(/status_gate: no/)).toBeTruthy();
  });

  it("surfaces industry load errors", async () => {
    listMock.mockRejectedValue(new Error("down"));
    render(<IndustrySection />);
    fireEvent.click(screen.getByRole("button", { name: "Show industries" }));
    expect(await screen.findByRole("alert")).toBeTruthy();
  });
});
