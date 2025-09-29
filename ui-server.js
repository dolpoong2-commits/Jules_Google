// ui-server.js — 로컬 설정 UI 서버
import express from "express";
import fs from "node:fs/promises";

const app = express();
const PORT = 3000;
app.use(express.json());
app.use(express.static("public"));

const SEED_PATH = "./seed.md";
const SERVICES_PATH = "./services.json";

// --- seed.md 파싱 유틸
const readSeed = async () => await fs.readFile(SEED_PATH, "utf-8");
function getBlock(text, tag, required = true) {
  const re = new RegExp(`<${tag}>[\\s\\S]*?<\\/${tag}>`, "i");
  const m = text.match(re);
  if (!m) {
    if (required) throw new Error(`seed.md에서 <${tag}> 블록을 찾을 수 없습니다.`);
    return "";
  }
  return { raw: m[0], inner: m[0].replace(new RegExp(`^<${tag}>\\s*`, "i"), "").replace(new RegExp(`\\s*<\\/${tag}>$`, "i"), "").trim() };
}
function setSelectionBlock(text, newId) {
  const { raw, inner } = getBlock(text, "선택");
  // 첫 번째 정수만 교체
  const replacedInner = inner.replace(/(\d+)/, String(newId));
  return text.replace(raw, `<선택>\n${replacedInner}\n</선택>`);
}
function getScenarioMap(text) {
  const ctxRe = /<시나리오_(\d+)_컨텍스트>([\s\S]*?)<\/시나리오_\1_컨텍스트>/g;
  const reqRe = /<시나리오_(\d+)_요청>([\s\S]*?)<\/시나리오_\1_요청>/g;
  const ctx = new Map(), req = new Map();
  let m;
  while ((m = ctxRe.exec(text)) !== null) ctx.set(+m[1], m[2].trim());
  while ((m = reqRe.exec(text)) !== null) req.set(+m[1], m[2].trim());
  const ids = [...new Set([...ctx.keys(), ...req.keys()])];
  return ids.map(id => ({
    id,
    title: `시나리오 ${id}`,
    contextFirstLine: (ctx.get(id) || "").split(/\r?\n/).map(s=>s.trim()).filter(Boolean)[0] || "",
  })).sort((a,b)=>a.id-b.id);
}
function getSelectedId(text) {
  const { inner } = getBlock(text, "선택");
  const m = inner.match(/(\d+)/);
  if (!m) throw new Error("<선택> 블록에서 시나리오 번호를 찾지 못했습니다.");
  return +m[1];
}
function appendScenario(text, ctx, req) {
  const nextId = (getScenarioMap(text).at(-1)?.id || 0) + 1;
  const block =
`
################################################################################
# 시나리오 ${nextId}
################################################################################
<시나리오_${nextId}_컨텍스트>
${ctx.trim()}
</시나리오_${nextId}_컨텍스트>
<시나리오_${nextId}_요청>
${req.trim()}
</시나리오_${nextId}_요청>\n`;
  return { newText: text + block, newId: nextId };
}

// --- API
app.get("/api/seed/selection", async (_req, res) => {
  try {
    const text = await readSeed();
    const options = getScenarioMap(text);
    const selectedId = getSelectedId(text);
    res.json({ selectedId, options });
  } catch (e) {
    res.status(500).json({ error: String(e.message || e) });
  }
});

app.post("/api/seed/selection", async (req, res) => {
  try {
    const { selectedId } = req.body;
    if (!Number.isInteger(selectedId) || selectedId < 1) return res.status(400).json({ error: "selectedId 정수 필요" });
    const text = await readSeed();
    const options = getScenarioMap(text).map(o=>o.id);
    if (!options.includes(selectedId)) return res.status(400).json({ error: "존재하지 않는 시나리오 번호" });
    const newText = setSelectionBlock(text, selectedId);
    await fs.writeFile(SEED_PATH, newText, "utf-8");
    res.json({ ok: true });
  } catch (e) { res.status(500).json({ error: String(e.message || e) }); }
});

app.post("/api/seed/scenario", async (req, res) => {
  try {
    const { context, request } = req.body;
    if (!context || !request) return res.status(400).json({ error: "context와 request가 필요합니다." });
    const text = await readSeed();
    const { newText, newId } = appendScenario(text, context, request);
    await fs.writeFile(SEED_PATH, newText, "utf-8");
    res.json({ ok: true, newId });
  } catch (e) { res.status(500).json({ error: String(e.message || e) }); }
});

app.get("/api/services", async (_req, res) => {
  try {
    const raw = await fs.readFile(SERVICES_PATH, "utf-8");
    res.json(JSON.parse(raw));
  } catch (e) { res.status(500).json({ error: String(e.message || e) }); }
});

app.post("/api/services", async (req, res) => {
  try {
    const services = req.body;
    if (!Array.isArray(services)) return res.status(400).json({ error: "배열이어야 합니다." });
    if (services.length < 1 || services.length > 8) return res.status(400).json({ error: "서비스 개수는 1~8개" });

    // 기본 셀렉터를 보강
    const defaultInput = ["div[contenteditable='true']", "textarea[aria-label]", "textarea"];
    const defaultLast  = ["div[data-message-author-role='assistant']", "div.markdown", "article"];

    const normalized = services.map(s => ({
      name: s.name?.trim() || "Service",
      url: s.url?.trim() || "",
      channel: s.channel || undefined,
      profileDir: s.profileDir || undefined,
      inputSelectors: s.inputSelectors?.length ? s.inputSelectors : defaultInput,
      send: s.send || "enter",
      lastMsgSelectors: s.lastMsgSelectors?.length ? s.lastMsgSelectors : defaultLast
    }));

    await fs.writeFile(SERVICES_PATH, JSON.stringify(normalized, null, 2), "utf-8");
    res.json({ ok: true, count: normalized.length });
  } catch (e) { res.status(500).json({ error: String(e.message || e) }); }
});

app.listen(PORT, () => {
  console.log(`UI 서버 실행: http://localhost:${PORT}`);
});