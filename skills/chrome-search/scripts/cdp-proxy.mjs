#!/usr/bin/env node
// CDP Proxy - 通过 HTTP API 操控用户日常 Chrome
// 要求：Chrome 已开启 --remote-debugging-port
// Node.js 22+（使用原生 WebSocket）

import http from 'node:http';
import { URL } from 'node:url';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import net from 'node:net';

const PORT = parseInt(process.env.CDP_PROXY_PORT || '3456');
let ws = null;
let cmdId = 0;
const pending = new Map();
const sessions = new Map();

let WS;
if (typeof globalThis.WebSocket !== 'undefined') {
  WS = globalThis.WebSocket;
} else {
  try {
    WS = (await import('ws')).default;
  } catch {
    console.error('[CDP Proxy] 错误：Node.js 版本 < 22 且未安装 ws 模块');
    process.exit(1);
  }
}

async function discoverChromePort() {
  const possiblePaths = [];
  const platform = os.platform();
  if (platform === 'darwin') {
    const home = os.homedir();
    possiblePaths.push(
      path.join(home, 'Library/Application Support/Google/Chrome/DevToolsActivePort'),
      path.join(home, 'Library/Application Support/Google/Chrome Canary/DevToolsActivePort'),
      path.join(home, 'Library/Application Support/Chromium/DevToolsActivePort'),
    );
  } else if (platform === 'linux') {
    const home = os.homedir();
    possiblePaths.push(
      path.join(home, '.config/google-chrome/DevToolsActivePort'),
      path.join(home, '.config/chromium/DevToolsActivePort'),
    );
  }

  for (const p of possiblePaths) {
    try {
      const content = fs.readFileSync(p, 'utf-8').trim();
      const lines = content.split('\n');
      const port = parseInt(lines[0]);
      if (port > 0 && port < 65536) {
        const ok = await checkPort(port);
        if (ok) return { port, wsPath: lines[1] || null };
      }
    } catch {}
  }

  const commonPorts = [9222, 9229, 9333];
  for (const port of commonPorts) {
    const ok = await checkPort(port);
    if (ok) {
      try {
        const res = await fetch(`http://127.0.0.1:${port}/json/version`);
        if (res.ok) {
          const info = await res.json();
          if (info?.webSocketDebuggerUrl) {
            const wsUrl = new URL(info.webSocketDebuggerUrl);
            return { port, wsPath: wsUrl.pathname };
          }
        }
      } catch {}
      return { port, wsPath: null };
    }
  }
  return null;
}

function checkPort(port) {
  return new Promise((resolve) => {
    const socket = net.createConnection(port, '127.0.0.1');
    const timer = setTimeout(() => { socket.destroy(); resolve(false); }, 2000);
    socket.once('connect', () => { clearTimeout(timer); socket.destroy(); resolve(true); });
    socket.once('error', () => { clearTimeout(timer); resolve(false); });
  });
}

function getWebSocketUrl(port, wsPath) {
  if (wsPath) return `ws://127.0.0.1:${port}${wsPath}`;
  return `ws://127.0.0.1:${port}/devtools/browser`;
}

let chromePort = null, chromeWsPath = null;
let connectingPromise = null;

async function connect() {
  if (ws && (ws.readyState === WS.OPEN || ws.readyState === 1)) return;
  if (connectingPromise) return connectingPromise;

  if (!chromePort) {
    const discovered = await discoverChromePort();
    if (!discovered) {
      throw new Error('Chrome 未开启远程调试端口。请用以下方式启动 Chrome：\n  macOS: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222\n  Linux: google-chrome --remote-debugging-port=9222');
    }
    chromePort = discovered.port;
    chromeWsPath = discovered.wsPath;
  }

  const wsUrl = getWebSocketUrl(chromePort, chromeWsPath);
  return connectingPromise = new Promise((resolve, reject) => {
    ws = new WS(wsUrl);
    const onOpen = () => { cleanup(); connectingPromise = null; console.log(`[CDP Proxy] 已连接 Chrome (端口 ${chromePort})`); resolve(); };
    const onError = (e) => { cleanup(); connectingPromise = null; ws = null; chromePort = null; chromeWsPath = null; reject(new Error(e.message)); };
    const onClose = () => { ws = null; chromePort = null; chromeWsPath = null; sessions.clear(); };
    const onMessage = (evt) => {
      const data = typeof evt === 'string' ? evt : (evt.data || evt);
      const msg = JSON.parse(data);
      if (msg.method === 'Target.attachedToTarget') sessions.set(msg.params.targetInfo.targetId, msg.params.sessionId);
      if (msg.method === 'Fetch.requestPaused') sendCDP('Fetch.failRequest', { requestId: msg.params.requestId, errorReason: 'ConnectionRefused' }, msg.params.sessionId).catch(() => {});
      if (msg.id && pending.has(msg.id)) { clearTimeout(pending.get(msg.id).timer); pending.delete(msg.id); pending.get(msg.id)?.resolve(msg); }
    };
    function cleanup() {
      ws.removeEventListener?.('open', onOpen);
      ws.removeEventListener?.('error', onError);
    }
    if (ws.on) { ws.on('open', onOpen); ws.on('error', onError); ws.on('close', onClose); ws.on('message', onMessage); }
    else { ws.addEventListener('open', onOpen); ws.addEventListener('error', onError); ws.addEventListener('close', onClose); ws.addEventListener('message', onMessage); }
  });
}

function sendCDP(method, params = {}, sessionId = null) {
  return new Promise(async (resolve, reject) => {
    if (!ws || (ws.readyState !== WS.OPEN && ws.readyState !== 1)) {
      try { await connect(); } catch (e) { return reject(new Error('WebSocket 未连接且重连失败: ' + e.message)); }
    }
    const id = ++cmdId;
    const timer = setTimeout(() => { pending.delete(id); reject(new Error('CDP 命令超时: ' + method)); }, 30000);
    pending.set(id, { resolve, timer });
    ws.send(JSON.stringify({ id, method, params, ...(sessionId ? { sessionId } : {}) }));
  });
}

const portGuardedSessions = new Set();

async function ensureSession(targetId) {
  if (sessions.has(targetId)) return sessions.get(targetId);
  const resp = await sendCDP('Target.attachToTarget', { targetId, flatten: true });
  if (resp.result?.sessionId) {
    const sid = resp.result.sessionId;
    sessions.set(targetId, sid);
    try {
      await sendCDP('Fetch.enable', { patterns: [
        { urlPattern: `http://127.0.0.1:${chromePort}/*`, requestStage: 'Request' },
        { urlPattern: `http://localhost:${chromePort}/*`, requestStage: 'Request' },
      ] }, sid);
      portGuardedSessions.add(sid);
    } catch {}
    return sid;
  }
  throw new Error('attach 失败');
}

async function waitForLoad(sessionId, timeoutMs = 15000) {
  await sendCDP('Page.enable', {}, sessionId);
  return new Promise((resolve) => {
    let resolved = false;
    const timer = setTimeout(() => { if (!resolved) { resolved = true; resolve('timeout'); } }, timeoutMs);
    const interval = setInterval(async () => {
      try {
        const resp = await sendCDP('Runtime.evaluate', { expression: 'document.readyState', returnByValue: true }, sessionId);
        if (resp.result?.result?.value === 'complete' && !resolved) { resolved = true; clearTimeout(timer); clearInterval(interval); resolve('complete'); }
      } catch {}
    }, 500);
  });
}

async function readBody(req) { let body = ''; for await (const chunk of req) body += chunk; return body; }

const server = http.createServer(async (req, res) => {
  const parsed = new URL(req.url, `http://localhost:${PORT}`);
  const pathname = parsed.pathname;
  const q = Object.fromEntries(parsed.searchParams);
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  try {
    if (pathname === '/health') { res.end(JSON.stringify({ status: 'ok', connected: !!(ws && ws.readyState === WS.OPEN || ws.readyState === 1), sessions: sessions.size, chromePort })); return; }
    await connect();

    if (pathname === '/targets') { const r = await sendCDP('Target.getTargets'); res.end(JSON.stringify(r.result.targetInfos.filter(t => t.type === 'page'), null, 2)); }
    else if (pathname === '/new') {
      const url = q.url || 'about:blank';
      const r = await sendCDP('Target.createTarget', { url, background: true });
      if (url !== 'about:blank') try { const sid = await ensureSession(r.result.targetId); await waitForLoad(sid); } catch {}
      res.end(JSON.stringify({ targetId: r.result.targetId }));
    }
    else if (pathname === '/close') { await sendCDP('Target.closeTarget', { targetId: q.target }); sessions.delete(q.target); res.end(JSON.stringify({ ok: true })); }
    else if (pathname === '/navigate') { const sid = await ensureSession(q.target); await sendCDP('Page.navigate', { url: q.url }, sid); await waitForLoad(sid); res.end(JSON.stringify({ ok: true })); }
    else if (pathname === '/back') { const sid = await ensureSession(q.target); await sendCDP('Runtime.evaluate', { expression: 'history.back()' }, sid); await waitForLoad(sid); res.end(JSON.stringify({ ok: true })); }
    else if (pathname === '/info') { const sid = await ensureSession(q.target); const r = await sendCDP('Runtime.evaluate', { expression: 'JSON.stringify({title:document.title,url:location.href,ready:document.readyState})', returnByValue: true }, sid); res.end(r.result?.result?.value || '{}'); }
    else if (pathname === '/eval') {
      const sid = await ensureSession(q.target);
      const body = await readBody(req);
      const r = await sendCDP('Runtime.evaluate', { expression: body || q.expr || 'document.title', returnByValue: true, awaitPromise: true }, sid);
      if (r.result?.result?.value !== undefined) res.end(JSON.stringify({ value: r.result.result.value }));
      else if (r.result?.exceptionDetails) { res.statusCode = 400; res.end(JSON.stringify({ error: r.result.exceptionDetails.text })); }
      else res.end(JSON.stringify(r.result));
    }
    else if (pathname === '/click') {
      const sid = await ensureSession(q.target);
      const sel = await readBody(req);
      if (!sel) { res.statusCode = 400; res.end(JSON.stringify({ error: '需要 CSS 选择器' })); return; }
      const r = await sendCDP('Runtime.evaluate', { expression: `(()=>{const el=document.querySelector(${JSON.stringify(sel)});if(!el)return{error:'未找到'};el.scrollIntoView({block:'center'});el.click();return{clicked:true,tag:el.tagName,text:(el.textContent||'').slice(0,100)}})()`, returnByValue: true, awaitPromise: true }, sid);
      res.end(JSON.stringify(r.result?.result?.value || r.result));
    }
    else if (pathname === '/clickAt') {
      const sid = await ensureSession(q.target);
      const sel = await readBody(req);
      const r1 = await sendCDP('Runtime.evaluate', { expression: `(()=>{const el=document.querySelector(${JSON.stringify(sel)});if(!el)return{error:'未找到'};el.scrollIntoView({block:'center'});const r=el.getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2}})()`, returnByValue: true, awaitPromise: true }, sid);
      const coord = r1.result?.result?.value;
      if (!coord || coord.error) { res.statusCode = 400; res.end(JSON.stringify(coord || r1.result)); return; }
      await sendCDP('Input.dispatchMouseEvent', { type: 'mousePressed', x: coord.x, y: coord.y, button: 'left', clickCount: 1 }, sid);
      await sendCDP('Input.dispatchMouseEvent', { type: 'mouseReleased', x: coord.x, y: coord.y, button: 'left', clickCount: 1 }, sid);
      res.end(JSON.stringify({ clicked: true, x: coord.x, y: coord.y }));
    }
    else if (pathname === '/scroll') {
      const sid = await ensureSession(q.target);
      const y = parseInt(q.y || '3000');
      const dir = q.direction || 'down';
      let js = dir === 'top' ? 'window.scrollTo(0,0)' : dir === 'bottom' ? 'window.scrollTo(0,document.body.scrollHeight)' : dir === 'up' ? `window.scrollBy(0,-${y})` : `window.scrollBy(0,${y})`;
      await sendCDP('Runtime.evaluate', { expression: js, returnByValue: true }, sid);
      await new Promise(r => setTimeout(r, 800));
      res.end(JSON.stringify({ ok: true }));
    }
    else if (pathname === '/screenshot') {
      const sid = await ensureSession(q.target);
      const fmt = q.format || 'png';
      const r = await sendCDP('Page.captureScreenshot', { format: fmt, quality: fmt === 'jpeg' ? 80 : undefined }, sid);
      if (q.file) { fs.writeFileSync(q.file, Buffer.from(r.result.data, 'base64')); res.end(JSON.stringify({ saved: q.file })); }
      else { res.setHeader('Content-Type', 'image/' + fmt); res.end(Buffer.from(r.result.data, 'base64')); }
    }
    else { res.statusCode = 404; res.end(JSON.stringify({ error: '未知端点' })); }
  } catch (e) { res.statusCode = 500; res.end(JSON.stringify({ error: e.message })); }
});

async function main() {
  const s = net.createServer();
  const available = await new Promise(r => { s.once('error', () => r(false)); s.once('listening', () => { s.close(); r(true); }); s.listen(PORT, '127.0.0.1'); });
  if (!available) { try { const ok = await new Promise(r => http.get(`http://127.0.0.1:${PORT}/health`, { timeout: 2000 }, res => { let d = ''; res.on('data', c => d += c); res.on('end', () => r(d.includes('"ok"'))); }).catch(() => false); if (ok) { console.log(`[CDP Proxy] 已有实例运行在端口 ${PORT}，退出`); process.exit(0); } } catch {} console.error(`端口 ${PORT} 已被占用`); process.exit(1); }
  server.listen(PORT, () => { console.log(`[CDP Proxy] 运行在 http://localhost:${PORT}`); connect().catch(e => console.error('[CDP Proxy] 初始连接失败:', e.message)); });
}
process.on('uncaughtException', e => console.error('[CDP Proxy]', e.message));
process.on('unhandledRejection', e => console.error('[CDP Proxy]', e?.message || e));
main();
