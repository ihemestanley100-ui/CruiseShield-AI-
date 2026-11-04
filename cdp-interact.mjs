/* CDP interaction client: genuinely drives the language selector in
 * headless Edge over the DevTools protocol (trusted mouse + keyboard
 * events, not DOM pokes). Flow: open panel -> filter -> arrow+Enter
 * select -> reopen -> Escape close -> reopen -> outside-click close.
 * Usage: node cdp-interact.mjs <url> <WxH> <outdir> <name> [cookie]
 * Outputs: <name>.interact.json (step records), <name>-open.png,
 * <name>.png (final), <name>.dom.html, <name>.console.json,
 * <name>.net.json. No new dependencies (ws from frontend/node_modules).
 */
import { createRequire } from "node:module";
import { spawn } from "node:child_process";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";

const require = createRequire(import.meta.url);
const WebSocket = require("C:/Users/HP/Projects/CruiseShield AI™/frontend/node_modules/ws");

const EDGE =
  "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const PORT = 9223;

const [url, size, outdir, name, cookieArg] = process.argv.slice(2);
if (!url || !size || !outdir || !name) {
  console.error("usage: node cdp-interact.mjs <url> <WxH> <outdir> <name> [cookie]");
  process.exit(2);
}
const [W, H] = size.split(",").map(Number);
fs.mkdirSync(outdir, { recursive: true });

function httpGetJson(pathname) {
  return new Promise((resolve, reject) => {
    http
      .get({ host: "127.0.0.1", port: PORT, path: pathname }, (res) => {
        let body = "";
        res.on("data", (c) => (body += c));
        res.on("end", () => {
          try {
            resolve(JSON.parse(body));
          } catch (e) {
            reject(e);
          }
        });
      })
      .on("error", reject);
  });
}

async function waitForEndpoint(tries = 40) {
  for (let i = 0; i < tries; i++) {
    try {
      await httpGetJson("/json/version");
      return true;
    } catch {
      await new Promise((r) => setTimeout(r, 500));
    }
  }
  return false;
}

const profile = fs.mkdtempSync(path.join(os.tmpdir(), "edge-cdp-"));
const edge = spawn(
  EDGE,
  [
    "--headless=new",
    "--disable-gpu",
    "--no-first-run",
    "--hide-scrollbars",
    "--no-proxy-server",
    `--remote-debugging-port=${PORT}`,
    `--user-data-dir=${profile}`,
    `--window-size=${W},${H}`,
    "about:blank",
  ],
  { stdio: "ignore" }
);

const fail = (msg) => {
  console.error("FATAL: " + msg);
  try {
    edge.kill();
  } catch {}
  process.exit(1);
};

if (!(await waitForEndpoint())) fail("devtools endpoint never came up");

const targets = await httpGetJson("/json/new?about:blank").catch(() => null);
const target = targets && targets.webSocketDebuggerUrl ? targets : (await httpGetJson("/json/list")).find((t) => t.type === "page");
if (!target || !target.webSocketDebuggerUrl) fail("no page target");

const ws = new WebSocket(target.webSocketDebuggerUrl, { maxPayload: 256 * 1024 * 1024 });
await new Promise((resolve, reject) => {
  ws.on("open", resolve);
  ws.on("error", reject);
});

const consoleErrors = [];
const failedRequests = [];
const inflight = new Set();
const reqUrls = new Map();
const tStart = Date.now();
ws.on("message", (raw) => {
  const msg = JSON.parse(raw.toString());
  if (msg.id !== undefined && pending.has(msg.id)) {
    const { resolve, reject } = pending.get(msg.id);
    pending.delete(msg.id);
    if (msg.error) reject(new Error(JSON.stringify(msg.error)));
    else resolve(msg.result);
    return;
  }
  if (msg.method === "Runtime.consoleAPICalled" && msg.params.type === "error") {
    consoleErrors.push(msg.params.args.map((a) => a.value ?? a.description ?? a.type).join(" "));
  } else if (msg.method === "Runtime.exceptionThrown") {
    const d = msg.params.exceptionDetails;
    consoleErrors.push("EXCEPTION: " + (d.text || "") + " | " + (d.exception?.description || "").slice(0, 300));
  } else if (msg.method === "Log.entryAdded" && ["error"].includes(msg.params.entry.level)) {
    consoleErrors.push("LOG: " + msg.params.entry.text + " @ " + msg.params.entry.url);
  } else if (msg.method === "Network.requestWillBeSent") {
    inflight.add(msg.params.requestId);
    reqUrls.set(msg.params.requestId, msg.params.request.url);
  } else if (msg.method === "Network.loadingFinished" || msg.method === "Network.loadingFailed") {
    inflight.delete(msg.params.requestId);
    if (msg.method === "Network.loadingFailed") {
      failedRequests.push(`FAILED ${msg.params.errorText} :: ${reqUrls.get(msg.params.requestId) || "?"}`);
    }
  } else if (msg.method === "Network.responseReceived") {
    const st = msg.params.response.status;
    if (st >= 400) failedRequests.push(`${st} ${msg.params.response.url}`);
  }
});
let nextId = 1;
const pending = new Map();
function send(method, params = {}) {
  const id = nextId++;
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
    ws.send(JSON.stringify({ id, method, params }));
  });
}
async function evaluate(expression) {
  const res = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  return res.result?.value;
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function settle(budgetMs = 20000) {
  const t0 = Date.now();
  for (;;) {
    await sleep(500);
    const elapsed = Date.now() - t0;
    if ((inflight.size === 0 && elapsed > 4000) || elapsed > budgetMs) break;
  }
}
async function clickAt(x, y) {
  await send("Input.dispatchMouseEvent", { type: "mousePressed", x, y, button: "left", clickCount: 1 });
  await send("Input.dispatchMouseEvent", { type: "mouseReleased", x, y, button: "left", clickCount: 1 });
}
async function keyPress(key, windowsVirtualKeyCode) {
  await send("Input.dispatchKeyEvent", { type: "keyDown", key, code: key, windowsVirtualKeyCode });
  await send("Input.dispatchKeyEvent", { type: "keyUp", key, code: key, windowsVirtualKeyCode });
}
async function buttonCenter() {
  return evaluate(`(() => {
    const b = document.querySelector(".lang-button");
    if (!b) return null;
    b.scrollIntoView({ block: "nearest" });
    const r = b.getBoundingClientRect();
    return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
  })()`);
}
async function selectorState() {
  return evaluate(`(() => {
    const b = document.querySelector(".lang-button");
    const panel = document.querySelector(".lang-panel");
    const search = document.querySelector(".lang-search");
    const opts = panel ? panel.querySelectorAll('[role="option"]') : [];
    const activeEl = search ? document.getElementById(search.getAttribute("aria-activedescendant") || "") : null;
    return {
      buttonFound: !!b,
      expanded: b ? b.getAttribute("aria-expanded") : null,
      labelledBy: b ? b.getAttribute("aria-label") : null,
      panelOpen: !!panel,
      panelRole: panel ? panel.getAttribute("role") : null,
      searchRole: search ? search.getAttribute("role") : null,
      searchFocused: search ? document.activeElement === search : false,
      buttonFocused: b ? document.activeElement === b : false,
      optionCount: opts.length,
      firstOption: opts.length ? (opts[0].textContent || "").trim().slice(0, 60) : null,
      optionTags: (() => {
        const metas = panel ? panel.querySelectorAll(".lang-option-meta") : [];
        return Array.from(metas).slice(0, 8).map((m) => ((m.textContent || "").split("·").pop() || "").trim());
      })(),
      activeDescendant: activeEl ? (activeEl.textContent || "").trim().slice(0, 60) : null,
      selectedTag: (() => {
        const sel = panel ? panel.querySelector('[aria-selected="true"] .lang-option-meta') : null;
        return sel ? (sel.textContent || "").trim() : null;
      })(),
      docLang: document.documentElement.lang,
      docDir: document.documentElement.dir,
      stored: (() => { try { return localStorage.getItem("cruiseshield-locale"); } catch { return null; } })(),
    };
  })()`);
}

await send("Page.enable");
await send("Runtime.enable");
await send("Log.enable");
await send("Network.enable");
if (cookieArg) {
  const eq = cookieArg.indexOf("=");
  await send("Network.setCookie", { name: cookieArg.slice(0, eq), value: cookieArg.slice(eq + 1), domain: "127.0.0.1", path: "/" });
}
await send("Emulation.setDeviceMetricsOverride", { width: W, height: H, deviceScaleFactor: 1, mobile: W < 768 });
await send("Page.navigate", { url });
await settle();

const steps = {};
steps.initial = await selectorState();
const c0 = await buttonCenter();
if (!c0) fail("language button not found");
await clickAt(c0.x, c0.y);
await sleep(900);
steps.afterOpen = await selectorState();
const shotOpen = await send("Page.captureScreenshot", { format: "png" });
fs.writeFileSync(path.join(outdir, `${name}-open.png`), Buffer.from(shotOpen.data, "base64"));

await send("Input.insertText", { text: "ara" });
await sleep(700);
steps.afterFilter = await selectorState();
await keyPress("ArrowDown", 40);
await sleep(300);
steps.afterArrow = await selectorState();
await keyPress("Enter", 13);
await sleep(900);
steps.afterSelect = await selectorState();

const c1 = await buttonCenter();
await clickAt(c1.x, c1.y);
await sleep(900);
steps.reopened = await selectorState();
await keyPress("Escape", 27);
await sleep(600);
steps.afterEscape = await selectorState();

const c2 = await buttonCenter();
await clickAt(c2.x, c2.y);
await sleep(900);
await clickAt(30, H - 30);
await sleep(600);
steps.afterOutsideClick = await selectorState();

fs.writeFileSync(path.join(outdir, `${name}.interact.json`), JSON.stringify(steps, null, 2));
const shot = await send("Page.captureScreenshot", { format: "png" });
fs.writeFileSync(path.join(outdir, `${name}.png`), Buffer.from(shot.data, "base64"));
const dom = await evaluate(`document.documentElement.outerHTML`);
fs.writeFileSync(path.join(outdir, `${name}.dom.html`), String(dom).slice(0, 500000));
fs.writeFileSync(path.join(outdir, `${name}.console.json`), JSON.stringify(consoleErrors, null, 2));
fs.writeFileSync(path.join(outdir, `${name}.net.json`), JSON.stringify(failedRequests, null, 2));

const filtered = steps.afterFilter.optionTags || [];
const expectedTag = filtered[Math.min(1, Math.max(0, filtered.length - 1))] || null;
const ok =
  steps.initial.expanded === "false" &&
  steps.afterOpen.expanded === "true" &&
  steps.afterOpen.panelRole === "dialog" &&
  steps.afterOpen.searchRole === "combobox" &&
  steps.afterOpen.searchFocused === true &&
  steps.afterFilter.optionCount > 0 &&
  expectedTag !== null &&
  steps.afterSelect.docLang === expectedTag &&
  steps.afterSelect.stored === expectedTag &&
  steps.afterSelect.expanded === "false" &&
  steps.afterSelect.buttonFocused === true &&
  steps.reopened.expanded === "true" &&
  steps.afterEscape.expanded === "false" &&
  steps.afterEscape.buttonFocused === true &&
  steps.afterOutsideClick.expanded === "false";
console.log(`INTERACT ${name}: open=${steps.afterOpen.expanded} focusSearch=${steps.afterOpen.searchFocused} ` +
  `filterN=${steps.afterFilter.optionCount} first=${JSON.stringify((filtered[0] || "") + "/" + (filtered[1] || ""))} ` +
  `expected=${expectedTag} selected=${steps.afterSelect.docLang} stored=${steps.afterSelect.stored} ` +
  `escClosed=${steps.afterEscape.expanded} escFocus=${steps.afterEscape.buttonFocused} ` +
  `outsideClosed=${steps.afterOutsideClick.expanded} consoleErr=${consoleErrors.length} netFail=${failedRequests.length} VERDICT=${ok ? "PASS" : "CHECK"}`);

ws.close();
try {
  edge.kill();
} catch {}
for (let i = 0; i < 10; i++) {
  try {
    fs.rmSync(profile, { recursive: true, force: true });
    break;
  } catch {
    Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 500);
  }
}
process.exit(0);
