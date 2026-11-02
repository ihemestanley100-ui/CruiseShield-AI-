/* CDP capture client: drives headless Edge over the DevTools protocol.
 * One capture = screenshot + DOM + console errors + failed requests +
 * horizontal-overflow probe + lang/dir. No new dependencies: uses the
 * `ws` package already present in frontend/node_modules.
 * Usage: node cdp-capture.mjs <url> <WxH> <outdir> <name> [cookie] [profileDir] [seedPairs]
 *   cookie:    "name=value" session cookie to plant before navigation
 *   profileDir: persistent Edge profile (kept); default is a temp profile
 *   seedPairs: "k=v;k2=v2" localStorage seeds applied + reloaded once
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

const [url, size, outdir, name, cookieArg, profileArg, seedArg] = process.argv.slice(2);
if (!url || !size || !outdir || !name) {
  console.error("usage: node cdp-capture.mjs <url> <WxH> <outdir> <name> [cookie] [profileDir] [seedPairs]");
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

const keepProfile = Boolean(profileArg);
const profile = profileArg || fs.mkdtempSync(path.join(os.tmpdir(), "edge-cdp-"));
fs.mkdirSync(profile, { recursive: true });
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

const tStart = Date.now();
let nextId = 1;
const pending = new Map();
const consoleErrors = [];
const failedRequests = [];
const inflight = new Set();
const reqUrls = new Map();
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
    const stack =
      d.stackTrace?.callFrames?.slice(0, 4).map((f) => `${f.functionName}@${f.url}:${f.lineNumber}`).join(" <- ") || "";
    consoleErrors.push(
      "EXCEPTION: " + (d.text || "") + " | " + (d.exception?.description || "").slice(0, 400) + (stack ? " | " + stack : "")
    );
  } else if (msg.method === "Log.entryAdded" && ["error"].includes(msg.params.entry.level)) {
    consoleErrors.push("LOG: " + msg.params.entry.text + " @ " + msg.params.entry.url);
  } else if (msg.method === "Network.requestWillBeSent") {
    inflight.add(msg.params.requestId);
    reqUrls.set(msg.params.requestId, msg.params.request.url);
  } else if (msg.method === "Network.loadingFinished" || msg.method === "Network.loadingFailed") {
    inflight.delete(msg.params.requestId);
    if (msg.method === "Network.loadingFailed") {
      failedRequests.push(
        `t=${Date.now() - tStart}ms ${msg.params.type} FAILED ${msg.params.errorText} :: ${reqUrls.get(msg.params.requestId) || "?"}`
      );
    }
  } else if (msg.method === "Network.responseReceived") {
    const st = msg.params.response.status;
    if (st >= 400) failedRequests.push(`${st} ${msg.params.response.url}`);
  }
});
function send(method, params = {}) {
  const id = nextId++;
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
    ws.send(JSON.stringify({ id, method, params }));
  });
}

await send("Page.enable");
await send("Runtime.enable");
await send("Log.enable");
await send("Network.enable");
if (cookieArg) {
  const eq = cookieArg.indexOf("=");
  await send("Network.setCookie", {
    name: cookieArg.slice(0, eq),
    value: cookieArg.slice(eq + 1),
    domain: "127.0.0.1",
    path: "/",
  });
}
await send("Emulation.setDeviceMetricsOverride", {
  width: W,
  height: H,
  deviceScaleFactor: 1,
  mobile: W < 768,
});
const tNav = Date.now();
await send("Page.navigate", { url });

// Settle: network idle + fixed budget, whichever first (cap 25s).
const t0 = Date.now();
for (;;) {
  await new Promise((r) => setTimeout(r, 500));
  const elapsed = Date.now() - t0;
  if ((inflight.size === 0 && elapsed > 4000) || elapsed > 25000) break;
}
const phases = { navigatedMs: t0 - tNav, settleDoneMs: Date.now() - tStart };
if (seedArg) {
  // Plant localStorage, reload once, re-settle: models a returning
  // visitor whose stored preference must win without URL params.
  const pairs = seedArg.split(";").filter(Boolean);
  for (const pair of pairs) {
    const eq = pair.indexOf("=");
    await send("Runtime.evaluate", {
      expression: `localStorage.setItem(${JSON.stringify(pair.slice(0, eq))},${JSON.stringify(pair.slice(eq + 1))})`,
    });
  }
  await send("Page.reload");
  const t1 = Date.now();
  for (;;) {
    await new Promise((r) => setTimeout(r, 500));
    const elapsed = Date.now() - t1;
    if ((inflight.size === 0 && elapsed > 4000) || elapsed > 25000) break;
  }
  phases.reseedReloadMs = Date.now() - tStart;
}
fs.writeFileSync(path.join(outdir, `${name}.phases.json`), JSON.stringify(phases, null, 2));

const shot = await send("Page.captureScreenshot", { format: "png" });
fs.writeFileSync(path.join(outdir, `${name}.png`), Buffer.from(shot.data, "base64"));

async function evaluate(expression) {
  const res = await send("Runtime.evaluate", {
    expression,
    returnByValue: true,
    awaitPromise: true,
  });
  return res.result?.value;
}

const docInfo = await evaluate(`({
  lang: document.documentElement.lang,
  dir: document.documentElement.dir,
  dirAttr: document.documentElement.getAttribute("dir"),
  htmlOpen: document.documentElement.outerHTML.slice(0, 120),
  title: document.title,
  scrollW: document.documentElement.scrollWidth,
  clientW: document.documentElement.clientWidth,
})`);
fs.writeFileSync(path.join(outdir, `${name}.doc.json`), JSON.stringify(docInfo, null, 2));

const offenders = await evaluate(`(() => {
  const vw = document.documentElement.clientWidth;
  const out = [];
  const els = document.querySelectorAll("body *");
  for (const el of els) {
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;
    const cs = getComputedStyle(el);
    if (cs.position === "fixed" && (r.right > vw + 1 || r.left < -1)) {
      // fixed drawers/panels intentionally sit off-viewport; note worst only
    }
    if (r.right > vw + 1 && out.length < 40) {
      let p = el.tagName.toLowerCase();
      if (el.id) p += "#" + el.id;
      else if (el.className && typeof el.className === "string") p += "." + el.className.trim().split(/\\s+/).slice(0, 3).join(".");
      out.push({ el: p, right: Math.round(r.right), width: Math.round(r.width),
                 text: (el.textContent || "").trim().slice(0, 60) });
    }
  }
  return { viewport: vw, scrollW: document.documentElement.scrollWidth, offenders: out };
})()`);
fs.writeFileSync(path.join(outdir, `${name}.overflow.json`), JSON.stringify(offenders, null, 2));

const dom = await evaluate(`document.documentElement.outerHTML`);
fs.writeFileSync(path.join(outdir, `${name}.dom.html`), String(dom).slice(0, 500000));
fs.writeFileSync(path.join(outdir, `${name}.console.json`), JSON.stringify(consoleErrors, null, 2));
fs.writeFileSync(path.join(outdir, `${name}.net.json`), JSON.stringify(failedRequests, null, 2));

console.log(`CAPTURE ${name}: ${W}x${H} lang=${docInfo.lang} dir=${docInfo.dir} scrollW=${docInfo.scrollW} offenders=${offenders.offenders.length} consoleErr=${consoleErrors.length} netFail=${failedRequests.length}`);

ws.close();
try {
  edge.kill();
} catch {}
// Edge releases the profile lazily; retry cleanup, else leave to OS temp.
if (!keepProfile) {
  for (let i = 0; i < 10; i++) {
    try {
      fs.rmSync(profile, { recursive: true, force: true });
      break;
    } catch {
      Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 500);
    }
  }
}
process.exit(0);