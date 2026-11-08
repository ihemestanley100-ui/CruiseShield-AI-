import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { IntelMap } from "../lib/api";
import { GeointelMap } from "./geointel-map";

const { mapMock } = vi.hoisted(() => ({ mapMock: vi.fn() }));

vi.mock("../lib/api", async (importOriginal) => ({
  ...((await importOriginal()) as object),
  getInvestigationMap: mapMock,
}));

beforeEach(() => {
  mapMock.mockReset();
});

function mapFixture(): IntelMap {
  return {
    investigation_id: "inv_84721",
    layers: {
      verified_addresses: {
        items: [
          {
            verification_id: "adr_000001",
            kind: "VERIFIED_ADDRESS",
            status: "VERIFIED",
            coordinates: { latitude: 6.5, longitude: 3.4 },
            masked: false,
          },
        ],
        item_count: 1,
        reason_if_empty: "",
      },
      ip_estimates: {
        items: [
          {
            observation_id: "net_000001",
            kind: "IP_ESTIMATE",
            status: "ESTIMATED",
            masked: true,
          },
        ],
        item_count: 1,
        reason_if_empty: "",
      },
    },
    masked: false,
    map_provider_note: "provider-neutral",
  };
}

describe("GeointelMap", () => {
  it("stays closed until expanded, then renders markers", async () => {
    mapMock.mockResolvedValue(mapFixture());
    render(<GeointelMap investigationId="inv_84721" />);
    expect(mapMock).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { expanded: false }));
    await waitFor(() => expect(mapMock).toHaveBeenCalledTimes(1));
    expect(await screen.findByLabelText("Evidence markers schematic"))
      .toBeTruthy();
    // Markers are role=button without aria-expanded; match by status name.
    expect(
      screen.getAllByRole("button", { name: /VERIFIED|ESTIMATED/ }).length
    ).toBeGreaterThan(0);
  });

  it("uses distinct shapes per evidence class", async () => {
    mapMock.mockResolvedValue(mapFixture());
    render(<GeointelMap investigationId="inv_84721" />);
    fireEvent.click(screen.getByRole("button", { expanded: false }));
    await screen.findByLabelText("Evidence markers schematic");
    expect(document.querySelector("rect")).toBeTruthy();
    expect(document.querySelector("circle")).toBeTruthy();
  });

  it("marker click shows provenance detail", async () => {
    mapMock.mockResolvedValue(mapFixture());
    render(<GeointelMap investigationId="inv_84721" />);
    fireEvent.click(screen.getByRole("button", { expanded: false }));
    await screen.findByLabelText("Evidence markers schematic");
    fireEvent.click(screen.getByLabelText(/VERIFIED_ADDRESS VERIFIED/));
    expect(screen.getByText("adr_000001")).toBeTruthy();
  });

  it("layer toggle hides markers", async () => {
    mapMock.mockResolvedValue(mapFixture());
    render(<GeointelMap investigationId="inv_84721" />);
    fireEvent.click(screen.getByRole("button", { expanded: false }));
    await screen.findByLabelText("Evidence markers schematic");
    const boxes = screen.getAllByRole("checkbox");
    expect(boxes.length).toBe(2);
    boxes.forEach((box) => fireEvent.click(box));
    expect(screen.getByText(/none/i)).toBeTruthy();
  });

  it("shows error with retry on failure", async () => {
    mapMock.mockRejectedValueOnce(new Error("down"));
    mapMock.mockResolvedValue(mapFixture());
    render(<GeointelMap investigationId="inv_84721" />);
    fireEvent.click(screen.getByRole("button", { expanded: false }));
    expect(await screen.findByRole("alert")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /retry/i }));
    await waitFor(() => expect(mapMock).toHaveBeenCalledTimes(2));
  });
});
