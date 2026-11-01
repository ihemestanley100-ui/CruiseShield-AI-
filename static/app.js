/* Shared UI helpers: health badge, JSON POST actions, replay, AI, forms. */
"use strict";

async function postJSON(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = (data && data.error) || {};
    throw new Error((err.code || res.status) + ": " + (err.message || "request failed"));
  }
  return data;
}

/* Escape untrusted text (model output, server messages, ids) before it
 * reaches innerHTML. Static markup stays literal; every ${...} value that
 * is not a hardcoded string must pass through esc(). */
function esc(value) {
  return String(value === null || value === undefined ? "" : value).replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
}

function setHTML(id, html) {
  const el = document.getElementById(id);
  if (el) el.innerHTML = html;
}

async function refreshHealth() {
  const badge = document.getElementById("health-badge");
  if (!badge) return;
  try {
    const res = await fetch("/api/v1/health");
    const data = await res.json();
    badge.textContent = "health: " + data.status;
    badge.className = "badge " + (data.status === "healthy" ? "ok" : "bad");
  } catch {
    badge.textContent = "health: unreachable";
    badge.className = "badge bad";
  }
}

/* Replay state is page-local; cursor tracked in a module variable. */
let replayCursor = 0;

async function loadReplay(cursor) {
  if (typeof window.CS_SCENARIO === "undefined") return;
  const res = await fetch(`/api/v1/replay/${window.CS_SCENARIO}?cursor=${cursor}`);
  const data = await res.json();
  replayCursor = data.cursor;
  const cur = data.current_event;
  setHTML("replay-state",
    `Event ${esc(data.cursor)}/${esc(data.total)}` +
    (cur ? ` — <code>${esc(cur.event_id)}</code> ${esc(cur.transaction.transaction_id)} ${esc(cur.occurred_at)}` : " — start") +
    `<br>Transactions: ${esc(data.counts.transactions)}, Edges: ${esc(data.counts.edges)}`);
  setHTML("replay-timeline",
    data.cumulative_event_ids.map((id) => `<li><code>${esc(id)}</code></li>`).join(""));
}

document.addEventListener("DOMContentLoaded", () => {
  refreshHealth();

  document.querySelectorAll("[data-action='judge-start']").forEach((btn) => {
    btn.addEventListener("click", async () => {
      btn.disabled = true;
      setHTML("judge-msg", "Starting…");
      try {
        const data = await postJSON("/api/v1/demo/judge-start", {});
        window.location.href = data.url;
      } catch (e) {
        setHTML("judge-msg", `<div class="alert error">${esc(e.message)}</div>`);
        btn.disabled = false;
      }
    });
  });

  const scenarioForm = document.getElementById("scenario-form");
  if (scenarioForm) {
    scenarioForm.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const id = document.getElementById("scenario").value;
      setHTML("scenario-msg", "Resetting…");
      try {
        await postJSON(`/api/v1/demo/scenarios/${id}/start`, {});
        window.location.reload();
      } catch (e) {
        setHTML("scenario-msg", `<div class="alert error">${esc(e.message)}</div>`);
      }
    });
  }

  document.querySelectorAll("[data-action='ai-analyze']").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const inv = btn.getAttribute("data-inv");
      btn.disabled = true;
      setHTML("ai-result", "Calling model…");
      try {
        const run = await postJSON(`/api/v1/investigations/${inv}/ai-analysis`, {});
        const r = run.result || {};
        const findings = (r.key_findings || []).map((f) =>
          `<li>${esc(f.finding)} <span class="muted">[${(f.evidence_ids || []).map(esc).join(", ")}]</span></li>`).join("");
        setHTML("ai-result",
          `<div class="alert ok">Status ${esc(run.status)} · model ${esc(run.model_id)} · ` +
          `latency ${esc(run.latency_ms)} ms · request <code>${esc(run.request_id || "n/a")}</code><br>` +
          `Schema ${esc(run.schema_validation_status)} · Refs ${esc(run.evidence_reference_validation_status)}</div>` +
          `<p><strong>System-computed fact:</strong> risk score is computed by the app, not the model.</p>` +
          `<p>${esc(r.summary || "")}</p><ul>${findings}</ul>` +
          `<p class="muted">Conclusion: ${esc(r.conclusion || "n/a")}. ${esc(r.disclaimer || "")}</p>`);
      } catch (e) {
        setHTML("ai-result", `<div class="alert error">AI unavailable: ${esc(e.message)}. ` +
          `Graph, risk, replay, simulation, and case features remain usable.</div>`);
      } finally {
        btn.disabled = false;
      }
    });
  });

  document.querySelectorAll("[data-action='replay-step']").forEach((btn) => {
    btn.addEventListener("click", () => {
      loadReplay(replayCursor + parseInt(btn.getAttribute("data-dir"), 10)).catch((e) =>
        setHTML("replay-state", `<div class="alert error">${esc(e.message)}</div>`));
    });
  });
  document.querySelectorAll("[data-action='replay-reset']").forEach((btn) => {
    btn.addEventListener("click", () => loadReplay(0));
  });
  if (document.getElementById("replay-state")) loadReplay(0).catch(() => {});

  const simForm = document.getElementById("sim-form");
  if (simForm) {
    simForm.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const sel = document.getElementById("sim-edges");
      const ids = Array.from(sel.selectedOptions).map((o) => o.value);
      setHTML("sim-result", "Running…");
      try {
        const sim = await postJSON("/api/v1/simulations", {
          target_transaction_id: window.CS_TXN,
          ignored_edge_ids: ids,
          assumption: document.getElementById("sim-assumption").value,
        });
        setHTML("sim-result",
          `<div class="alert ok">Baseline ${esc(sim.baseline_score)} (${esc(sim.baseline_band)}) → ` +
          `simulated ${esc(sim.simulated_score)} (${esc(sim.simulated_band)}). ` +
          `Run <code>${esc(sim.simulation_id)}</code>.</div>` +
          `<p class="muted">${esc(sim.limitations)}</p>`);
      } catch (e) {
        setHTML("sim-result", `<div class="alert error">${esc(e.message)}</div>`);
      }
    });
  }

  const decForm = document.getElementById("decision-form");
  if (decForm) {
    decForm.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const caseId = decForm.getAttribute("data-case");
      setHTML("decision-result", "Recording…");
      try {
        const data = await postJSON(`/api/v1/cases/${caseId}/decisions`, {
          decision: document.getElementById("dec-label").value,
          target_status: document.getElementById("dec-target").value,
          reason: document.getElementById("dec-reason").value,
          actor_id: "investigator",
        });
        setHTML("decision-result",
          `<div class="alert ok">Recorded ${esc(data.decision.decision_id)}; ` +
          `case now ${esc(data.case.status)}; audit ${esc(data.audit.audit_event_id)}.</div>`);
      } catch (e) {
        setHTML("decision-result", `<div class="alert error">${esc(e.message)}</div>`);
      }
    });
  }
});
