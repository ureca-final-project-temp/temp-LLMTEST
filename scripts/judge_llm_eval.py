import json
import os
import urllib.request
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH = os.path.join(ROOT, "results", "raw", "llm_answer_generation.jsonl")
OUT_PATH = os.path.join(ROOT, "results", "raw", "llm_answer_judgement.jsonl")
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
JUDGE_MODEL = "qwen3:1.7b"
BATCH_SIZE = 4

SYSTEM = """You are a strict Korean customer-center FAQ answer evaluator.
For each case, compare the user question, FAQ Context, expected behavior, and every model answer.
Judge each answer with binary values (1 pass, 0 fail): accuracy, completeness, relevance, grounding, and naturalness.
Set problem=true for hallucinated or unsupported facts, irrelevant content, wrong FAQ combinations, unsafe certainty, empty answers, or invalid JSON format.
Return only one JSON object with this shape:
{"evaluations":[{"test":"T01","case_id":"E01","model":"model-name","accuracy":1,"completeness":1,"relevance":1,"grounding":1,"naturalness":1,"problem":false,"issue":""}]}
Include one evaluation for every model in every case. The issue must be a short Korean explanation when problem=true, otherwise an empty string.
"""

def ask(payload):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as res:
        return json.loads(res.read().decode("utf-8"))

def parse_json(text):
    try:
        return json.loads(text)
    except Exception:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            try: return json.loads(text[start:end + 1])
            except Exception: return None
    return None

def normalize(case_rows, evaluation_map):
    result = []
    for row in case_rows:
        e = evaluation_map.get(row["model"], {})
        result.append({"model": row["model"], "accuracy": int(bool(e.get("accuracy", False))), "completeness": int(bool(e.get("completeness", False))), "relevance": int(bool(e.get("relevance", False))), "grounding": int(bool(e.get("grounding", False))), "naturalness": int(bool(e.get("naturalness", False))), "problem": bool(e.get("problem", True)), "issue": str(e.get("issue", "평가 결과 누락"))})
    return result

def main():
    part = int(os.environ.get("JUDGE_PART", "0"))
    parts = int(os.environ.get("JUDGE_PARTS", "1"))
    output_path = OUT_PATH if parts == 1 else os.path.join(ROOT, "results", "raw", f"llm_answer_judgement_part{part}.jsonl")
    rows = [json.loads(line) for line in open(RAW_PATH, encoding="utf-8") if line.strip()]
    grouped = defaultdict(list)
    for row in rows: grouped[(row["test"], row["case"]["id"])].append(row)
    completed = {}
    if os.path.exists(output_path):
        for line in open(output_path, encoding="utf-8"):
            if line.strip():
                item = json.loads(line); completed[(item["test"], item["case_id"])] = item
    all_pending = [(key, items) for key, items in sorted(grouped.items()) if key not in completed]
    pending = all_pending[part::parts]
    out = open(output_path, "a", encoding="utf-8")
    for batch_start in range(0, len(pending), BATCH_SIZE):
        batch = pending[batch_start:batch_start + BATCH_SIZE]
        payload_cases = []
        for (test_id, case_id), items in batch:
            case = items[0]["case"]
            payload_cases.append({"test": test_id, "case_id": case_id, "question": case.get("query", ""), "faq_context": case.get("context", ""), "expected_behavior": case.get("test_point", ""), "answers": [{"model": r["model"], "answer": (r.get("parsed") or {}).get("answer", r.get("raw_output", "")), "grounded": (r.get("parsed") or {}).get("grounded", ""), "format_valid": r.get("format_valid", False)} for r in items]})
        try:
            response = ask({"model": JUDGE_MODEL, "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": json.dumps({"cases": payload_cases}, ensure_ascii=False)}], "format": "json", "stream": False, "think": False, "options": {"temperature": 0, "num_predict": 8192}})
            parsed = parse_json(response.get("message", {}).get("content", "")) or {}
            evaluations = parsed.get("evaluations", [])
            if not evaluations and isinstance(parsed.get("cases"), list):
                for case_result in parsed["cases"]:
                    evaluations.extend(case_result.get("evaluations", []))
            by_case_model = defaultdict(dict)
            for evaluation in evaluations:
                if isinstance(evaluation, dict): by_case_model[(evaluation.get("test"), evaluation.get("case_id"))][evaluation.get("model")] = evaluation
            for (test_id, case_id), items in batch:
                item = {"test": test_id, "case_id": case_id, "judge_model": JUDGE_MODEL, "evaluations": normalize(items, by_case_model[(test_id, case_id)])}
                out.write(json.dumps(item, ensure_ascii=False) + "\n")
        except Exception as exc:
            for (test_id, case_id), items in batch:
                item = {"test": test_id, "case_id": case_id, "judge_model": JUDGE_MODEL, "error": str(exc), "evaluations": normalize(items, {})}
                out.write(json.dumps(item, ensure_ascii=False) + "\n")
        out.flush()
        done = min(batch_start + len(batch), len(pending))
        print(f"part={part} judged_new={done}/{len(pending)} total_completed={len(completed) + done}")
    out.close()
    print(f"saved={output_path} total_cases={len(grouped)}")

if __name__ == "__main__": main()
