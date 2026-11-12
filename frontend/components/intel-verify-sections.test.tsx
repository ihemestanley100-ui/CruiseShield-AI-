import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  AddressSection,
  IdentitySection,
} from "./intel-verify-sections";

const { identityMock, addressMock } = vi.hoisted(() => ({
  identityMock: vi.fn(),
  addressMock: vi.fn(),
}));

vi.mock("../lib/api", async (importOriginal) => ({
  ...((await importOriginal()) as object),
  requestIdentityVerification: identityMock,
  requestAddressVerification: addressMock,
}));

beforeEach(() => {
  identityMock.mockReset();
  addressMock.mockReset();
});

describe("IdentitySection", () => {
  it("submits and renders verbatim states with factors", async () => {
    identityMock.mockResolvedValue({
      verification_status: "UNAVAILABLE",
      subject_masked: "ID******01",
      factors: [],
      missing: ["authorized passport provider"],
      limitations: ["no live connection"],
      verification_id: "idv_000001",
    });
    render(<IdentitySection investigationId="inv_84721" />);
    fireEvent.click(screen.getByRole("button", { name: /verify/i }));
    fireEvent.change(screen.getByPlaceholderText(/subject reference/i), {
      target: { value: "ID-1" },
    });
    fireEvent.click(screen.getByRole("button", { name: /^submit$/i }));
    await waitFor(() => expect(identityMock).toHaveBeenCalledTimes(1));
    expect(await screen.findByText("UNAVAILABLE")).toBeTruthy();
    expect(screen.getByText(/no live connection/)).toBeTruthy();
  });

  it("shows error on failure", async () => {
    identityMock.mockRejectedValueOnce(new Error("denied"));
    render(<IdentitySection />);
    fireEvent.click(screen.getByRole("button", { name: /verify/i }));
    fireEvent.click(screen.getByRole("button", { name: /^submit$/i }));
    expect(await screen.findByRole("alert")).toBeTruthy();
  });
});

describe("AddressSection", () => {
  it("submits and renders masked address", async () => {
    addressMock.mockResolvedValue({
      verification_status: "UNVERIFIED",
      subject_masked: "CU******01",
      address_masked: {
        country: "NG",
        city: "Lagos",
        street_masked: "5 ****",
      },
      limitations: ["geocoding only"],
      verification_id: "adr_000001",
    });
    render(<AddressSection investigationId="inv_84721" />);
    fireEvent.click(screen.getByRole("button", { name: /verify/i }));
    fireEvent.click(screen.getByRole("button", { name: /^submit$/i }));
    await waitFor(() => expect(addressMock).toHaveBeenCalledTimes(1));
    expect(await screen.findByText("UNVERIFIED")).toBeTruthy();
    expect(screen.getByText(/Lagos/)).toBeTruthy();
  });
});
