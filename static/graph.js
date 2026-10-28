/* Deterministic SVG graph: BFS layers left-to-right from the sender. No libraries. */
"use strict";

const COLORS = {
  account: "#38bdf8", device: "#fbbf24", phone: "#2dd4bf",
  merchant: "#f472b6", beneficiary: "#f87171", unknown: "#94a3b8",
};

function layout(nodes, edges, roots) {
  const adj = new Map(nodes.map((n) => [n.node_id, []]));
  for (const e of edges) {
    if (adj.has(e.source_node_id)) adj.get(e.source_node_id).push(e.target_node_id);
    if (adj.has(e.target_node_id)) adj.get(e.target_node_id).push(e.source_node_id);
  }
  const depth = new Map();
  const queue = [...roots.filter((r) => adj.has(r))];
  queue.forEach((r) => depth.set(r, 0));
  if (!queue.length && nodes.length) {
    queue.push(nodes[0].node_id);
    depth.set(nodes[0].node_id, 0);
  }
  while (queue.length) {
    const cur = queue.shift();
    for (const nxt of adj.get(cur).sort()) {
      if (!depth.has(nxt)) {
        depth.set(nxt, depth.get(cur) + 1);
        queue.push(nxt);
      }
    }
  }
  const layers = new Map();
  for (const n of nodes) {
    const d = depth.has(n.node_id) ? depth.get(n.node_id) : 99;
    if (!layers.has(d)) layers.set(d, []);
    layers.get(d).push(n.node_id);
  }
  const pos = new Map();
  const ordered = [...layers.keys()].sort((a, b) => a - b);
  ordered.forEach((d, li) => {
    const ids = layers.get(d).sort();
    ids.forEach((id, i) => {
      pos.set(id, { x: 90 + li * 170, y: 60 + i * 62 });
    });
  });
  return pos;
}

function esc(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
}

async function renderGraph() {
  const wrap = document.getElementById("graph-wrap");
  const status = document.getElementById("graph-status");
  const detail = document.getElementById("graph-detail");
  if (!wrap || typeof window.CS_TXN === "undefined") return;
  let data;
  try {
    const res = await fetch(`/api/v1/graph/${window.CS_TXN}`);
    data = await res.json();
    if (!res.ok) throw new Error((data.error || {}).message || res.status);
  } catch (e) {
    if (status) status.textContent = "Graph failed to load: " + e.message;
    return;
  }
  const byId = new Map(data.nodes.map((n) => [n.node_id, n]));
  const roots = [];
  for (const e of data.edges) {
    if (e.relationship_type === "SENT_TO" && !roots.length) {
      roots.push(e.source_node_id, e.target_node_id);
    }
  }
  const pos = layout(data.nodes, data.edges, roots);
  const maxX = Math.max(400, ...[...pos.values()].map((p) => p.x)) + 120;
  const maxY = Math.max(200, ...[...pos.values()].map((p) => p.y)) + 60;
  let svg = `<svg viewBox="0 0 ${maxX} ${maxY}" role="group" aria-label="Network graph">`;
  for (const e of data.edges) {
    const a = pos.get(e.source_node_id), b = pos.get(e.target_node_id);
    if (!a || !b) continue;
    svg += `<line x1="${a.x}" y1="${a.y}" x2="${b.x}" y2="${b.y}" stroke="#475569" stroke-width="2" ` +
      `data-edge="${esc(e.edge_id)}" style="cursor:pointer"><title>${esc(e.edge_id)}: ${esc(e.relationship_type)}</title></line>`;
  }
  for (const n of data.nodes) {
    const p = pos.get(n.node_id);
    const c = COLORS[n.node_type] || COLORS.unknown;
    svg += `<g tabindex="0" role="button" data-node="${esc(n.node_id)}" aria-label="${esc(n.display_label)}">` +
      `<circle cx="${p.x}" cy="${p.y}" r="16" fill="${c}" stroke="#0a1628" stroke-width="2" style="cursor:pointer"/>` +
      `<text x="${p.x + 22}" y="${p.y + 5}" fill="#e2e8f0" font-size="13">${esc(n.display_label)}</text></g>`;
  }
  svg += "</svg>";
  wrap.innerHTML = svg;
  if (status) status.textContent = `${data.counts.nodes} nodes, ${data.counts.edges} edges. Select a node or edge for details.`;

  const showNode = (id) => {
    const n = byId.get(id);
    if (!n || !detail) return;
    const rel = data.edges.filter((e) => e.source_node_id === id || e.target_node_id === id);
    detail.innerHTML = `<div class="alert ok"><strong>${esc(n.display_label)}</strong> (${esc(n.node_type)})<br>` +
      `Source: <code>${esc((n.source_record_ids || []).join(", "))}</code><br>` +
      `${rel.length} relationship(s): ` +
      rel.map((e) => `<code>${esc(e.edge_id)}</code> ${esc(e.relationship_type)}`).join("; ") + "</div>";
  };
  const showEdge = (id) => {
    const e = data.edges.find((x) => x.edge_id === id);
    if (!e || !detail) return;
    detail.innerHTML = `<div class="alert ok"><strong>${esc(e.edge_id)}</strong>: ` +
      `${esc(e.source_node_id)} ${esc(e.relationship_type)} ${esc(e.target_node_id)}<br>` +
      `Provenance: <code>${esc(e.source_event_ids.join(", "))}</code> · ` +
      `Evidence: <code>${esc(e.evidence_ids.join(", "))}</code></div>`;
  };
  wrap.querySelectorAll("[data-node]").forEach((g) => {
    g.addEventListener("click", () => showNode(g.getAttribute("data-node")));
    g.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); showNode(g.getAttribute("data-node")); }
    });
  });
  wrap.querySelectorAll("[data-edge]").forEach((line) => {
    line.addEventListener("click", () => showEdge(line.getAttribute("data-edge")));
  });
}

document.addEventListener("DOMContentLoaded", renderGraph);
