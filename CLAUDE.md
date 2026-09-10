# CLAUDE.md — 작업 재개용 메모

이 프로젝트에서 다시 작업을 시작할 때 이 파일부터 읽으세요. 전체 방법론/설계 이유는 [`README.md`](README.md)에 있고, 이 파일은 **"지금 어디까지 했고 다음에 뭘 해야 하는지"**만 빠르게 파악하기 위한 진행 상황 스냅샷입니다.

## 마지막 작업일: 2026-09-11

## 지금까지 한 일

1. **테스트 대상 확정**: Qwen3(0.6B/1.7B/4B/8B), EXAONE 3.5(2.4B/7.8B), Gemma3(270M/1B/4B) 9개 모델, 전부 Ollama에 로컬 설치 완료
2. **평가 프레임워크 9개 영역 확정** + 프롬프트 템플릿 3종 확정 (README 5·9절)
3. **자동화 파이프라인 구축** — 모델 호출(Ollama API) → 결정론적 보조지표 → Judge 채점(Claude Code 헤드리스) → 결과 문서 자동 집계, 4단계 스크립트 (README 10절)
4. **FAQ 답변 생성 라운드 (Easy/Medium/Hard) 전부 실행 완료** ✅ — 각 9개 모델 × 9케이스, 결과는 `results/faq_{easy,medium,hard}_results.md`
5. **RAG 안정성 테스트를 유형당 3건(21건)→9건(63건)으로 확대**, 컨텍스트 개수(3/5/10개) 기준 Small/Medium/Large 3개 파일로 분리, 전용 파이프라인 스크립트 작성
6. **RAG 안정성 Small/Medium 라운드 실행 완료** ✅ — `results/faq_rag_stability_{small,medium}_results.md`

## 다음에 할 일 (우선순위 순)

1. **RAG 안정성 Large 라운드 실행**
   ```
   node scripts/run_rag_stability_round.js large
   node scripts/score_rag_stability.js large
   node scripts/judge_rag_stability_round.js large
   node scripts/aggregate_rag_stability_round.js large
   ```
2. **의도 분류 라운드 (항목 3·4)** — 데이터(`data/eval_sets/intent_classification.csv`, 113건)는 준비됐지만 **전용 러너 스크립트가 아직 없음** (RAG 안정성처럼 새로 만들어야 함 — FAQ 컨텍스트 없이 질문만 주고 3-way 분류, 채점은 결정론적 Confusion Matrix라 Judge 불필요)
3. **클러스터 라벨링 라운드 (항목 9)** — 데이터(`data/eval_sets/cluster_labeling.csv`, 20건→4그룹)는 준비됐지만 **전용 러너 스크립트가 아직 없음** (그룹별 라벨링 프롬프트, Judge로 라벨 정확도 채점)
4. 사람 채점 calibration set 확보 후 Judge 신뢰도 검증
5. Easy/Medium/Hard/RAG안정성 결과 문서의 `사람평가`/`사람 총평` 칸 검토

## 지금까지 나온 핵심 결과 (요약)

- **Qwen3 4B**가 Easy/Medium/Hard 전부 환각률 0%를 유지한 유일한 모델 (다만 속도가 제일 느림, 케이스당 7~20초)
- **Gemma3 4B**가 정확도-속도 밸런스 1순위 후보로 보임 (Hard 100% 정답률, Qwen3 4B보다 10배 빠름)
- **EXAONE 3.5(2.4B/7.8B)는 난이도가 올라갈수록 환각률이 계속 악화** (Hard에서 67%까지)
- Gemma3 270M/1B는 Hard에서 정답률 20%대로 사실상 실사용 어려움
- **반전**: FAQ 라운드에서 최고였던 Qwen3 0.6B가 RAG 안정성에서는 Small 14.3% → Medium 25.0%로 계속 하위권 — "단순 재진술"과 "무관/모순 컨텍스트 저항"은 완전히 다른 능력
- **RAG 안정성 Small/Medium 모두 Qwen3 8B가 1위** (85.7%/81.0%), **Gemma3 4B가 근소한 2위권** (76.2%/71.4%) — 이 둘이 유력 후보로 굳어지는 중. Gemma3 270M/1B는 Medium에서 0~10%대로 사실상 전멸

## 되짚어볼 것 (다음 세션에서 판단 근거로 참고)

- RAG 안정성이 최종 모델 선정의 핵심 기준이라고 합의함 (Easy/Medium/Hard는 진단용 보조 자료)
- 정답률 임계값(Judge 1~5점 중 4점 이상=정답)은 임의로 정한 것 — 필요하면 조정
- `gemma3:12b`가 계획에 없이 추가 설치되어 있음 (8B 캡 초과라 테스트 대상에서 제외한 상태, 포함하고 싶으면 알려달라고 했었음)
