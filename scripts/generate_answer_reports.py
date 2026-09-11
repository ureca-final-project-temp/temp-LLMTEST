import json
import os
import statistics
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH = os.path.join(ROOT, "results", "raw", "llm_answer_generation.jsonl")
OUT_DIR = os.path.join(ROOT, "results")
TEST_NAMES = {
    "T01": "Easy_answer_generation", "T02": "Medium_answer_generation",
    "T03": "Hard_answer_generation", "T04": "irrelevant_FAQ_response",
    "T05": "empty_Context_response", "T06": "contradictory_FAQ_response",
    "T07": "partial_information_response", "T08": "similar_but_no_answer",
    "T09": "correct_FAQ_plus_noise", "T10": "multi_FAQ_combination",
}

def answer_of(record):
    parsed = record.get("parsed")
    return parsed.get("answer", "") if isinstance(parsed, dict) else record.get("raw_output", "")

def auto_flags(record):
    flags = []
    if not record.get("ok"): flags.append("execution_error")
    if not record.get("format_valid"): flags.append("json_format_error")
    if not answer_of(record).strip(): flags.append("empty_answer")
    return flags

def write_test_report(test_id, records):
    records.sort(key=lambda x: (x["case"]["id"], x["model"]))
    by_case = defaultdict(list)
    for record in records: by_case[record["case"]["id"]].append(record)
    path = os.path.join(OUT_DIR, f"{test_id}_{TEST_NAMES[test_id]}.md")
    with open(path, "w", encoding="utf-8") as out:
        out.write(f"# {test_id} {TEST_NAMES[test_id]}\n\n")
        out.write(f"- Cases: {len(by_case)}\n- Model answers: {len(records)}\n")
        out.write("- Review method: manually check accuracy, completeness, relevance, grounding, and natural Korean expression.\n\n")
        for case_id, case_records in by_case.items():
            case = case_records[0]["case"]
            out.write(f"---\n\n## {case_id}\n\n### User question\n\n{case['query']}\n\n")
            out.write("### FAQ Context\n\n```text\n" + case.get("context", "") + "\n```\n\n")
            if case.get("expected_ref") is not None:
                out.write(f"- Expected reference FAQ: {case.get('expected_ref', '')}\n")
                out.write(f"- Expected behavior: {case.get('expected_behavior', '')}\n")
                out.write(f"- Failure condition: {case.get('failure_condition', '')}\n\n")
            out.write("### Model answers\n\n")
            for record in case_records:
                parsed = record.get("parsed") if isinstance(record.get("parsed"), dict) else {}
                flags = auto_flags(record)
                out.write(f"#### {record['model']}\n\nAnswer:\n\n{answer_of(record)}\n\n")
                out.write(f"- grounded: `{parsed.get('grounded', '')}`\n- used_faq_ids: `{parsed.get('used_faq_ids', '')}`\n")
                out.write(f"- latency_ms: `{record.get('latency_ms', '')}`\n- Automatic flags: `{', '.join(flags) if flags else 'none'}`\n")
                out.write("- Manual review: `accuracy / completeness / relevance / grounding / naturalness — review required`\n\n")

def write_resource_report(records):
    by_model = defaultdict(list)
    for record in records: by_model[record["model"]].append(record)
    path = os.path.join(OUT_DIR, "resource_benchmark.md")
    with open(path, "w", encoding="utf-8") as out:
        out.write("# Resource and Execution Benchmark\n\n| Model | Calls | Execution errors | Valid JSON | Avg latency (ms) | P95 latency (ms) | Avg output tokens |\n|---|---:|---:|---:|---:|---:|---:|\n")
        for model, rows in by_model.items():
            latencies = sorted(r["latency_ms"] for r in rows if r.get("ok"))
            counts = [r["eval_count"] for r in rows if isinstance(r.get("eval_count"), int)]
            p95 = latencies[max(0, int(len(latencies) * 0.95) - 1)] if latencies else ""
            avg = round(statistics.mean(latencies)) if latencies else ""
            avg_tokens = round(statistics.mean(counts), 1) if counts else ""
            errors = sum(1 for r in rows if not r.get("ok"))
            formats = sum(1 for r in rows if r.get("format_valid"))
            out.write(f"| {model} | {len(rows)} | {errors} | {formats}/{len(rows)} | {avg} | {p95} | {avg_tokens} |\n")
        out.write("\nRAM/VRAM peak was not collected in this run; record it separately if needed.\n")

def main():
    with open(RAW_PATH, encoding="utf-8") as f: records = [json.loads(line) for line in f if line.strip()]
    by_test = defaultdict(list)
    for record in records: by_test[record["test"]].append(record)
    for test_id in sorted(by_test): write_test_report(test_id, by_test[test_id])
    write_resource_report(records)
    print(f"generated_reports={len(by_test)} records={len(records)}")

if __name__ == "__main__": main()
