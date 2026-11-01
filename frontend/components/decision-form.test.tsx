import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../lib/api";
import { DecisionForm } from "./decision-form";

const { postDecisionMock } = vi.hoisted(() => ({ postDecisionMock: vi.fn() }));

vi.mock("../lib/api", async (importOriginal) => ({
  ...((await importOriginal()) as object),
  postDecision: postDecisionMock,
}));

function decisionFixture() {
  return {
    decision: {
      decision_id: "decision_0002",
      case_id: "case_84721",
      actor_id: "investigator",
      actor_role: "INVESTIGATOR",
      decision: "Escalate",
      reason: "Network review.",
      evidence_viewed: [],
      recommendation_at_decision: "",
      created_at: "2026-10-29T00:00:00Z",
      authorization_scope: "demo",
      trace_id: "t",
    },
    audit: {
      audit_event_id: "audit_0007",
      actor_type: "human",
      actor_id: "investigator",
      action: "case.decision",
      target_type: "case",
      target_id: "case_84721",
      previous_state_reference: "TRIAGED",
      new_state_reference: "INVESTIGATING",
      reason: "Escalate: Network review.",
      timestamp: "2026-10-29T00:00:00Z",
      trace_id: "t",
      request_id: "t",
    },
    case: {
      case_id: "case_84721",
      investigation_id: "inv_84721",
      status: "INVESTIGATING",
      created_at: "2026-10-28T00:00:00Z",
      updated_at: "2026-10-29T00:00:00Z",
      trace_id: "t",
    },
  };
}

beforeEach(() => {
  postDecisionMock.mockReset();
});

describe("DecisionForm", () => {
  it("preselects no decision and blocks submit until one is chosen", () => {
    render(
      <DecisionForm
        caseId="case_84721"
        allowedTransitions={["INVESTIGATING"]}
        onDecided={() => {}}
      />
    );
    expect(
      (screen.getByLabelText("Decision") as HTMLSelectElement).value
    ).toBe("");
    fireEvent.change(screen.getByLabelText(/Reason/), {
      target: { value: "Has reason, no decision." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Record decision" }));
    expect(screen.getByText(/select a decision/i)).toBeTruthy();
    expect(postDecisionMock).not.toHaveBeenCalled();
  });

  it("refuses to submit without a reason", () => {
    render(
      <DecisionForm
        caseId="case_84721"
        allowedTransitions={["INVESTIGATING"]}
        onDecided={() => {}}
      />
    );
    fireEvent.change(screen.getByLabelText("Decision"), {
      target: { value: "Escalate" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Record decision" }));
    expect(screen.getByText(/reason is required/i)).toBeTruthy();
    expect(postDecisionMock).not.toHaveBeenCalled();
  });

  it("posts the decision once and reports the result", async () => {
    postDecisionMock.mockResolvedValue(decisionFixture());
    const onDecided = vi.fn();
    render(
      <DecisionForm
        caseId="case_84721"
        allowedTransitions={["INVESTIGATING", "FALSE_POSITIVE"]}
        onDecided={onDecided}
      />
    );
    fireEvent.change(screen.getByLabelText("Decision"), {
      target: { value: "Escalate" },
    });
    fireEvent.change(screen.getByLabelText("Move case to"), {
      target: { value: "INVESTIGATING" },
    });
    fireEvent.change(screen.getByLabelText(/Reason/), {
      target: { value: "Network review." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Record decision" }));
    await waitFor(() => expect(onDecided).toHaveBeenCalledTimes(1));
    expect(postDecisionMock).toHaveBeenCalledTimes(1);
    expect(postDecisionMock).toHaveBeenCalledWith("case_84721", {
      decision: "Escalate",
      target_status: "INVESTIGATING",
      reason: "Network review.",
      actor_id: "investigator",
      evidence_viewed: [],
      recommendation: "",
    });
  });

  it("shows server validation errors honestly", async () => {
    postDecisionMock.mockRejectedValue(
      new ApiError("INVALID_TRANSITION", "bad move", 400, "t")
    );
    render(
      <DecisionForm
        caseId="case_84721"
        allowedTransitions={["INVESTIGATING"]}
        onDecided={() => {}}
      />
    );
    fireEvent.change(screen.getByLabelText("Decision"), {
      target: { value: "Escalate" },
    });
    fireEvent.change(screen.getByLabelText(/Reason/), {
      target: { value: "x" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Record decision" }));
    await waitFor(() =>
      expect(screen.getByText("INVALID_TRANSITION: bad move")).toBeTruthy()
    );
  });

  it("shows a terminal-state message when no transitions exist", () => {
    render(
      <DecisionForm caseId="case_84721" allowedTransitions={[]} onDecided={() => {}} />
    );
    expect(screen.getByText(/terminal state/i)).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Record decision" })).toBeNull();
  });
});
