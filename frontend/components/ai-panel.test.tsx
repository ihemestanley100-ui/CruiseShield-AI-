import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";
import { ApiError } from "../lib/api";
import type { AgentRun } from "../lib/api";
import { AiPanel } from "./ai-panel";

const { postAiAnalysisMock, postAiFollowupMock } = vi.hoisted(() => ({
  postAiAnalysisMock: vi.fn(),
  postAiFollowupMock: vi.fn(),
}));

vi.mock("../lib/api", async (importOriginal) => ({
  ...((await importOriginal()) as object),
  postAiAnalysis: postAiAnalysisMock,
  postAiFollowup: postAiFollowupMock,
}));

function runFixture(): AgentRun {
  return {
    agent_run_id: "agentrun_9",
    model_id: "muse-spark-1.3",
    prompt_version: "cs-prompt-v2",
    request_id: "req_9",
    latency_ms: 1200,
    status: "SUCCEEDED",
    schema_validation_status: "VALIDATED",
    evidence_reference_validation_status: "VALIDATED",
    error_code: "",
    result: {
      summary: "Seeded network shows shared infrastructure.",
      key_findings: [
        {
          finding: "Device sharing observed.",
          evidence_ids: ["evidence_rr_R-003_84721"],
          confidence_label: "high",
          caveat: "Demo data.",
        },
      ],
      alternative_explanations: ["Shared household device."],
      missing_information: ["None for demo."],
      conclusion: "requires_review",
      disclaimer: "Advisory only.",
    },
  };
}

beforeEach(() => {
  postAiAnalysisMock.mockReset();
  postAiFollowupMock.mockReset();
});

afterEach(() => {
  vi.useRealTimers();
});

describe("AiPanel", () => {
  it("runs analysis and renders findings with provenance", async () => {
    postAiAnalysisMock.mockResolvedValue(runFixture());
    render(<AiPanel invId="inv_84721" />);
    fireEvent.click(screen.getByRole("button", { name: "Run AI analysis" }));
    expect(screen.getByText("Calling model…")).toBeTruthy();
    await waitFor(() => {
      expect(screen.getByText(/shared infrastructure/)).toBeTruthy();
    });
    expect(screen.getByText("Device sharing observed.")).toBeTruthy();
    expect(screen.getByText(/muse-spark-1.3/)).toBeTruthy();
    expect(screen.getByText(/agentrun_9/)).toBeTruthy();
  });

  it("renders missing information and alternative explanations", async () => {
    postAiAnalysisMock.mockResolvedValue(runFixture());
    render(<AiPanel invId="inv_84721" />);
    fireEvent.click(screen.getByRole("button", { name: "Run AI analysis" }));
    await waitFor(() => {
      expect(screen.getByText("Missing information:")).toBeTruthy();
    });
    expect(screen.getByText("None for demo.")).toBeTruthy();
    expect(screen.getByText("Alternative explanations:")).toBeTruthy();
    expect(screen.getByText("Shared household device.")).toBeTruthy();
  });

  it("omits the uncertainty sections when the model sends none", async () => {
    postAiAnalysisMock.mockResolvedValue({
      ...runFixture(),
      result: {
        ...runFixture().result,
        missing_information: [],
        alternative_explanations: [],
      },
    });
    render(<AiPanel invId="inv_84721" />);
    fireEvent.click(screen.getByRole("button", { name: "Run AI analysis" }));
    await waitFor(() => {
      expect(screen.getByText(/shared infrastructure/)).toBeTruthy();
    });
    expect(screen.queryByText("Missing information:")).toBeNull();
    expect(screen.queryByText("Alternative explanations:")).toBeNull();
  });

  it("shows an honest error and retries", async () => {
    postAiAnalysisMock.mockRejectedValue(
      new ApiError("MODEL_TIMEOUT", "timed out", 503, "")
    );
    render(<AiPanel invId="inv_84721" />);
    fireEvent.click(screen.getByRole("button", { name: "Run AI analysis" }));
    await waitFor(() => {
      expect(screen.getByText(/MODEL_TIMEOUT/)).toBeTruthy();
    });
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(postAiAnalysisMock).toHaveBeenCalledTimes(2);
  });

  it("shows invalid model output as an error without findings", async () => {
    postAiAnalysisMock.mockRejectedValue(
      new ApiError("MODEL_OUTPUT_INVALID", "missing critical fields", 503, "")
    );
    render(<AiPanel invId="inv_84721" />);
    fireEvent.click(screen.getByRole("button", { name: "Run AI analysis" }));
    await waitFor(() => {
      expect(screen.getByText(/MODEL_OUTPUT_INVALID/)).toBeTruthy();
    });
    expect(screen.queryByText("Calling model…")).toBeNull();
  });

  it("asks a follow-up and renders the validated answer", async () => {
    postAiAnalysisMock.mockResolvedValue(runFixture());
    postAiFollowupMock.mockResolvedValue({
      ...runFixture(),
      agent_run_id: "agentrun_10",
      prompt_version: "cs-prompt-v2-followup",
      result: {
        ...runFixture().result,
        summary: "dev_04 is shared by three accounts.",
      },
    });
    render(<AiPanel invId="inv_84721" />);
    fireEvent.click(screen.getByRole("button", { name: "Run AI analysis" }));
    await waitFor(() => {
      expect(screen.getByLabelText(/follow-up/)).toBeTruthy();
    });
    fireEvent.change(screen.getByLabelText(/follow-up/), {
      target: { value: "Why is dev_04 shared?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Ask follow-up" }));
    await waitFor(() => {
      expect(
        screen.getByText("dev_04 is shared by three accounts.")
      ).toBeTruthy();
    });
    expect(postAiFollowupMock).toHaveBeenCalledWith(
      "inv_84721",
      "Why is dev_04 shared?"
    );
    expect(screen.getByText(/agentrun_10/)).toBeTruthy();
  });

  it("blocks empty follow-ups and shows follow-up errors", async () => {
    postAiAnalysisMock.mockResolvedValue(runFixture());
    postAiFollowupMock.mockRejectedValue(
      new ApiError("MODEL_TIMEOUT", "timed out", 503, "")
    );
    render(<AiPanel invId="inv_84721" />);
    fireEvent.click(screen.getByRole("button", { name: "Run AI analysis" }));
    await waitFor(() => {
      expect(screen.getByLabelText(/follow-up/)).toBeTruthy();
    });
    expect(
      screen.getByRole("button", { name: "Ask follow-up" })
    ).toHaveProperty("disabled", true);
    fireEvent.change(screen.getByLabelText(/follow-up/), {
      target: { value: "Why?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Ask follow-up" }));
    await waitFor(() => {
      expect(screen.getByText("MODEL_TIMEOUT: timed out")).toBeTruthy();
    });
    // The original validated analysis is untouched by the failed follow-up.
    expect(screen.getByText(/shared infrastructure/)).toBeTruthy();
  });

  it("times out a hung request and recovers", async () => {
    vi.useFakeTimers();
    try {
      postAiAnalysisMock.mockImplementation(
        (_id: string, signal?: AbortSignal) =>
          new Promise<never>((_resolve, reject) => {
            signal?.addEventListener("abort", () =>
              reject(new DOMException("Aborted", "AbortError"))
            );
          })
      );
      render(<AiPanel invId="inv_84721" />);
      fireEvent.click(screen.getByRole("button", { name: "Run AI analysis" }));
      await act(async () => {
        vi.advanceTimersByTime(36000);
      });
      expect(screen.getByText(/timed out or was cancelled/)).toBeTruthy();
      expect(
        screen.getByRole("button", { name: "Retry" })
      ).toBeTruthy();
    } finally {
      vi.useRealTimers();
    }
  });
});
