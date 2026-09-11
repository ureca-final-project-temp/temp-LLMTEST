# LLM FAQ Answer Generation Test Summary

## 1. Test overview

- Purpose: Evaluate how well each local LLM generates an answer from a user question and retrieved FAQ Context.
- Models: 8 models from `ollama list`
- Test cases: 480
- Total model responses: 3,840
- Repetitions: 1 per model and case
- Temperature: 0
- Output format: JSON
- Prompt language: Korean customer-center response

The LLM was instructed to use only the provided FAQ Context, avoid guessing, handle insufficient or conflicting information safely, and return `answer`, `grounded`, and `used_faq_ids` fields.

## 2. Test composition

| Test | Cases | Purpose |
|---|---:|---|
| T01 Easy | 20 | Direct answer generation with easy FAQ Context |
| T02 Medium | 20 | Answer generation with moderately complex FAQ Context |
| T03 Hard | 20 | Answer generation with difficult or ambiguous FAQ Context |
| T04 Irrelevant FAQ | 60 | Check refusal to use unrelated FAQ information |
| T05 Empty Context | 60 | Check whether the model avoids guessing without FAQ evidence |
| T06 Contradictory FAQ | 60 | Check whether conflicting FAQ information is handled safely |
| T07 Partial Information | 60 | Check whether the model avoids filling missing details by assumption |
| T08 Similar but No Answer | 60 | Check whether similar but insufficient FAQ information is rejected |
| T09 Correct FAQ + Noise | 60 | Check whether relevant FAQ information is selected over noise |
| T10 Multi-FAQ Combination | 60 | Check whether multiple relevant FAQs are combined correctly |

## 3. Execution results by model

| Model | Calls | Execution errors | Valid JSON | Avg latency (ms) | P95 latency (ms) | Avg output tokens |
|---|---:|---:|---:|---:|---:|---:|
| exaone3.5:2.4b | 480 | 0 | 480/480 | 992 | 1,823 | 152.1 |
| exaone3.5:7.8b | 480 | 0 | 475/480 | 1,719 | 2,547 | 118.4 |
| qwen3:1.7b | 480 | 0 | 480/480 | 456 | 768 | 100.7 |
| qwen3:4b | 480 | 0 | 479/480 | 796 | 1,359 | 87.3 |
| qwen3:14b | 480 | 0 | 480/480 | 7,784 | 11,174 | 75.3 |
| gemma3:12b | 480 | 0 | 480/480 | 5,377 | 7,328 | 59.7 |
| qwen3:8b | 480 | 0 | 480/480 | 1,095 | 1,643 | 74.8 |
| gemma3:4b | 480 | 0 | 479/480 | 779 | 1,227 | 73.2 |

## 4. Automatic findings

- All 3,840 requests completed without an execution error.
- 3,833 responses were valid JSON.
- 7 responses failed the required JSON format.
- The format failures were concentrated in long or complex cases:
  - `exaone3.5:7.8b`: 5 cases
  - `qwen3:4b`: 1 case
  - `gemma3:4b`: 1 case
- RAM and VRAM peak usage was not collected in this run.

## 5. Content-quality review status

The Markdown files contain every model answer for direct review. The following criteria must be judged by reading each answer against the question and FAQ Context:

- Accuracy: whether the answer states the FAQ-supported facts correctly
- Completeness: whether all necessary parts of the answer are included
- Relevance: whether the answer addresses the user question without unrelated FAQ content
- Grounding: whether claims are supported by the provided FAQ Context
- Naturalness: whether the Korean customer-center response is clear and natural
- Hallucination/problem flag: whether unsupported facts, invented conditions, incorrect combinations, or unsafe certainty appear

These criteria have not been converted into automatic scores in this summary. The per-test Markdown files are the source for manual content review.

## 6. Detailed results

- [T01 Easy](T01_Easy_answer_generation.md)
- [T02 Medium](T02_Medium_answer_generation.md)
- [T03 Hard](T03_Hard_answer_generation.md)
- [T04 Irrelevant FAQ](T04_irrelevant_FAQ_response.md)
- [T05 Empty Context](T05_empty_Context_response.md)
- [T06 Contradictory FAQ](T06_contradictory_FAQ_response.md)
- [T07 Partial Information](T07_partial_information_response.md)
- [T08 Similar but No Answer](T08_similar_but_no_answer.md)
- [T09 Correct FAQ + Noise](T09_correct_FAQ_plus_noise.md)
- [T10 Multi-FAQ Combination](T10_multi_FAQ_combination.md)
- [Resource benchmark](resource_benchmark.md)
