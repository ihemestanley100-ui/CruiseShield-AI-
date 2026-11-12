import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Conversation, OrchestratedTurn } from "../lib/api";
import { AssistantShell } from "./assistant-shell";

const { openMock, getMock, sendMock } = vi.hoisted(() => ({
  openMock: vi.fn(),
  getMock: vi.fn(),
  sendMock: vi.fn(),
}));

vi.mock("../lib/api", async (importOriginal) => ({
  ...((await importOriginal()) as object),
  postConversation: openMock,
  getConversation: getMock,
  postConversationMessage: sendMock,
}));

beforeEach(() => {
  openMock.mockReset();
  getMock.mockReset();
  sendMock.mockReset();
});

function convFixture(messages: Conversation["messages"] = []): Conversation {
  return {
    conversation_id: "conv_1",
    tenant_id: "org_primary",
    owner: "judge",
    context: { investigation_id: "inv_1" },
    messages,
    created_at: "2026-11-07T10:00:00Z",
    expires_at: "2027-02-05T10:00:00Z",
  };
}

function turnFixture(): OrchestratedTurn {
  return {
    user_message: {
      role: "user",
      text: "monitoring status",
      at: "2026-11-07T10:00:00Z",
    },
    assistant_message: {
      role: "assistant",
      text: "state=COMPLETED intent=MONITORING",
      at: "2026-11-07T10:00:01Z",
    },
    execution: {
      execution_id: "exec_1",
      state: "COMPLETED",
      steps: [{ tool: "monitoring.status", status: "OK" }],
      error: "",
    },
  };
}

describe("AssistantShell", () => {
  it("stays closed until opened, then creates a conversation", async () => {
    openMock.mockResolvedValue(convFixture());
    render(
      <AssistantShell
        title="Investigation copilot"
        context={{ investigation_id: "inv_1" }}
      />
    );
    expect(openMock).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Open assistant" }));
    await waitFor(() =>
      expect(openMock).toHaveBeenCalledWith({ investigation_id: "inv_1" })
    );
  });

  it("sends turns and renders the execution summary", async () => {
    openMock.mockResolvedValue(convFixture());
    const turn = turnFixture();
    sendMock.mockResolvedValue(turn);
    getMock.mockResolvedValue(
      convFixture([turn.user_message, turn.assistant_message])
    );
    render(<AssistantShell title="Copilot" context={{}} />);
    fireEvent.click(screen.getByRole("button", { name: "Open assistant" }));
    const input = await screen.findByRole("textbox");
    fireEvent.change(input, { target: { value: "monitoring status" } });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));
    await waitFor(() => expect(sendMock).toHaveBeenCalledWith(
      "conv_1",
      "monitoring status"
    ));
    expect(
      await screen.findByText("state=COMPLETED intent=MONITORING")
    ).toBeTruthy();
  });

  it("surfaces open failures", async () => {
    openMock.mockRejectedValue(new Error("down"));
    render(<AssistantShell title="Copilot" context={{}} />);
    fireEvent.click(screen.getByRole("button", { name: "Open assistant" }));
    expect(await screen.findByRole("alert")).toBeTruthy();
  });
});
