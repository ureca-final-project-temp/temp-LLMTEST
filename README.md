# LLM_Test — FAQ 챗봇용 로컬 LLM 선정 테스트

## 1. 프로젝트 개요

이 레포는 **FAQ 챗봇 시스템에 실제로 탑재할 로컬 LLM을 고르기 위한 기술 검증(기술 선정) 테스트 하네스**입니다.

우리 서비스는 사용자의 질문에 대해 적절한 FAQ를 찾아, 그 내용을 상황에 맞는 자연어로 답변해주는 챗봇입니다. 이 레포는 그중 **LLM이 담당하는 부분만** 떼어내어, 여러 후보 로컬 모델 중 어떤 모델이 실제 서비스에 적합한지 정량적으로 비교하는 것을 목적으로 합니다.

## 2. 테스트 범위와 원칙

- **임베딩 모델은 평가 대상이 아닙니다.** 벡터 검색(FAQ 매칭)은 이미 검증된 별도 축으로 보고, 이 레포는 매칭된 FAQ를 받아 LLM이 무엇을 하는지만 평가합니다.
- **테스트 대상(후보) 모델은 로컬 전용입니다.** 벡터DB·임베딩DB·외부 API를 전혀 사용하지 않고, Ollama로 구동되는 무료/오픈소스 로컬 모델만 후보로 둡니다.
- **채점(Judge)에는 외부 API 사용이 허용됩니다.** "외부 API를 쓰지 않는다"는 원칙은 서비스 품질을 결정하는 요소(=후보 LLM)에 한정되며, 서비스 품질을 판단만 하는 도구(=채점자)는 예외입니다. 이 레포에서는 Claude Code를 헤드리스로 호출해 Judge로 사용하며, 이는 별도 API 결제 없이 기존 Claude Pro 사용량 안에서 처리합니다 (평가 데이터 규모가 작아 충분함).

## 3. 왜 이 테스트가 필요한가

로컬 오픈소스 모델은 크기·학습 데이터 구성에 따라 다음이 크게 갈립니다.

- FAQ 원문을 자연스러운 한국어 상담 답변으로 재구성하는 능력
- 주어진 근거 없이 정보를 지어내는(환각) 경향
- 사용자 의도를 정확히 분류하는 능력
- 지정된 출력 포맷을 안정적으로 지키는 능력
- 실제 챗봇에 쓸 수 있을 만큼의 응답 속도

이 중 어떤 것도 이론적 스펙(파라미터 수)만으로는 판단할 수 없기 때문에, 동일한 데이터·동일한 기준으로 직접 돌려보고 비교합니다.

## 4. 테스트 대상 모델

가장 낮은 파라미터부터 최대 8B까지, 3개 모델 패밀리 총 9개 모델을 비교합니다.

| 패밀리 | 크기 | Ollama 태그 |
|---|---|---|
| Qwen3 | 0.6B | `qwen3:0.6b` |
| Qwen3 | 1.7B | `qwen3:1.7b` |
| Qwen3 | 4B | `qwen3:4b` |
| Qwen3 | 8B | `qwen3:8b` |
| EXAONE 3.5 | 2.4B | `exaone3.5:2.4b` |
| EXAONE 3.5 | 7.8B | `exaone3.5:7.8b` |
| Gemma3 | 270M | `gemma3:270m` |
| Gemma3 | 1B | `gemma3:1b` |
| Gemma3 | 4B | `gemma3:4b` |

> Gemma3 270M은 "가장 낮은 파라미터부터"라는 조건에 맞춰 포함했습니다. 범위를 8개로 줄이고 싶다면 이 모델을 제외하면 됩니다.

## 5. 평가 프레임워크 (9개 영역)

| # | 평가 영역 | 핵심 질문 | 측정 방법 | 채점 방식 |
|---|---|---|---|---|
| 1 | 답변 정확도 | FAQ 내용을 정확히 이해하고 답하는가? | LLM Judge + 키워드 커버리지 + ROUGE-L, 수동평가 | Judge + 결정론적 보조지표 |
| 2 | RAG 충실도 | 주어진 FAQ만 근거로 답하는가? | Faithfulness(Judge), Hallucination Rate, 숫자/고유명사 검증 | Judge + 결정론적 보조지표 |
| 3 | FAQ 부재 판단 | FAQ에 없는 질문에 억지로 답하지 않는가? | Precision / Recall / F1 | 결정론적 |
| 4 | 의도 분류 | 사용자 질문의 의도(`FAQ_RAG`/`MAP_API`/`UNREGISTERED`)를 정확히 분류하는가? | Accuracy, Macro-F1 | 결정론적 |
| 5 | 표현 품질 | 자연스러운 한국어 상담 답변인가? | 자연스러움, 명확성, 친절성 | Judge 필요 |
| 6 | 명령 수행 능력 | 지정 형식으로 안정적으로 출력하는가? | Format Success Rate | 결정론적 |
| 7 | 성능 | 실제 채팅 서비스에 충분히 빠른가? | TTFT, TPS, 전체 Latency | 결정론적 (계측) |
| 8 | 리소스 요구량 | 서비스 규모에서 감당 가능한가? | VRAM/RAM 사용량, 모델 크기·양자화 | 결정론적 (계측) |
| 9 | 클러스터 라벨링 | FAQ 부재 질문 묶음에 적절한 라벨/요약을 붙이는가? | 라벨 정확도(Judge), 라벨 환각 여부, 문자열 유사도 기반 라벨 구분력 | Judge + 결정론적 보조지표 |

클러스터링(그룹 나누기) 자체는 임베딩이 담당하고, LLM은 이미 만들어진 그룹에 라벨/요약만 붙이는 역할로 한정합니다.

> 항목 4의 의도 카테고리는 `data/intent_guide.csv` 기준입니다: `FAQ_RAG`(등록 FAQ로 답변), `MAP_API`(위치·지도 데이터 필요), `UNREGISTERED`(FAQ 근거 부족, 답변 보류), `UNREGISTERED_CLUSTERING`(미등록 질의 중 클러스터링 대상으로 수집). 분류 채점 시 `UNREGISTERED_CLUSTERING`은 `UNREGISTERED`와 같은 클래스로 취급합니다(3-way 분류: FAQ_RAG/MAP_API/UNREGISTERED). `_CLUSTERING` 접미사는 해당 건이 항목 9(클러스터 라벨링) 데이터로도 쓰인다는 태그일 뿐입니다.

## 6. 진행 순서

전체 9개 항목을 한 번에 다 보지 않고, 아래 순서로 나눠서 진행합니다.

1. **1차: FAQ 답변 생성 라운드 (현재 진행 중)** — 항목 1·2·5·6·7 (답변 정확도 / RAG 충실도 / 표현 품질 / 명령 수행 / 성능)을 난이도별(Easy/Medium/Hard) + RAG 안정성 시나리오로 검증
2. **2차: 의도 판단 라운드 (데이터 준비 완료)** — 항목 3·4 (FAQ 부재 판단 / 의도 분류). `data/eval_sets/intent_classification.csv`로 진행
3. **3차: 클러스터 라벨링 라운드 (데이터 준비 완료)** — 항목 9. `data/eval_sets/cluster_labeling.csv`로 진행

항목 8(리소스 요구량)은 모델별 고정 속성이라 별도 라운드 없이 모델 프로필 표에 기록합니다.

## 7. 평가 데이터

원본은 `data/raw/EmbeddingTestFAQ.xlsx` (임베딩 검색 테스트용으로 먼저 만들어졌던 파일을 재사용). 이 중 이번 LLM 테스트에 맞게 정리한 파일은 다음과 같습니다.

| 파일 | 원본 시트 | 용도 |
|---|---|---|
| `data/faq.csv` | FAQ | 마스터 FAQ 지식베이스 (100건: ID/카테고리/질문/답변/권장 처리 의도/세부 의도) |
| `data/intent_guide.csv` | Intent 가이드 | 의도 카테고리 4종 정의 및 판정 기준 (테스트 데이터 아님, 참고용) |
| `data/eval_sets/faq_easy.csv` | Retrieval Easy | 1차 라운드 - Easy 테스트 케이스 10건 (FAQ_RAG 9 + MAP_API 1) |
| `data/eval_sets/faq_medium.csv` | Retrieval Medium | 1차 라운드 - Medium 테스트 케이스 10건 (FAQ_RAG 9 + MAP_API 1) |
| `data/eval_sets/faq_hard.csv` | Retrieval Hard | 1차 라운드 - Hard 테스트 케이스 10건 (FAQ_RAG 9 + MAP_API 1) |
| `data/eval_sets/rag_faithfulness.csv` | RAG 안정성질문 | 항목 2(RAG 충실도) 전용 시나리오 21건 — 무관 FAQ/빈 컨텍스트/모순 FAQ/부분 정보/유사 오답/노이즈/다중 FAQ 조합 (각 3건씩 7개 유형) |
| `data/eval_sets/cluster_labeling.csv` | 미등록 클러스터링 | 항목 9(클러스터 라벨링) 전용 — 미등록 질의 20건 + 정답 클러스터(4개 그룹) |
| `data/eval_sets/intent_classification.csv` | (통합) | 항목 3·4용 통합 데이터셋 — 위 5개 파일에서 처리 의도가 라벨된 71건을 하나로 모음 |

### 7-1. Easy/Medium/Hard를 임베딩 시트에서 재활용해도 되는 이유

Easy/Medium/Hard 시트는 원래 **임베딩 검색 랭킹(Top-1 정답률) 검증용**으로 설계됐습니다. `Acceptable FAQ`, `Hard Negative FAQ` 컬럼이 그 증거이고, 이 컬럼들은 랭킹 문제라 이번 LLM 단독 평가에서는 **사용하지 않습니다**.

이 레포에서는 "임베딩이 정답 FAQ를 이미 올바르게 찾아줬다"고 가정하고, **User Query + Ground Truth FAQ 원문만 LLM에 제공한 뒤 생성한 답변의 품질만 평가**하는 방식으로 재활용합니다. 원래 설계 목적(임베딩이 헷갈려하는 정도)은 안 쓰지만, 난이도가 올라가면서 같이 딸려오는 두 가지 특성이 우연히 **LLM 생성 난이도**로도 그대로 유효합니다.

- **표현 방식**: Easy는 FAQ 문구와 거의 겹치는 직접 표현, Medium/Hard는 구어체·상황 묘사·동의어로 에둘러 말함 → LLM이 간접적인 질문 의도를 얼마나 잘 이해하는지 테스트 (순수 LLM 능력)
- **경쟁 FAQ(주의分산 요소)**: Hard로 갈수록 한 질문 안에 여러 연관 개념(분실+회선정지, 번호이동+기기변경, 로밍+Wi-Fi 등)이 섞여 있어 비슷한 FAQ로 오답할 여지가 큼 → 실제로 물어본 것에 정확히 대응하는 FAQ 하나에 집중해서 답하는 능력을 테스트 (RAG 검색과 무관한 순수 생성 능력)

즉 "임베딩이 어려워하는 이유"와 "LLM이 어려워하는 이유"는 다르지만, 난이도 라벨(Easy/Medium/Hard) 자체는 두 목적 모두에 우연히 들어맞아서 그대로 재사용합니다.

## 8. Judge (채점자) 구성

- 채점자: Claude Code 헤드리스 호출 (Pro 사용량 내)
- 후보 모델이 스스로를 채점하지 않도록, 모든 모델에 **동일한 고정 Judge**를 적용
- 절대 점수보다 **정답(Ground Truth FAQ 원문) 대조 채점**을 우선
- 환각 여부는 점수에 섞지 않고 **환각률(%)로 별도 집계** — 특정 임계치를 넘으면 다른 점수와 무관하게 "부적합" 표시

### 8-1. 결정론적 보조 지표 (무료, 규칙 기반)

LLM Judge 하나에만 판단을 맡기지 않고, 비용 없이 재현 가능한 규칙 기반 지표를 **같이** 계산해서 나란히 표기합니다. 임베딩·API가 필요 없는 것만 채택했습니다.

| 지표 | 적용 항목 | 계산 방식 |
|---|---|---|
| 키워드/사실 커버리지 (%) | 답변 정확도 | 정답 FAQ 답변에서 핵심 명사·숫자·조건을 미리 추출해두고, 생성 답변에 몇 %가 포함됐는지 문자열 매칭으로 계산 |
| n-gram 중복도 (ROUGE-L) | 답변 정확도 | 정답 답변과 생성 답변의 최장 공통 부분열 기반 재현율/정밀도 |
| 숫자/고유명사 존재 검증 | RAG 충실도 | 생성 답변에 등장하는 모든 숫자·금액·고유명사가 제공된 FAQ/컨텍스트 원문에 실제로 있는지 정규식 대조. 없으면 환각 후보로 플래그 |
| 문자열 중복/유사도 체크 | 클러스터 라벨 구분력 | 모델이 생성한 클러스터 라벨들끼리 Jaccard 유사도·편집 거리를 계산해, 서로 다른 클러스터에 지나치게 비슷한 라벨이 붙었는지 확인 |

이 지표들은 패러프레이즈(같은 뜻, 다른 표현)를 놓칠 수 있다는 한계가 있어 **LLM Judge/사람 평가를 대체하지 않고 보조 신호로만 사용**합니다. 임베딩 기반 의미 유사도는 원래 "임베딩 제외" 원칙과 결이 달라 이번엔 채택하지 않았습니다.

### 8-2. 사람(운영자) 평가 병행

LLM Judge가 채점하는 항목(1·2·5·9)은 **사람이 개별 건마다 별도로 직접 판단**합니다. 이건 소량 calibration set으로 Judge를 검증하는 것과는 별개로, **모든 테스트 케이스 하나하나에 대해** 결과 문서에 사람 의견을 남길 수 있는 칸을 둡니다.

- 결과 문서의 모델별 표에는 `사람 평가(의견)` 컬럼이 있고, 테스트 케이스마다 자유 텍스트로 의견을 남깁니다 (Judge 판정에 동의/이견 모두 기록)
- 모델별 결과 하단에는 해당 모델 전체에 대한 사람 총평 칸도 별도로 둡니다
- Judge와 사람 판단이 다를 경우, **최종 판단은 사람 의견을 우선**합니다. 이 차이가 누적되면 Judge 프롬프트/기준을 보정하는 데 사용합니다

## 9. 결과 문서

| 문서 | 내용 |
|---|---|
| [`results/faq_easy_results.md`](results/faq_easy_results.md) | Easy 난이도 모델별 결과 |
| [`results/faq_medium_results.md`](results/faq_medium_results.md) | Medium 난이도 모델별 결과 |
| [`results/faq_hard_results.md`](results/faq_hard_results.md) | Hard 난이도 모델별 결과 |
| [`results/faq_rag_stability_results.md`](results/faq_rag_stability_results.md) | RAG 안정성 시나리오(무관 FAQ/모순 FAQ/빈 컨텍스트 등) 모델별 결과 |
| [`results/intent_classification_results.md`](results/intent_classification_results.md) | 의도 분류(항목 3·4) 모델별 결과 |
| [`results/cluster_labeling_results.md`](results/cluster_labeling_results.md) | 클러스터 라벨링(항목 9) 모델별 결과 |

## 10. 리포지토리 구조

```
LLM_Test/
├── README.md
├── data/
│   ├── raw/
│   │   └── EmbeddingTestFAQ.xlsx        # 원본 엑셀
│   ├── faq.csv                          # 마스터 FAQ (100건)
│   ├── intent_guide.csv                 # 의도 카테고리 정의 (참고용)
│   └── eval_sets/
│       ├── faq_easy.csv
│       ├── faq_medium.csv
│       ├── faq_hard.csv
│       ├── rag_faithfulness.csv
│       ├── cluster_labeling.csv
│       └── intent_classification.csv    # 위 5개 파일 통합
└── results/
    ├── faq_easy_results.md
    ├── faq_medium_results.md
    ├── faq_hard_results.md
    ├── faq_rag_stability_results.md
    ├── intent_classification_results.md
    └── cluster_labeling_results.md
```

## 11. TODO

- [ ] Ollama에 9개 후보 모델 설치 및 워밍업(모델 로드 시간 분리 측정)
- [ ] 답변 생성 프롬프트 템플릿 확정 (출력 포맷 포함 — 항목 6 측정 기준과 직결)
- [ ] 결정론적 보조 지표 계산 스크립트 작성 (키워드 커버리지, ROUGE-L, 숫자/고유명사 검증, 라벨 문자열 유사도)
- [ ] Easy → Medium → Hard → RAG 안정성 순으로 9개 모델 실행 및 결과 문서 채우기
- [ ] 사람 채점 calibration set 소량 확보 후 Judge 신뢰도 검증 추가
- [ ] 의도 판단 라운드(항목 3·4) 9개 모델 실행 및 결과 문서 채우기
- [ ] 클러스터 라벨링 라운드(항목 9) 9개 모델 실행 및 결과 문서 채우기
