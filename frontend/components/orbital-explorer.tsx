"use client";

/* Batch B: orbital graph renderer (SVG, no new dependencies).
 *
 * VISUAL METAPHOR ONLY: ring depth, angle, node size, and rotation carry
 * NO meaning about risk, guilt, ownership, timing, causation, or
 * investigative priority. Sizes distinguish the focus node from the rest;
 * shapes + labels (never color alone) distinguish entity types. */

import { useEffect, useMemo, useRef, useState } from "react";
import type { GraphEdge, GraphNode } from "../lib/api";
import {
  adaptGraph,
  bfsDepths,
  defaultFocus,
  layoutOrbital,
  ORBIT_CX,
  ORBIT_CY,
  ORBIT_HEIGHT,
  ORBIT_WIDTH,
  RING_RADII,
} from "../lib/orbital-layout";

interface Props {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

type Selection =
  | { kind: "node"; id: string }
  | { kind: "edge"; id: string }
  | null;

const PAN_STEP = 40;
/* Radians per second at 1x: one revolution ≈ 63s — deliberately slow. */
const SPEEDS: Record<string, number> = { "0.5×": 0.05, "1×": 0.1, "2×": 0.2 };

const TYPE_COLORS: Record<string, string> = {
  account: "var(--orbit-node-white)",
  device: "var(--orbit-node-amber)",
  phone: "var(--orbit-cyan)",
  merchant: "var(--orbit-electric)",
  beneficiary: "var(--orbit-verified)",
  ip: "var(--orbit-node-sky)",
  location: "var(--orbit-node-lime)",
};

function NodeGlyph({
  type,
  x,
  y,
  r,
  focus,
}: {
  type: string;
  x: number;
  y: number;
  r: number;
  focus: boolean;
}) {
  const fill = TYPE_COLORS[type] ?? "var(--muted)";
  const common = {
    fill,
    stroke: focus ? "var(--orbit-cyan)" : "var(--orbit-deep)",
    strokeWidth: focus ? 3 : 2,
  };
  switch (type) {
    case "device":
      return <rect x={x - r} y={y - r} width={2 * r} height={2 * r} {...common} />;
    case "phone":
      return (
        <polygon
          points={`${x},${y - r} ${x + r},${y + r} ${x - r},${y + r}`}
          {...common}
        />
      );
    case "merchant":
      return (
        <polygon
          points={`${x},${y - r} ${x + r},${y} ${x},${y + r} ${x - r},${y}`}
          {...common}
        />
      );
    case "beneficiary":
      return (
        <polygon
          points={[0, 1, 2, 3, 4, 5]
            .map((i) => {
              const a = (Math.PI / 3) * i - Math.PI / 2;
              return `${x + r * Math.cos(a)},${y + r * Math.sin(a)}`;
            })
            .join(" ")}
          {...common}
        />
      );
    case "ip":
      return (
        <polygon
          points={[0, 1, 2, 3, 4]
            .map((i) => {
              const a = ((2 * Math.PI) / 5) * i - Math.PI / 2;
              return `${x + r * Math.cos(a)},${y + r * Math.sin(a)}`;
            })
            .join(" ")}
          {...common}
        />
      );
    case "location":
      return (
        <g>
          <circle cx={x} cy={y} r={r} {...common} />
          <circle cx={x} cy={y} r={r / 2.5} fill="var(--orbit-deep)" />
        </g>
      );
    default:
      return <circle cx={x} cy={y} r={r} {...common} />;
  }
}

export function OrbitalExplorer({ nodes, edges }: Props) {
  const adapted = useMemo(() => adaptGraph(nodes, edges), [nodes, edges]);
  const initialFocus = useMemo(
    () => defaultFocus(adapted.nodes, adapted.edges),
    [adapted]
  );
  const nodeTypes = useMemo(
    () => [...new Set(adapted.nodes.map((n) => n.node_type))].sort(),
    [adapted]
  );
  const relTypes = useMemo(
    () => [...new Set(adapted.edges.map((e) => e.relationship_type))].sort(),
    [adapted]
  );
  const reducedMotion = useRef(
    typeof window !== "undefined" &&
      typeof window.matchMedia === "function" &&
      (window.matchMedia("(prefers-reduced-motion: reduce)")?.matches ??
        false)
  );
  const [focusId, setFocusId] = useState<string | null>(null);
  const [pinned, setPinned] = useState(false);
  const [activeTypes, setActiveTypes] = useState<Set<string> | null>(null);
  const [activeRels, setActiveRels] = useState<Set<string> | null>(null);
  const [showLabels, setShowLabels] = useState(true);
  const [selection, setSelection] = useState<Selection>(null);
  const [playing, setPlaying] = useState(!reducedMotion.current);
  const [speed, setSpeed] = useState("1×");
  const [rotation, setRotation] = useState(0);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const drag = useRef<{ x: number; y: number } | null>(null);
  const raf = useRef(0);
  const last = useRef(0);

  const focus = focusId ?? initialFocus;
  const types = activeTypes ?? new Set(nodeTypes);
  const rels = activeRels ?? new Set(relTypes);

  const base = useMemo(
    () => layoutOrbital(adapted.nodes, adapted.edges, focus),
    [adapted, focus]
  );
  const byId = useMemo(
    () => new Map(adapted.nodes.map((n) => [n.node_id, n])),
    [adapted]
  );
  const pos = useMemo(() => {
    const out = new Map<string, { x: number; y: number; ring: number }>();
    for (const [id, p] of base) {
      const a = p.angle + rotation;
      const radius = RING_RADII[p.ring];
      out.set(id, {
        x: ORBIT_CX + radius * Math.cos(a),
        y: ORBIT_CY + radius * Math.sin(a) * 0.72,
        ring: p.ring,
      });
    }
    return out;
  }, [base, rotation]);

  useEffect(() => {
    if (!playing) return;
    last.current = performance.now();
    const tick = (now: number) => {
      const dt = (now - last.current) / 1000;
      last.current = now;
      setRotation((r) => r + dt * (SPEEDS[speed] ?? 0.1));
      raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf.current);
  }, [playing, speed]);

  useEffect(() => () => cancelAnimationFrame(raf.current), []);

  const visibleNodes = adapted.nodes.filter((n) => types.has(n.node_type));
  const visibleIds = new Set(visibleNodes.map((n) => n.node_id));
  const visibleEdges = adapted.edges.filter(
    (e) =>
      rels.has(e.relationship_type) &&
      visibleIds.has(e.source_node_id) &&
      visibleIds.has(e.target_node_id)
  );
  const usedRings = [...new Set(visibleNodes.map((n) => base.get(n.node_id)?.ring ?? 0))]
    .filter((r) => r > 0)
    .sort((a, b) => a - b);

  function toggle(setter: (v: Set<string> | null) => void, current: Set<string>, v: string) {
    const next = new Set(current);
    if (next.has(v)) next.delete(v);
    else next.add(v);
    setter(next);
  }

  function resetView() {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setRotation(0);
    setFocusId(null);
    setPinned(false);
    setSelection(null);
  }

  const selectedNode =
    selection?.kind === "node" ? byId.get(selection.id) : undefined;
  const selectedEdge =
    selection?.kind === "edge"
      ? adapted.edges.find((e) => e.edge_id === selection.id)
      : undefined;
  const selectedNodeRels = selectedNode
    ? adapted.edges.filter(
        (e) =>
          e.source_node_id === selectedNode.node_id ||
          e.target_node_id === selectedNode.node_id
      )
    : [];
  const focusNode = byId.get(focus);
  const depths = useMemo(
    () => bfsDepths(adapted.nodes, adapted.edges, focus),
    [adapted, focus]
  );

  return (
    <section className="card" aria-label="Orbital graph">
      <h2>Orbital explorer</h2>
      <p className="muted">Synthetic demo data. Rings and motion are layout only — they do not indicate risk, guilt, or priority.</p>
      <p className="muted" aria-live="polite" data-testid="orbital-counts">
        Focus: {focusNode?.display_label ?? focus} · Showing{" "}
        {visibleNodes.length} of {adapted.nodes.length} nodes,{" "}
        {visibleEdges.length} of {adapted.edges.length} edges.
        {adapted.droppedEdgeIds.length > 0 &&
          ` ${adapted.droppedEdgeIds.length} edge(s) hidden: endpoint unknown (${adapted.droppedEdgeIds.join(", ")}).`}
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
      <div className="chip-row" role="group" aria-label="Orbital view controls">
        <button type="button" className="chip" onClick={() => setZoom((z) => Math.min(3, +(z + 0.25).toFixed(2)))}>
          Zoom in
        </button>
        <button type="button" className="chip" onClick={() => setZoom((z) => Math.max(0.25, +(z - 0.25).toFixed(2)))}>
          Zoom out
        </button>
        <button type="button" className="chip" onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }); }}>
          Fit to screen
        </button>
        <button type="button" className="chip" aria-pressed={showLabels} onClick={() => setShowLabels((s) => !s)}>
          {showLabels ? "Hide labels" : "Show labels"}
        </button>
        <button type="button" className="chip" onClick={resetView}>
          Reset view
        </button>
        <label className="chip-label">
          Speed{" "}
          <select value={speed} onChange={(ev) => setSpeed(ev.target.value)} aria-label="Animation speed">
            {Object.keys(SPEEDS).map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </label>
      </div>
      <div className="orbital-stage">
        <button
          type="button"
          className="chip orbital-play"
          onClick={() => setPlaying((p) => !p)}
          aria-label={playing ? "Pause animation" : "Play animation"}
          title={reducedMotion.current ? "Paused by default: reduced-motion preference detected." : undefined}
        >
          {playing ? "⏸" : "▶"}
        </button>
        <svg
          viewBox={`0 0 ${ORBIT_WIDTH} ${ORBIT_HEIGHT}`}
          role="img"
          aria-label={`Orbital graph focused on ${focusNode?.display_label ?? focus}: ${visibleNodes.length} nodes, ${visibleEdges.length} edges. Tab to reach nodes and edges, Enter to select, arrow keys to pan.`}
          tabIndex={0}
          data-testid="orbital-svg"
          className="graph-canvas orbital-canvas"
          onKeyDown={(ev) => {
            if (ev.key === "ArrowLeft") setPan((p) => ({ ...p, x: p.x + PAN_STEP }));
            else if (ev.key === "ArrowRight") setPan((p) => ({ ...p, x: p.x - PAN_STEP }));
            else if (ev.key === "ArrowUp") setPan((p) => ({ ...p, y: p.y + PAN_STEP }));
            else if (ev.key === "ArrowDown") setPan((p) => ({ ...p, y: p.y - PAN_STEP }));
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
          <g transform={`translate(${pan.x},${pan.y}) scale(${zoom})`} data-testid="orbital-viewport">
            {usedRings.map((r) => (
              <ellipse
                key={r}
                cx={ORBIT_CX}
                cy={ORBIT_CY}
                rx={RING_RADII[r]}
                ry={RING_RADII[r] * 0.72}
                className="orbit-ring"
              />
            ))}
            {visibleEdges.map((e) => {
              const a = pos.get(e.source_node_id);
              const b = pos.get(e.target_node_id);
              if (!a || !b) return null;
              const selected = selection?.kind === "edge" && selection.id === e.edge_id;
              return (
                <g
                  key={e.edge_id}
                  tabIndex={0}
                  role="button"
                  aria-label={`Edge ${e.edge_id}: ${e.source_node_id} ${e.relationship_type} ${e.target_node_id}`}
                  data-edge={e.edge_id}
                  className="graph-edge orbital-edge"
                  onClick={() => setSelection({ kind: "edge", id: e.edge_id })}
                  onKeyDown={(ev) => {
                    if (ev.key === "Enter" || ev.key === " ") {
                      ev.preventDefault();
                      setSelection({ kind: "edge", id: e.edge_id });
                    }
                  }}
                >
                  <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} strokeWidth={selected ? 4 : 2}>
                    <title>{`${e.edge_id}: ${e.relationship_type}`}</title>
                  </line>
                </g>
              );
            })}
            {visibleNodes.map((n) => {
              const p = pos.get(n.node_id);
              if (!p) return null;
              const isFocus = n.node_id === focus;
              const selected = selection?.kind === "node" && selection.id === n.node_id;
              const r = isFocus ? 14 : p.ring === 1 ? 10 : 8;
              return (
                <g
                  key={n.node_id}
                  tabIndex={0}
                  role="button"
                  aria-label={`${n.display_label} (${n.node_type})${isFocus ? ", orbit focus" : ""}`}
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
                  <NodeGlyph type={n.node_type} x={p.x} y={p.y} r={selected ? r + 3 : r} focus={isFocus} />
                  {showLabels && (
                    <text x={p.x + r + 6} y={p.y + 5} className="graph-label orbital-label">
                      {n.display_label}
                    </text>
                  )}
                </g>
              );
            })}
          </g>
        </svg>
      </div>
      <ul className="legend" aria-label="Entity legend">
        {nodeTypes.map((t) => (
          <li key={t}>
            <span className={`legend-swatch legend-${t}`} aria-hidden="true" /> {t}
          </li>
        ))}
        <li className="muted">Shapes + labels identify types (never color alone). Ring = graph steps from focus, not risk.</li>
      </ul>
      <div aria-live="polite" data-testid="orbital-detail">
        {selectedNode && (
          <div className="alert ok">
            <strong>{selectedNode.display_label}</strong> ({selectedNode.node_type})
            {selectedNode.node_id === focus ? " · orbit focus" : ""}
            <br />
            Source: <code>{selectedNode.source_record_ids.join(", ")}</code>
            <br />
            {selectedNodeRels.length} relationship(s):{" "}
            {selectedNodeRels.map((e) => (
              <span key={e.edge_id}>
                <code>{e.edge_id}</code> {e.relationship_type}{" "}
              </span>
            ))}
            <br />
            {pinned && focus === selectedNode.node_id ? (
              <button type="button" className="chip" onClick={() => { setFocusId(null); setPinned(false); }}>
                Unpin focus
              </button>
            ) : (
              <button type="button" className="chip" onClick={() => { setFocusId(selectedNode.node_id); setPinned(true); }}>
                Pin as orbit focus
              </button>
            )}
          </div>
        )}
        {selectedEdge && (
          <div className="alert ok">
            <strong>{selectedEdge.edge_id}</strong>: {selectedEdge.source_node_id}{" "}
            {selectedEdge.relationship_type} {selectedEdge.target_node_id}
            <br />
            Provenance: <code>{selectedEdge.source_event_ids.join(", ")}</code> · Evidence:{" "}
            <code>{selectedEdge.evidence_ids.join(", ")}</code>
            <br />
            Valid: {selectedEdge.valid_from} → {selectedEdge.valid_to ?? "present"} · Trace:{" "}
            <code>{selectedEdge.trace_id}</code>
          </div>
        )}
        {!selectedNode && !selectedEdge && (
          <p className="muted">Select a node or edge for details.{depths.size === 0 && focus !== "" ? " Focus has no connections in the current filter." : ""}</p>
        )}
      </div>
    </section>
  );
}
