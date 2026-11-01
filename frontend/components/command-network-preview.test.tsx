import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { GraphEdge, GraphNode, GraphResponse } from "../lib/api";
import { CommandNetworkPreview } from "./command-network-preview";

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
  }: {
    href: string;
    children: React.ReactNode;
  }) => <a href={href}>{children}</a>,
}));

function node(node_id: string, node_type = "account"): GraphNode {
  return {
    node_id,
    node_type,
    display_label: `Label ${node_id}`,
    synthetic_flag: true,
    source_record_ids: [`seed:scn_primary:${node_id}`],
  };
}

function edge(
  edge_id: string,
  source_node_id: string,
  target_node_id: string
): GraphEdge {
  return {
    edge_id,
    source_node_id,
    target_node_id,
    relationship_type: "SENT_TO",
    source_event_ids: ["evt_demo_84721"],
    evidence_ids: [`evidence_${edge_id}`],
    valid_from: "2026-10-27T10:00:00Z",
    valid_to: null,
    synthetic_flag: true,
    trace_id: "trace_demo_84721",
  };
}

function graphFixture(): GraphResponse {
  return {
    transaction_id: "txn_84721",
    nodes: [node("acct_A"), node("acct_B"), node("dev_04", "device")],
    edges: [
      edge("edge_0001", "acct_A", "acct_B"),
      edge("edge_0002", "acct_B", "dev_04"),
    ],
    provenance_errors: [],
    counts: { nodes: 22, edges: 30 },
  };
}

describe("CommandNetworkPreview", () => {
  it("labels real totals and the preview subset honestly", () => {
    const { container } = render(
      <CommandNetworkPreview graph={graphFixture()} />
    );
    expect(screen.getByTestId("network-preview-counts").textContent).toContain(
      "22 nodes, 30 edges"
    );
    expect(screen.getByTestId("network-preview-counts").textContent).toContain(
      "Preview shows 3 nodes and 2 relationships"
    );
    const svg = container.querySelector("svg");
    expect(svg?.getAttribute("role")).toBe("img");
    expect(svg?.getAttribute("aria-label")).toContain("3 of 22 nodes");
    expect(svg?.textContent).toContain("Label acct_A");
    expect(
      screen
        .getByRole("link", { name: "Open full network explorer" })
        .getAttribute("href")
    ).toBe("/network/txn_84721");
  });

  it("surfaces provenance errors instead of hiding them", () => {
    const graph = graphFixture();
    graph.provenance_errors = ["edge_0009"];
    render(<CommandNetworkPreview graph={graph} />);
    expect(screen.getByRole("alert").textContent).toContain("edge_0009");
  });
});
