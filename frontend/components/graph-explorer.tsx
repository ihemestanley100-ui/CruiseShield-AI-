"use client";

/* Batch 3: deterministic 2D SVG network explorer. Renders exactly the
 * nodes/edges fetched from GET /api/v1/graph/{txn}; filters only hide,
 * never invent or alter data. No animation, so reduced-motion needs no
 * special handling. */

import { useMemo, useRef, useState } from "react";
import type { GraphEdge, GraphNode } from "../lib/api";
import { defaultRoots, layoutGraph } from "../lib/graph-layout";

interface Props {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

type Selection =
  | { kind: "node"; id: string }
  | { kind: "edge"; id: string }
  | null;

const PAN_STEP = 40;

export function GraphExplorer({ nodes, edges }: Props) {
  const nodeTypes = useMemo(
    () => [...new Set(nodes.map((n) => n.node_type))].sort(),
    [nodes]
  );
  const relTypes = useMemo(
    () => [...new Set(edges.map((e) => e.relationship_type))].sort(),
    [edges]
  );
  const [activeTypes, setActiveTypes] = useState<Set<string> | null>(null);
  const [activeRels, setActiveRels] = useState<Set<string> | null>(null);
  const [selection, setSelection] = useState<Selection>(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const drag = useRef<{ x: number; y: number } | null>(null);

  const types = activeTypes ?? new Set(nodeTypes);
  const rels = activeRels ?? new Set(relTypes);

  const pos = useMemo(
    () => layoutGraph(nodes, edges, defaultRoots(edges)),
    [nodes, edges]
  );
  const byId = useMemo(
    () => new Map(nodes.map((n) => [n.node_id, n])),
    [nodes]
  );
  const visibleNodes = nodes.filter((n) => types.has(n.node_type));
  const visibleIds = new Set(visibleNodes.map((n) => n.node_id));
  const visibleEdges = edges.filter(
    (e) =>
      rels.has(e.relationship_type) &&
      visibleIds.has(e.source_node_id) &&
      visibleIds.has(e.target_node_id)
  );
  const maxX = Math.max(400, ...[...pos.values()].map((p) => p.x)) + 120;
  const maxY = Math.max(200, ...[...pos.values()].map((p) => p.y)) + 60;

  function toggle(setter: (v: Set<string> | null) => void, current: Set<string>, v: string) {
    const next = new Set(current);
    if (next.has(v)) next.delete(v);
    else next.add(v);
    setter(next);
  }

  const selectedNode =
    selection?.kind === "node" ? byId.get(selection.id) : undefined;
  const selectedEdge =
    selection?.kind === "edge"
      ? edges.find((e) => e.edge_id === selection.id)
      : undefined;
  const selectedNodeRels = selectedNode
    ? edges.filter(
        (e) =>
          e.source_node_id === selectedNode.node_id ||
          e.target_node_id === selectedNode.node_id
      )
    : [];

  return (
    <section className="card" aria-label="Network graph">
      <h2>Network graph</h2>
      <p className="muted" aria-live="polite" data-testid="graph-counts">
        Showing {visibleNodes.length} of {nodes.length} nodes,{" "}
        {visibleEdges.length} of {edges.length} edges.
      </p>
      <div className="chip-row" role="group" aria-label="Entity type filters">
        {nodeTypes.map((t) => (
          <label key={t} className="chip-label">
            <input
              type="checkbox"
              checked={types.has(t)}
              onChange={() => toggle(setActiveTypes, types, t)}
            />{" "}
            {t}
          </label>
        ))}
      </div>
      <div className="chip-row" role="group" aria-label="Relationship filters">
        {relTypes.map((r) => (
          <label key={r} className="chip-label">
            <input
              type="checkbox"
              checked={rels.has(r)}
              onChange={() => toggle(setActiveRels, rels, r)}
            />{" "}
            {r}
          </label>
        ))}
      </div>
      <div className="chip-row" role="group" aria-label="Graph view controls">
        <button
          type="button"
          className="chip"
          onClick={() => setZoom((z) => Math.min(3, +(z + 0.25).toFixed(2)))}
        >
          Zoom in
        </button>
        <button
          type="button"
          className="chip"
          onClick={() => setZoom((z) => Math.max(0.25, +(z - 0.25).toFixed(2)))}
        >
          Zoom out
        </button>
        <button
          type="button"
          className="chip"
          onClick={() => {
            setZoom(1);
            setPan({ x: 0, y: 0 });
          }}
        >
          Fit to screen
        </button>
      </div>
      <svg
        viewBox={`0 0 ${maxX} ${maxY}`}
        role="img"
        aria-label={`Network graph: ${visibleNodes.length} nodes, ${visibleEdges.length} edges. Use Tab to reach nodes and edges, Enter to select, arrow keys on the graph to pan.`}
        tabIndex={0}
        data-testid="graph-svg"
        className="graph-canvas"
        onKeyDown={(ev) => {
          if (ev.key === "ArrowLeft") setPan((p) => ({ ...p, x: p.x + PAN_STEP }));
          else if (ev.key === "ArrowRight")
            setPan((p) => ({ ...p, x: p.x - PAN_STEP }));
          else if (ev.key === "ArrowUp") setPan((p) => ({ ...p, y: p.y + PAN_STEP }));
          else if (ev.key === "ArrowDown")
            setPan((p) => ({ ...p, y: p.y - PAN_STEP }));
          else return;
          ev.preventDefault();
        }}
        onPointerDown={(ev) => {
          drag.current = { x: ev.clientX, y: ev.clientY };
          (ev.target as Element).setPointerCapture?.(ev.pointerId);
        }}
        onPointerMove={(ev) => {
          if (!drag.current) return;
          const dx = ev.clientX - drag.current.x;
          const dy = ev.clientY - drag.current.y;
          drag.current = { x: ev.clientX, y: ev.clientY };
          setPan((p) => ({ x: p.x + dx, y: p.y + dy }));
        }}
        onPointerUp={() => {
          drag.current = null;
        }}
      >
        <g
          transform={`translate(${pan.x},${pan.y}) scale(${zoom})`}
          data-testid="graph-viewport"
        >
          {visibleEdges.map((e) => {
            const a = pos.get(e.source_node_id);
            const b = pos.get(e.target_node_id);
            if (!a || !b) return null;
            const selected =
              selection?.kind === "edge" && selection.id === e.edge_id;
            return (
              <g
                key={e.edge_id}
                tabIndex={0}
                role="button"
                aria-label={`Edge ${e.edge_id}: ${e.source_node_id} ${e.relationship_type} ${e.target_node_id}`}
                data-edge={e.edge_id}
                className="graph-edge"
                onClick={() => setSelection({ kind: "edge", id: e.edge_id })}
                onKeyDown={(ev) => {
                  if (ev.key === "Enter" || ev.key === " ") {
                    ev.preventDefault();
                    setSelection({ kind: "edge", id: e.edge_id });
                  }
                }}
              >
                <line
                  x1={a.x}
                  y1={a.y}
                  x2={b.x}
                  y2={b.y}
                  strokeWidth={selected ? 4 : 2}
                >
                  <title>{`${e.edge_id}: ${e.relationship_type}`}</title>
                </line>
              </g>
            );
          })}
          {visibleNodes.map((n) => {
            const p = pos.get(n.node_id);
            if (!p) return null;
            const selected =
              selection?.kind === "node" && selection.id === n.node_id;
            return (
              <g
                key={n.node_id}
                tabIndex={0}
                role="button"
                aria-label={`${n.display_label} (${n.node_type})`}
                data-node={n.node_id}
                className="graph-node"
                onClick={() => setSelection({ kind: "node", id: n.node_id })}
                onKeyDown={(ev) => {
                  if (ev.key === "Enter" || ev.key === " ") {
                    ev.preventDefault();
                    setSelection({ kind: "node", id: n.node_id });
                  }
                }}
              >
                <circle
                  cx={p.x}
                  cy={p.y}
                  r={selected ? 19 : 16}
                  className={`graph-dot graph-${n.node_type}`}
                />
                <text x={p.x + 22} y={p.y + 5} className="graph-label">
                  {n.display_label}
                </text>
              </g>
            );
          })}
        </g>
      </svg>
      <div aria-live="polite" data-testid="graph-detail">
        {selectedNode && (
          <div className="alert ok">
            <strong>{selectedNode.display_label}</strong> (
            {selectedNode.node_type})<br />
            Source:{" "}
            <code>{selectedNode.source_record_ids.join(", ")}</code>
            <br />
            {selectedNodeRels.length} relationship(s):{" "}
            {selectedNodeRels.map((e) => (
              <span key={e.edge_id}>
                <code>{e.edge_id}</code> {e.relationship_type}{" "}
              </span>
            ))}
          </div>
        )}
        {selectedEdge && (
          <div className="alert ok">
            <strong>{selectedEdge.edge_id}</strong>:{" "}
            {selectedEdge.source_node_id} {selectedEdge.relationship_type}{" "}
            {selectedEdge.target_node_id}
            <br />
            Provenance:{" "}
            <code>{selectedEdge.source_event_ids.join(", ")}</code> · Evidence:{" "}
            <code>{selectedEdge.evidence_ids.join(", ")}</code>
            <br />
            Valid: {selectedEdge.valid_from} →{" "}
            {selectedEdge.valid_to ?? "present"} · Trace:{" "}
            <code>{selectedEdge.trace_id}</code>
          </div>
        )}
        {!selectedNode && !selectedEdge && (
          <p className="muted">Select a node or edge for details.</p>
        )}
      </div>
    </section>
  );
}
