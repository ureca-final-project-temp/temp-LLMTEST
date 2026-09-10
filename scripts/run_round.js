'use strict';

// Runs the FAQ answer-generation prompt (README 9-1) against all 9 candidate models
// for one round (easy/medium/hard/rag), and appends raw results to results/raw/<round>.jsonl
//
// Usage: node scripts/run_round.js easy
//        node scripts/run_round.js medium
//        node scripts/run_round.js hard
//        node scripts/run_round.js rag

const fs = require('fs');
const path = require('path');
const { parseCsvObjects } = require('./lib/csv');
const { chatOnce } = require('./lib/ollama');

const ROOT = path.resolve(__dirname, '..');
const DATA_DIR = path.join(ROOT, 'data');
const RAW_DIR = path.join(ROOT, 'results', 'raw');

const MODELS = [
  'qwen3:0.6b',
  'qwen3:1.7b',
  'qwen3:4b',
  'qwen3:8b',
  'exaone3.5:2.4b',
  'exaone3.5:7.8b',
  'gemma3:270m',
  'gemma3:1b',
  'gemma3:4b',
];

const SYSTEM_PROMPT = `당신은 통신사 고객센터 챗봇입니다. 아래 제공된 FAQ 내용만 근거로 사용자 질문에 친절하고 자연스러운 한국어 존댓말로 답변하세요.

규칙:
1. 제공된 FAQ에 없는 내용(금액, 기간, 절차 등)을 추가하거나 추측하지 마세요.
2. 제공된 FAQ가 없거나, 질문과 무관하거나, 서로 모순되는 경우 솔직하게 답변할 수 없다고 안내하세요.
3. 여러 FAQ가 제공된 경우 실제로 질문과 관련된 FAQ만 사용하고, 관련 없는 FAQ는 무시하세요.
4. 답변은 아래 JSON 형식으로만 출력하세요. 다른 텍스트를 앞뒤에 추가하지 마세요.

출력 형식:
{
  "answer": "사용자에게 보여줄 답변 텍스트",
  "grounded": true | false,
  "used_faq_ids": ["FAQ-028"]
}

- answer: 실제 답변 문장
- grounded: 제공된 FAQ만으로 충분히 답할 수 있었는가 (모르겠다고 답했다면 false)
- used_faq_ids: 답변에 실제로 사용한 FAQ ID 목록 (없으면 빈 배열)`;

function loadFaqMap() {
  const text = fs.readFileSync(path.join(DATA_DIR, 'faq.csv'), 'utf8');
  const rows = parseCsvObjects(text);
  const map = new Map();
  for (const r of rows) {
    map.set(r['FAQ ID'], { category: r['카테고리'], question: r['FAQ 질문'], answer: r['FAQ 답변'] });
  }
  return map;
}

function buildContextBlockFromFaqIds(idsField, faqMap) {
  const ids = idsField.split(';').map((s) => s.trim()).filter(Boolean);
  if (ids.length === 0) return '(제공된 FAQ 없음)';
  return ids
    .map((id) => {
      const faq = faqMap.get(id);
      if (!faq) return `${id}: (원문 조회 실패)`;
      return `${id}: ${faq.category} - Q: ${faq.question} A: ${faq.answer}`;
    })
    .join('\n');
}

const ROUND_CONFIG = {
  easy: { file: 'faq_easy.csv', excludeIntent: 'MAP_API', idField: 'ID', queryField: '사용자 질문', gtField: 'Primary GT', intentField: '처리 의도' },
  medium: { file: 'faq_medium.csv', excludeIntent: 'MAP_API', idField: 'ID', queryField: '사용자 질문', gtField: 'Primary GT', intentField: '처리 의도' },
  hard: { file: 'faq_hard.csv', excludeIntent: 'MAP_API', idField: 'ID', queryField: '사용자 질문', gtField: 'Primary GT', intentField: '처리 의도' },
};

async function runFaqRound(roundName) {
  const cfg = ROUND_CONFIG[roundName];
  const faqMap = loadFaqMap();
  const text = fs.readFileSync(path.join(DATA_DIR, 'eval_sets', cfg.file), 'utf8');
  const rows = parseCsvObjects(text).filter((r) => r[cfg.intentField] !== cfg.excludeIntent);

  fs.mkdirSync(RAW_DIR, { recursive: true });
  const outPath = path.join(RAW_DIR, `faq_${roundName}.jsonl`);
  const outStream = fs.createWriteStream(outPath, { flags: 'a' });

  console.log(`[${roundName}] ${rows.length} cases x ${MODELS.length} models = ${rows.length * MODELS.length} calls`);

  for (const row of rows) {
    const id = row[cfg.idField];
    const query = row[cfg.queryField];
    const contextBlock = buildContextBlockFromFaqIds(row[cfg.gtField], faqMap);
    const userPrompt = `[사용자 질문]\n${query}\n\n[참고 FAQ]\n${contextBlock}`;

    for (const model of MODELS) {
      process.stdout.write(`  ${id} x ${model} ... `);
      const result = await chatOnce(model, SYSTEM_PROMPT, userPrompt);
      const record = {
        round: roundName,
        id,
        model,
        query,
        contextBlock,
        ...result,
      };
      outStream.write(JSON.stringify(record) + '\n');
      if (result.ok) {
        console.log(`ok (${result.latencyMs}ms, format=${result.formatValid})`);
      } else {
        console.log(`FAILED: ${result.error}`);
      }
    }
  }

  outStream.end();
  console.log(`[${roundName}] done -> ${outPath}`);
}

async function main() {
  const roundName = process.argv[2];
  if (!ROUND_CONFIG[roundName]) {
    console.error(`Usage: node scripts/run_round.js <${Object.keys(ROUND_CONFIG).join('|')}>`);
    process.exit(1);
  }
  await runFaqRound(roundName);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
