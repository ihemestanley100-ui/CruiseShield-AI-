"use client";

import { useState } from "react";
import type { EvidenceItem } from "../lib/api";

const ALL = "all";

function Provenance({ label, ids }: { label: string; ids: string[] }) {
  return (
    <div>
      <span className="muted">{label}: </span>
      {ids.length === 0 ? (
        <span className="muted">none</span>
      ) : (
        ids.map((id, index) => (
          <span key={id}>
            {index > 0 && ", "}
            <code>{id}</code>
          </span>
        ))
      )}
    </div>
  );
}

export function EvidenceList({ items }: { items: EvidenceItem[] }) {
  const types = Array.from(new Set(items.map((i) => i.evidence_type))).sort();
  const [filter, setFilter] = useState<string>(ALL);
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState<ReadonlySet<string>>(new Set());
  const needle = query.trim().toLowerCase();
  const shown = items.filter(
    (i) =>
      (filter === ALL || i.evidence_type === filter) &&
      (needle === "" ||
        i.evidence_id.toLowerCase().includes(needle) ||
        i.evidence_type.toLowerCase().includes(needle) ||
        i.title.toLowerCase().includes(needle) ||
        i.description.toLowerCase().includes(needle))
  );
  const toggle = (id: string) =>
    setOpen((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });

  return (
    <section className="card" aria-labelledby="evidence-h">
      <h2 id="evidence-h">
        Evidence package ({shown.length} of {items.length})
      </h2>
      <p className="evidence-search">
        <label htmlFor="evidence-search">Search evidence</label>{" "}
        <input
          id="evidence-search"
          type="search"
          value={query}
          onChange={(ev) => setQuery(ev.target.value)}
          placeholder="Filter by ID, type, title, or description"
          className="text-input"
        />{" "}
        {query !== "" && (
          <button
            type="button"
            className="chip"
            onClick={() => {
              setQuery("");
              setFilter(ALL);
            }}
          >
            Clear search
          </button>
        )}
      </p>
      <div className="chip-row" role="group" aria-label="Filter by type">
        {[ALL, ...types].map((type) => (
          <button
            key={type}
            type="button"
            className="chip"
            aria-pressed={filter === type}
            onClick={() => setFilter(type)}
          >
            {type} (
            {type === ALL
              ? items.length
              : items.filter((i) => i.evidence_type === type).length}
            )
          </button>
        ))}
      </div>
      {shown.length === 0 ? (
        <p className="muted">
          {query.trim() === ""
            ? "No evidence items match this filter."
            : "No evidence items match this search."}
        </p>
      ) : (
        <ul className="stack">
          {shown.map((item) => {
            const expanded = open.has(item.evidence_id);
            return (
              <li key={item.evidence_id} className="evidence-item">
                <div>
                  <code>{item.evidence_id}</code>{" "}
                  <span className="badge">{item.evidence_type}</span>
                </div>
                <div>{item.title}</div>
                <p className="muted">{item.description}</p>
                <button
                  type="button"
                  className="chip"
                  aria-expanded={expanded}
                  aria-controls={`prov-${item.evidence_id}`}
                  onClick={() => toggle(item.evidence_id)}
                >
                  {expanded ? "Hide provenance" : "Show provenance"}
                </button>
                {expanded && (
                  <div
                    id={`prov-${item.evidence_id}`}
                    className="stack"
                  >
                    <Provenance label="Events" ids={item.event_ids} />
                    <Provenance
                      label="Graph edges"
                      ids={item.graph_edge_ids}
                    />
                    <Provenance
                      label="Rule results"
                      ids={item.rule_result_ids}
                    />
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
