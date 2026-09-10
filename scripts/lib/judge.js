'use strict';

const { spawnSync } = require('child_process');

const CLAUDE_BIN = process.platform === 'win32' ? 'claude.cmd' : 'claude';

function buildJudgePrompt({ faqQuestion, faqAnswer, userQuery, answer }) {
  return `당신은 통신사 FAQ 챗봇 답변을 채점하는 평가자입니다. 아래 정답 FAQ와 챗봇이 생성한 답변을 비교해서 채점하세요.

[정답 FAQ]
Q: ${faqQuestion}
A: ${faqAnswer}

[사용자 질문]
${userQuery}

[챗봇 생성 답변]
${answer}

채점 기준:
1. answer_accuracy: 생성 답변이 정답 FAQ의 핵심 정보를 빠짐없이 정확하게 담았는가 (1~5점, 5가 가장 정확)
2. faithful: 생성 답변이 정답 FAQ에 없는 내용을 추가하거나 지어내지 않았는가 (true/false)
3. hallucination: faithful이 false인 경우 구체적으로 어떤 문장/내용이 근거 없는지 한국어로 간단히 (근거 없는 내용이 없으면 빈 문자열)
4. expression_quality: 자연스러운 한국어 존댓말 상담 답변으로서의 품질 (1~5점, 자연스러움/명확성/친절성 종합)

챗봇 생성 답변이 비어있거나, 질문과 무관하거나, 형식 템플릿을 그대로 복사한 것처럼 실패작이어도 채점을 거부하지 말고 낮은 점수(예: 1점)로 반드시 아래 JSON 형식으로만 답하세요. 다른 텍스트, 설명, 마크다운 코드블록 없이 순수 JSON 객체 하나만 출력하세요.
{"answer_accuracy": 1-5, "faithful": true/false, "hallucination": "...", "expression_quality": 1-5}`;
}

function stripCodeFence(text) {
  const trimmed = text.trim();
  const fenceMatch = trimmed.match(/^```(?:json)?\s*([\s\S]*?)\s*```$/i);
  return fenceMatch ? fenceMatch[1].trim() : trimmed;
}

// Calls the Claude Code CLI headlessly (claude -p, prompt via stdin) as the fixed Judge.
function judgeAnswer(fields, { timeoutMs = 120000 } = {}) {
  const prompt = buildJudgePrompt(fields);
  const startedAt = Date.now();
  const res = spawnSync(CLAUDE_BIN, ['-p'], {
    input: prompt,
    encoding: 'utf8',
    timeout: timeoutMs,
    maxBuffer: 10 * 1024 * 1024,
    shell: process.platform === 'win32',
  });
  const latencyMs = Date.now() - startedAt;

  if (res.error) return { ok: false, error: `spawn_error: ${res.error.message}`, latencyMs };
  if (res.status !== 0) return { ok: false, error: `exit_${res.status}: ${(res.stderr || '').slice(0, 300)}`, latencyMs };

  const stdout = (res.stdout || '').trim();
  const cleaned = stripCodeFence(stdout);
  try {
    const scores = JSON.parse(cleaned);
    return { ok: true, scores, raw: stdout, latencyMs };
  } catch (e) {
    return { ok: false, error: `parse_error: ${e.message}`, raw: stdout, latencyMs };
  }
}

module.exports = { judgeAnswer, buildJudgePrompt };
