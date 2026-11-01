import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { GraphEdge, GraphNode } from "../lib/api";
import { OrbitalExplorer } from "./orbital-explorer";

const NODES: GraphNode[] = [
  {
    node_id: "acct_A",
    node_type: "account",
    display_label: "Account A",
    synthetic_flag: true,
    source_record_ids: ["seed:scn_primary:acct_A"],
  },
  {
    node_id: "acct_B",
    node_type: "account",
    display_label: "Account B",
    synthetic_flag: true,
    source_record_ids: ["seed:scn_primary:acct_B"],
  },
  {
    node_id: "dev_04",
    node_type: "device",
    display_label: "Device 04",
    synthetic_flag: true,
    source_record_ids: ["seed:scn_primary:dev_04"],
  },
];

const EDGES: GraphEdge[] = [
  {
    edge_id: "edge_0001",
    source_node_id: "acct_A",
    target_node_id: "acct_B",
    relationship_type: "SENT_TO",
    source_event_ids: ["evt_demo_84721"],
    evidence_ids: ["evidence_edge_0001"],
    valid_from: "2026-10-27T10:00:00Z",
    valid_to: null,
    synthetic_flag: true,
    trace_id: "trace_demo_84721",
  },
  {
    edge_id: "edge_0002",
    source_node_id: "acct_B",
    target_node_id: "dev_04",
    relationship_type: "USES_DEVICE",
    source_event_ids: ["evt_demo_84721"],
    evidence_ids: ["evidence_edge_0002"],
    valid_from: "2026-10-27T10:00:00Z",
    valid_to: null,
    synthetic_flag: true,
    trace_id: "trace_demo_84721",
  },
];

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("OrbitalExplorer", () => {
  it("renders all nodes and edges around the deterministic focus", () => {
    const { container } = render(
      <OrbitalExplorer nodes={NODES} edges={EDGES} />
    );
    // acct_B has the highest degree, so it is the initial focus.
    expect(screen.getByTestId("orbital-counts")).toHaveTextContent(
      "Focus: Account B"
    );
    expect(screen.getByTestId("orbital-counts")).toHaveTextContent(
      "Showing 3 of 3 nodes, 2 of 2 edges."
    );
    expect(container.querySelectorAll("[data-node]")).toHaveLength(3);
    expect(container.querySelectorAll("[data-edge]")).toHaveLength(2);
  });

  it("shows node provenance and pins a new focus", () => {
    const { container } = render(
      <OrbitalExplorer nodes={NODES} edges={EDGES} />
    );
    fireEvent.click(container.querySelector('[data-node="dev_04"]') as Element);
    const detail = screen.getByTestId("orbital-detail");
    expect(detail).toHaveTextContent("Device 04");
    expect(detail).toHaveTextContent("seed:scn_primary:dev_04");
    expect(detail).toHaveTextContent("edge_0002");
    fireEvent.click(screen.getByRole("button", { name: "Pin as orbit focus" }));
    expect(screen.getByTestId("orbital-counts")).toHaveTextContent(
      "Focus: Device 04"
    );
    fireEvent.click(screen.getByRole("button", { name: "Unpin focus" }));
    expect(screen.getByTestId("orbital-counts")).toHaveTextContent(
      "Focus: Account B"
    );
  });

  it("shows edge provenance and evidence on selection", () => {
    const { container } = render(
      <OrbitalExplorer nodes={NODES} edges={EDGES} />
    );
    fireEvent.click(container.querySelector('[data-edge="edge_0002"]') as Element);
    const detail = screen.getByTestId("orbital-detail");
    expect(detail).toHaveTextContent("USES_DEVICE");
    expect(detail).toHaveTextContent("evt_demo_84721");
    expect(detail).toHaveTextContent("evidence_edge_0002");
  });

  it("filters hide nodes and edges, and labels can hide", () => {
    const { container } = render(
      <OrbitalExplorer nodes={NODES} edges={EDGES} />
    );
    fireEvent.click(screen.getByLabelText("device"));
    expect(screen.getByTestId("orbital-counts")).toHaveTextContent(
      "Showing 2 of 3 nodes, 1 of 2 edges."
    );
    fireEvent.click(screen.getByRole("button", { name: "Hide labels" }));
    expect(container.querySelectorAll("text")).toHaveLength(0);
    fireEvent.click(screen.getByRole("button", { name: "Show labels" }));
    expect(container.querySelectorAll("text").length).toBeGreaterThan(0);
  });

  it("reports dangling edges instead of hiding them", () => {
    const bad: GraphEdge = {
      ...EDGES[0],
      edge_id: "edge_bad",
      target_node_id: "ghost",
    };
    render(<OrbitalExplorer nodes={NODES} edges={[...EDGES, bad]} />);
    expect(screen.getByTestId("orbital-counts")).toHaveTextContent(
      "1 edge(s) hidden: endpoint unknown (edge_bad)."
    );
  });

  it("pause control toggles the animation state", () => {
    render(<OrbitalExplorer nodes={NODES} edges={EDGES} />);
    const pause = screen.getByRole("button", { name: "Pause animation" });
    fireEvent.click(pause);
    expect(
      screen.getByRole("button", { name: "Play animation" })
    ).toBeTruthy();
  });

  it("starts paused when reduced motion is requested", () => {
    // stubGlobal (removed by unstubAllGlobals): defineProperty + global
    // restore leaves a neutered mock that returns undefined.
    vi.stubGlobal(
      "matchMedia",
      vi.fn().mockImplementation((query: string) => ({
        matches: query === "(prefers-reduced-motion: reduce)",
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      }))
    );
    render(<OrbitalExplorer nodes={NODES} edges={EDGES} />);
    expect(
      screen.getByRole("button", { name: "Play animation" })
    ).toBeTruthy();
  });

  it("zoom controls change the viewport transform", () => {
    render(<OrbitalExplorer nodes={NODES} edges={EDGES} />);
    const viewport = screen.getByTestId("orbital-viewport");
    fireEvent.click(screen.getByRole("button", { name: "Zoom in" }));
    expect(viewport.getAttribute("transform")).toBe(
      "translate(0,0) scale(1.25)"
    );
    fireEvent.click(screen.getByRole("button", { name: "Reset view" }));
    expect(viewport.getAttribute("transform")).toBe(
      "translate(0,0) scale(1)"
    );
  });
});
