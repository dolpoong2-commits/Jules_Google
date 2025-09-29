// Node 18+, Playwright 기반 8창 토론 오케스트레이터
// - 공식 AI API 미사용. 브라우저 DOM 자동화로 입력/출력
// - 라운드 설계: R0 설정 → R1 제안 → R2 교차검증 → R3 합의초안 → R4 리스크/로드맵 → Final 마크다운 출력
// - 셀렉터는 services.json에서 관리(사이트 변경시 해당 항목만 수정)
// 실행: node debate_orchestrator.js

import fs from "node:fs/promises";
import path from "node:path";
import { chromium } from "playwright";

const PERSIST_DIR = path.resolve("./.profiles");     // 로그인 세션 유지 폴더
const SERVICES    = JSON.parse(await fs.readFile("./services.json", "utf-8"));
const SEED        = await fs.readFile("./seed.md", "utf-8");

const TIMEOUT_SEND   = 30_000;  // 각 전송 대기
const TIMEOUT_REPLY  = 90_000;  // 답변 수집 대기 (사이트마다 조정)
const ROUND_PAUSE    = 3_000;   // 라운드 간 짧은 휴식

// 유틸: locator 후보들 중 첫번째 존재하는 셀렉터를 찾음
async function pickLocator(page, selectors) {
  for (const sel of selectors) {
    const loc = page.locator(sel);
    if (await loc.first().count().catch(() => 0)) return loc.first();
  }
  return null;
}

// 입력창에 텍스트 쓰고 전송(enter 또는 버튼 클릭)
async function sendPrompt(page, svc, text) {
  const input = await pickLocator(page, svc.inputSelectors);
  if (!input) throw new Error(`[${svc.name}] 입력창 selector 불일치`);
  // 포커스 → 기존 내용 제거 → 입력
  await input.click({ timeout: TIMEOUT_SEND });
  // 일부 사이트는 contenteditable, 일부는 textarea이므로 모두 커버
  await page.keyboard.down("Control"); await page.keyboard.press("KeyA"); await page.keyboard.up("Control");
  await page.keyboard.press("Backspace");
  await input.type(text, { delay: 10 });

  if (svc.send === "enter") {
    await page.keyboard.press("Enter");
  } else if (svc.send && svc.send.selector) {
    await page.locator(svc.send.selector).click();
  }
}

// 마지막 어시스턴트 메시지 텍스트 수집(여러 후보 셀렉터 시도)
async function readLastAnswer(page, svc) {
  for (const sel of svc.lastMsgSelectors) {
    const nodes = page.locator(sel);
    const n = await nodes.count().catch(() => 0);
    if (n > 0) {
      // 가장 마지막 요소의 textContent
      const txt = (await nodes.nth(n - 1).innerText({ timeout: 10_000 }).catch(() => "")).trim();
      if (txt) return txt;
    }
  }
  // fallback: 페이지 전체에서 최근 2~3개 말풍선 후보 긁기
  const all = await page.locator("body").innerText().catch(() => "");
  return (all || "").slice(-4000);
}

// 단순 병합 + 중복 제거(로컬 규칙기반, API 없이)
function mergeAnswers(answerMap) {
  // answerMap: { name: text }
  const merged = [];
  const seen = new Set();
  for (const [name, text] of Object.entries(answerMap)) {
    const lines = (text || "").split(/\r?\n/).map(s => s.trim()).filter(Boolean);
    for (let s of lines) {
      // 노이즈 제거(머리말/푸터/중복문구)
      s = s.replace(/^[-•*]\s*/, "");
      if (s.length < 3) continue;
      const key = s.toLowerCase();
      if (!seen.has(key)) { seen.add(key); merged.push(`- ${s}`); }
    }
  }
  return merged.join("\n");
}

// 교차검증 프롬프트 생성(상대 요약 + 반박/보강 유도)
function makeCrossPrompt(answerMap, selfName, maxChars = 1200) {
  const others = Object.entries(answerMap)
    .filter(([n]) => n !== selfName)
    .map(([n, t]) => `● ${n}: ${t.slice(0, 250)}...`)
    .join("\n");
  return `다른 7명의 제안 요약입니다:\n${others}\n\n위 내용을 근거로 다음을 수행하세요:\n1) 가장 취약한 가설 3개를 근거와 함께 반박\n2) 누락된 리스크 3개 추가\n3) 시장/기술/운영 관점에서 실행 우선순위 5개 제시(근거 포함)\n(800~1200자)`;
}

async function main() {
  // 1) 브라우저 준비(영구 프로필)
  await fs.mkdir(PERSIST_DIR, { recursive: true });
  const browser = await chromium.launchPersistentContext(PERSIST_DIR, {
    headless: false,
    args: [
      "--disable-dev-shm-usage",
      "--disable-blink-features=AutomationControlled",
      "--start-maximized",
    ],
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    viewport: { width: 1400, height: 900 }
  });

  // 2) 탭 준비
  const pages = {};
  for (const svc of SERVICES) {
    const page = await browser.newPage();
    pages[svc.name] = page;
    await page.goto(svc.url, { waitUntil: "domcontentloaded" });
    // 최초 1회 로그인은 사람이 직접 진행(세션 저장됨)
  }
  console.log("로그인이 필요하면 각 탭에서 먼저 로그인 후 Enter…");
  // 사용자가 로그인/쿠키 수락 등 마친 뒤 Enter
  process.stdin.setRawMode(true); process.stdin.resume();
  await new Promise(r => process.stdin.once("data", r));
  process.stdin.setRawMode(false);

  // === R0: 컨텍스트/규칙 주입 ===
  for (const svc of SERVICES) {
    await sendPrompt(pages[svc.name], svc, SEED);
  }
  await new Promise(r => setTimeout(r, ROUND_PAUSE));

  // === R1: 1차 제안 유도 ===
  const round1 = "위 컨텍스트 기반으로 1차 제안을 해주세요. (요약/시장/제품/기술/운영/재무/리스크를 불릿으로 500~800자)";
  for (const svc of SERVICES) {
    await sendPrompt(pages[svc.name], svc, round1);
  }

  // 답변 수집
  let answers = {};
  const deadline1 = Date.now() + TIMEOUT_REPLY;
  while (Date.now() < deadline1) {
    for (const svc of SERVICES) {
      if (answers[svc.name]) continue;
      answers[svc.name] = await readLastAnswer(pages[svc.name], svc).catch(() => "");
    }
    if (Object.values(answers).every(t => t && t.length > 50)) break;
    await new Promise(r => setTimeout(r, 2000));
  }

  // === R2: 교차검증 ===
  for (const svc of SERVICES) {
    const cross = makeCrossPrompt(answers, svc.name);
    await sendPrompt(pages[svc.name], svc, cross);
  }
  // 수집
  let crossAnswers = {};
  const deadline2 = Date.now() + TIMEOUT_REPLY;
  while (Date.now() < deadline2) {
    for (const svc of SERVICES) {
      if (crossAnswers[svc.name]) continue;
      crossAnswers[svc.name] = await readLastAnswer(pages[svc.name], svc).catch(() => "");
    }
    if (Object.values(crossAnswers).every(t => t && t.length > 50)) break;
    await new Promise(r => setTimeout(r, 2000));
  }

  // === R3: 합의 초안 생성(로컬 병합 알고리즘) ===
  const merged1 = mergeAnswers(answers);
  const merged2 = mergeAnswers(crossAnswers);
  const draft = `# 합의 초안 (v1)\n\n## 1차 제안 병합\n${merged1}\n\n## 교차검증 병합\n${merged2}\n`;

  // 각 창에 초안을 돌려 피드백 받기
  for (const svc of SERVICES) {
    await sendPrompt(pages[svc.name], svc,
      `다음 합의 초안을 검토하고, 명확한 “최종 사업계획 목차(10항)”와 “SRS 목차(12항)”를 제안하고 누락 항목을 보강:\n\n${draft.slice(0, 3500)}`);
  }
  let refine = {};
  const deadline3 = Date.now() + TIMEOUT_REPLY;
  while (Date.now() < deadline3) {
    for (const svc of SERVICES) {
      if (refine[svc.name]) continue;
      refine[svc.name] = await readLastAnswer(pages[svc.name], svc).catch(() => "");
    }
    if (Object.values(refine).every(t => t && t.length > 50)) break;
    await new Promise(r => setTimeout(r, 2000));
  }

  // === Final: 마크다운 정리 ===
  const finalDoc = [
    "# 최종 결과(자동 취합)",
    "## 서비스별 1차 제안",
    ...Object.entries(answers).map(([n, t]) => `### ${n}\n${t}`),
    "## 서비스별 교차검증",
    ...Object.entries(crossAnswers).map(([n, t]) => `### ${n}\n${t}`),
    "## 합의 초안 병합",
    draft,
    "## 최종 피드백",
    ...Object.entries(refine).map(([n, t]) => `### ${n}\n${t}`)
  ].join("\n\n");

  await fs.writeFile("./final_business_plan.md", finalDoc, "utf-8");
  console.log("완료: final_business_plan.md 생성");

  // 브라우저 유지(사후 검토용)
  // await browser.close();
}
main().catch(e => console.error(e));