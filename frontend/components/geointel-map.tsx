"use client";

/* Investigation map: provider-neutral schematic renderer.

No tile dependency and no paid map SDK: markers render on a
schematic grid from the provider-neutral map payload. Verified,
estimated, observed, and unverified evidence use distinct marker
shapes (never the same visual). Coordinates render only when the
server returns them (authorized + unmasked); masked payloads show
status rows without positions. A Leaflet/OSM tile binding may be
added later behind MAP_PROVIDER without changing this contract.
Zero new i18n keys (translator review pending with I18N-02). */

import type { IntelMap } from "../lib/api";
import { getInvestigationMap, userErrorMessage } from "../lib/api";
import { useState } from "react";
import { useTranslation } from "../lib/i18n/context";

type MapState =
  | { kind: "closed" }
  | { kind: "loading" }
  | { kind: "ready"; data: IntelMap }
  | { kind: "error"; message: string };

function kindOf(item: Record<string, unknown>): string {
  return String(item.kind ?? "UNKNOWN");
}

function statusOf(item: Record<string, unknown>): string {
  return String(
    item.status ?? item.verification_status ?? "UNVERIFIED"
  );
}

function shapeFor(status: string, kind: string): string {
  if (status === "VERIFIED" || status === "AUTHORIZED_OBSERVATION")
    return "square";
  if (status === "ESTIMATED" || kind === "IP_ESTIMATE") return "circle";
  if (status === "PARTIALLY_VERIFIED" || kind === "TELECOM")
    return "triangle";
  return "hollow";
}

function MarkerGlyph({ shape, x, y }: { shape: string; x: number; y: number }) {
  if (shape === "square")
    return <rect x={x - 6} y={y - 6} width={12} height={12} />;
  if (shape === "circle") return <circle cx={x} cy={y} r={7} />;
  if (shape === "triangle")
    return <polygon points={`${x},${y - 8} ${x + 8},${y + 6} ${x - 8},${y + 6}`} />;
  return <circle cx={x} cy={y} r={7} fill="none" strokeWidth={2} />;
}

export function GeointelMap({
  investigationId,
}: {
  investigationId: string;
}) {
  const { t: tEvidence } = useTranslation("evidence");
  const { t: tCommon } = useTranslation("common");
  const [state, setState] = useState<MapState>({ kind: "closed" });
  const [layers, setLayers] = useState<string[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [selected, setSelected] = useState<Record<string, unknown> | null>(
    null
  );
  const load = () => {
    setState({ kind: "loading" });
    getInvestigationMap(investigationId).then(
      (data) => {
        setState({ kind: "ready", data });
        setLayers(Object.keys(data.layers));
      },
      (err: unknown) =>
        setState({
          kind: "error",
          message: userErrorMessage(err, tCommon),
        })
    );
  };
  if (state.kind === "closed") {
    return (
      <div>
        <h3>Investigation map</h3>
        <p>
          <button type="button" onClick={load} aria-expanded={false}>
            {tEvidence("showProv")}
          </button>
        </p>
      </div>
    );
  }
  const close = () => setState({ kind: "closed" });
  const toggleLayer = (name: string) =>
    setLayers((prev) =>
      prev.includes(name) ? prev.filter((l) => l !== name) : [...prev, name]
    );
  const visible =
    state.kind === "ready"
      ? Object.entries(state.data.layers).flatMap(([name, layer]) =>
          layers.includes(name)
            ? layer.items
                .filter(
                  (item) =>
                    !statusFilter || statusOf(item) === statusFilter
                )
                .map((item, i) => ({ name, item, i }))
            : []
        )
      : [];
  return (
    <div>
      <h3>Investigation map</h3>
      <p>
        <button type="button" onClick={close} aria-expanded={true}>
          {tEvidence("hideProv")}
        </button>
      </p>
      {state.kind === "loading" && (
        <p className="muted">{tCommon("loading")}</p>
      )}
      {state.kind === "error" && (
        <>
          <div className="alert error" role="alert">
            {state.message}
          </div>
          <p>
            <button type="button" onClick={load}>
              {tCommon("retry")}
            </button>
          </p>
        </>
      )}
      {state.kind === "ready" && (
        <>
          <p className="muted">
            Schematic rendering · {state.data.map_provider_note}
            {state.data.masked ? " · coordinates masked" : ""}
          </p>
          <fieldset>
            <legend>Layers</legend>
            {Object.keys(state.data.layers).map((name) => (
              <label key={name}>
                <input
                  type="checkbox"
                  checked={layers.includes(name)}
                  onChange={() => toggleLayer(name)}
                />{" "}
                {name} ({state.data.layers[name].item_count})
              </label>
            ))}
          </fieldset>
          <p>
            <label>
              Status filter{" "}
              <input
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                placeholder="VERIFIED / ESTIMATED / …"
              />
            </label>
          </p>
          <svg
            role="img"
            aria-label="Evidence markers schematic"
            viewBox="0 0 400 220"
            width="100%"
            height="220"
          >
            {Array.from({ length: 9 }, (_, i) => (
              <line
                key={`v${i}`}
                x1={(i + 1) * 40}
                y1={0}
                x2={(i + 1) * 40}
                y2={220}
                strokeWidth={1}
                opacity={0.25}
              />
            ))}
            {Array.from({ length: 5 }, (_, i) => (
              <line
                key={`h${i}`}
                x1={0}
                y1={(i + 1) * 36}
                x2={400}
                y2={(i + 1) * 36}
                strokeWidth={1}
                opacity={0.25}
              />
            ))}
            {visible.map(({ name, item, i }, idx) => {
              const x = 30 + ((idx * 53) % 340);
              const y = 30 + ((idx * 47) % 160);
              return (
                <g
                  key={`${name}-${i}`}
                  onClick={() => setSelected({ ...item, layer: name })}
                  role="button"
                  aria-label={`${name} ${statusOf(item)}`}
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ")
                      setSelected({ ...item, layer: name });
                  }}
                >
                  <MarkerGlyph
                    shape={shapeFor(statusOf(item), kindOf(item))}
                    x={x}
                    y={y}
                  />
                </g>
              );
            })}
          </svg>
          <p className="muted">
            square = verified/authorized · circle = estimated · triangle =
            partial/telecom · hollow = unverified
          </p>
          {selected && (
            <dl>
              <dt>Layer</dt>
              <dd>{String(selected.layer ?? "")}</dd>
              <dt>Status</dt>
              <dd>
                <strong>{statusOf(selected)}</strong>
              </dd>
              <dt>Reference</dt>
              <dd>
                {String(
                  selected.verification_id ??
                    selected.observation_id ??
                    selected.transaction_id ??
                    ""
                )}
              </dd>
              <dt>Source</dt>
              <dd>
                {String(
                  selected.provider_id ?? selected.source ?? "platform"
                )}
              </dd>
              <dt>Observed</dt>
              <dd>{String(selected.observed_at ?? selected.verified_at ?? "")}</dd>
            </dl>
          )}
          {visible.length === 0 && (
            <p className="muted">{tCommon("none")}</p>
          )}
        </>
      )}
    </div>
  );
}
