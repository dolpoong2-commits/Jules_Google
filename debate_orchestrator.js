// Node 18+, Playwright 기반 다중 AI 토론 오케스트레이터
// - 로컬 UI 서버(ui-server.js)로 시나리오/서비스 설정 관리
// - seed.md의 <선택> 값을 읽어 해당 시나리오로 토론 주제 자동 설정
// 실행:
//   - npm run ui       (설정 UI 실행)
//   - npm run dry      (프롬프트 생성 미리보기)
//   - npm start        (실제 토론 실행)

import fs from "node:fs/promises";
import path from "node:path";
import { chromium } from "playwright";

const PERSIST_DIR = path.resolve("./.profiles");
const SERVICES_PATH = "./services.json";
const SEED_PATH = "./seed.md";

const TIMEOUT_SEND   = 30_000;
const TIMEOUT_REPLY  = 90_000;
const ROUND_PAUSE    = 3_000;

// =============================================================================
// 유틸리티 함수
// =============================================================================

// seed.md에서 특정 태그 블록의 내용을 추출
function getBlock(text, tag, required = true) {
  const re = new RegExp(`<${tag}>([\\s\\S]*?)<\\/${tag}>`, "i");
  const match = text.match(re);
  if (!match) {
    if (required) throw new Error(`seed.md에서 <${tag}> 블록을 찾을 수 없습니다.`);
    return "";
  }
  return match[1].trim();
}

// seed.md의 <선택> 블록에서 시나리오 ID를 추출
function getSelectedId(text) {
  const block = getBlock(text, "선택");
  const match = block.match(/(\d+)/);
  if (!match) throw new Error("<선택> 블록에서 시나리오 번호를 찾지 못했습니다.");
  return +match[1];
}

// 보이는 첫 번째 로케이터를 선택
async function pickLocator(page, selectors) {
  for (const sel of selectors) {
    const loc = page.locator(sel).first();
    if (await loc.isVisible().catch(() => false)) {
      return loc;
    }
  }
  return null;
}

// 입력창에 프롬프트 전송
async function sendPrompt(page, svc, text) {
  const input = await pickLocator(page, svc.inputSelectors);
  if (!input) throw new Error(`[${svc.name}] 입력창 selector 불일치`);
  await input.click({ timeout: TIMEOUT_SEND });
  await page.keyboard.down("Control"); await page.keyboard.press("KeyA"); await page.keyboard.up("Control");
  await page.keyboard.press("Backspace");
  await input.type(text, { delay: 10 });

  if (svc.send === "enter") {
    await page.keyboard.press("Enter");
  } else if (svc.send && svc.send.selector) {
    await page.locator(svc.send.selector).click();
  }
}

// 마지막 답변 수집
async function readLastAnswer(page, svc) {
  for (const sel of svc.lastMsgSelectors) {
    const nodes = page.locator(sel);
    if ((await nodes.count().catch(() => 0)) > 0) {
      const txt = (await nodes.last().innerText({ timeout: 10_000 }).catch(() => "")).trim();
      if (txt) return txt;
    }
  }
  const all = await page.locator("body").innerText().catch(() => "");
  return (all || "").slice(-4000);
}

// 답변 병합 (규칙 기반)
function mergeAnswers(answerMap) {
  const merged = [];
  const seen = new Set();
  for (const text of Object.values(answerMap)) {
    const lines = (text || "").split(/\r?\n/).map(s => s.trim()).filter(Boolean);
    for (let s of lines) {
      s = s.replace(/^[-•*]\s*/, "");
      if (s.length < 10) continue;
      const key = s.toLowerCase();
      if (!seen.has(key)) {
        seen.add(key);
        merged.push(`- ${s}`);
      }
    }
  }
  return merged.join("\n");
}

// 교차 검증 프롬프트 생성
function makeCrossPrompt(answerMap, selfName) {
  const others = Object.entries(answerMap)
    .filter(([n]) => n !== selfName)
    .map(([n, t]) => `● ${n} 제안: ${t.slice(0, 300)}...`)
    .join("\n");
  return `다른 AI들의 제안 요약입니다:\n${others}\n\n위 내용을 근거로 <공통_절차>의 R2(교차 검증) 과제를 수행하세요.`;
}

// =============================================================================
// 메인 오케스트레이션 로직
// =============================================================================
async function main() {
  const isDryRun = process.argv.includes('--dry-run');
  const services = JSON.parse(await fs.readFile(SERVICES_PATH, "utf-8"));
  const seedText = await fs.readFile(SEED_PATH, "utf-8");
  const selectedId = getSelectedId(seedText);

  console.log(`[INFO] 선택된 시나리오: ${selectedId}`);

  // --- 프롬프트 구성 ---
  const scenarioContext = getBlock(seedText, `시나리오_${selectedId}_컨텍스트`);
  const scenarioRequest = getBlock(seedText, `시나리오_${selectedId}_요청`);

  const promptR0 = `
<전체 컨텍스트>
${getBlock(seedText, '설정')}
${getBlock(seedText, '공통_절차')}
${getBlock(seedText, '형식_규칙')}
${getBlock(seedText, '품질_원칙')}
${getBlock(seedText, '출력_요구')}
<선택된 시나리오 컨텍스트>
${scenarioContext}
</전체 컨텍스트>
위 모든 내용을 숙지했습니다. 첫 번째 요청을 기다리겠습니다.`.trim();

  const promptR1 = `첫 번째 과제입니다. <공통_절차>의 R1(1차 제안)과 아래의 <시나리오 요청>을 참고하여 제안을 시작하세요.\n\n<시나리오 요청>\n${scenarioRequest}`;

  if (isDryRun) {
    console.log("============== DRY RUN ==============");
    console.log("R0 (초기 컨텍스트) 프롬프트:\n\n" + promptR0);
    console.log("\n-------------------------------------\n");
    console.log("R1 (1차 제안) 프롬프트:\n\n" + promptR1);
    console.log("\n=====================================");
    return;
  }

  // --- 브라우저 실행 ---
  const pages = {};
  console.log("[INFO] 서비스별 브라우저 컨텍스트를 실행합니다...");
  await fs.mkdir(PERSIST_DIR, { recursive: true });

  for (const svc of services) {
    const profileDir = svc.profileDir || path.join(PERSIST_DIR, svc.name.replace(/[\s/]/g, '_'));
    const launchOptions = {
      headless: false,
      args: ["--disable-dev-shm-usage", "--disable-blink-features=AutomationControlled", "--start-maximized"],
      userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
      viewport: null,
      channel: svc.channel || undefined,
    };
    console.log(`[INFO] '${svc.name}' 서비스 실행... (프로필: ${profileDir}, 채널: ${svc.channel || '기본'})`);
    const context = await chromium.launchPersistentContext(profileDir, launchOptions);
    const page = context.pages().length ? context.pages()[0] : await context.newPage();
    pages[svc.name] = page;
    await page.goto(svc.url, { waitUntil: "domcontentloaded", timeout: 60_000 });
  }

  console.log("\n[ACTION] 모든 브라우저 창이 준비되었습니다. 필요시 각 서비스에 로그인한 후, 이 터미널로 돌아와 Enter 키를 누르세요...");
  process.stdin.setRawMode(true);
  process.stdin.resume();
  await new Promise(r => process.stdin.once("data", r));
  process.stdin.setRawMode(false);

  // --- 토론 라운드 진행 ---
  console.log("\n[ROUND 0] 컨텍스트 주입 시작...");
  for (const svc of services) await sendPrompt(pages[svc.name], svc, promptR0);
  await new Promise(r => setTimeout(r, ROUND_PAUSE));

  console.log("\n[ROUND 1] 1차 제안 요청 시작...");
  for (const svc of services) await sendPrompt(pages[svc.name], svc, promptR1);

  console.log("\n[INFO] 답변 수집 중... (최대 90초 대기)");
  let answersR1 = {};
  const deadline1 = Date.now() + TIMEOUT_REPLY;
  while (Date.now() < deadline1 && Object.keys(answersR1).length < services.length) {
    for (const svc of services) {
      if (!answersR1[svc.name]) {
        answersR1[svc.name] = await readLastAnswer(pages[svc.name], svc).catch(() => "");
      }
    }
    await new Promise(r => setTimeout(r, 2000));
  }

  console.log("\n[ROUND 2] 교차 검증 시작...");
  for (const svc of services) {
    const crossPrompt = makeCrossPrompt(answersR1, svc.name);
    await sendPrompt(pages[svc.name], svc, crossPrompt);
  }

  console.log("\n[INFO] 교차 검증 답변 수집 중...");
  let answersR2 = {};
  const deadline2 = Date.now() + TIMEOUT_REPLY;
  while (Date.now() < deadline2 && Object.keys(answersR2).length < services.length) {
    for (const svc of services) {
      if (!answersR2[svc.name]) {
        answersR2[svc.name] = await readLastAnswer(pages[svc.name], svc).catch(() => "");
      }
    }
    await new Promise(r => setTimeout(r, 2000));
  }

  console.log("\n[ROUND 3] 합의 초안 생성 및 피드백 요청...");
  const mergedR1 = mergeAnswers(answersR1);
  const mergedR2 = mergeAnswers(answersR2);
  const draft = `# 합의 초안\n\n## 1차 제안 요약\n${mergedR1}\n\n## 교차 검증 요약\n${mergedR2}`;
  const promptR3 = `다음은 지금까지의 논의를 종합한 합의 초안입니다. <공통_절차>의 R3(합의 초안) 과제를 참고하여, 이 초안을 기반으로 완전한 보고서 초안을 작성해주세요.\n\n${draft.slice(0, 3500)}`;
  for (const svc of services) await sendPrompt(pages[svc.name], svc, promptR3);

  console.log("\n[INFO] 최종 초안 수집 중...");
  let answersR3 = {};
  const deadline3 = Date.now() + TIMEOUT_REPLY;
  while (Date.now() < deadline3 && Object.keys(answersR3).length < services.length) {
    for (const svc of services) {
      if (!answersR3[svc.name]) {
        answersR3[svc.name] = await readLastAnswer(pages[svc.name], svc).catch(() => "");
      }
    }
    await new Promise(r => setTimeout(r, 2000));
  }

  // --- 최종 결과물 생성 ---
  console.log("\n[COMPLETE] 최종 결과물 생성 중...");
  const outputFile = getBlock(seedText, '설정').match(/output_file:\s*(\S+)/)?.[1] || 'final_business_plan.md';
  const finalDoc = [
    `# 최종 보고서 (시나리오: ${selectedId})`,
    "## 1차 제안 (개별)",
    ...Object.entries(answersR1).map(([n, t]) => `### ${n}\n${t}`),
    "## 2차 교차 검증 (개별)",
    ...Object.entries(answersR2).map(([n, t]) => `### ${n}\n${t}`),
    "## 3차 종합 초안 (개별)",
    ...Object.entries(answersR3).map(([n, t]) => `### ${n}\n${t}`),
  ].join("\n\n---\n\n");

  await fs.writeFile(outputFile, finalDoc, "utf-8");
  console.log(`\n✅ 완료: ${outputFile} 파일이 생성되었습니다.`);
  console.log("브라우저 창은 검토를 위해 열어두었습니다. 수동으로 닫아주세요.");
}

main().catch(e => console.error("[FATAL ERROR]", e));