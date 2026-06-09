"""
run_search_tests.py — ortho-kb 검색 회귀 테스트 러너

사용법:
    python scripts/run_search_tests.py
    python scripts/run_search_tests.py --verbose
    python scripts/run_search_tests.py --category emergency
    python scripts/run_search_tests.py --threshold 0.7  # 합격 임계 (기본 0.7)

종료 코드:
    0  — 합격률 임계 이상 (기본 70%)
    1  — 합격률 임계 미만 (CI에서 push 차단)
    2  — 실행 자체 실패 (인덱스/사전 누락 등)

리포트:
    - 카테고리별 합격률
    - 실패 케이스 상세 (query, expected, actual)
    - 총 통계 (합격/실패/총개수/시간)
"""
from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

try:
    from search_engine import full_search, load_index, load_intents
except ImportError as e:
    print(f"[ERROR] search_engine 모듈 로드 실패: {e}", file=sys.stderr)
    print(f"  PYTHONPATH={sys.path}", file=sys.stderr)
    sys.exit(2)

TEST_PATH = ROOT / "tests" / "search_test_suite.json"


def check_assertion(expected: dict, actual: dict) -> tuple[bool, list[str]]:
    """기대값 ↔ 실제 결과 비교. (통과여부, 불일치 사유 리스트) 반환."""
    failures = []

    # slug 검증
    if "slug" in expected:
        exp_slug = expected["slug"]
        act_slug = actual.get("detected_slug")
        if act_slug != exp_slug:
            failures.append(f"slug: 기대={exp_slug!r} 실제={act_slug!r}")

    # emergency 검증
    if "emergency" in expected and expected["emergency"] is not None:
        if actual.get("is_emergency", False) != expected["emergency"]:
            failures.append(
                f"emergency: 기대={expected['emergency']} 실제={actual.get('is_emergency')}"
            )

    # time_stage 검증
    if "time_stage" in expected and expected["time_stage"] is not None:
        exp_stage = expected["time_stage"]
        actual_ts = actual.get("time_stage")
        actual_stage = actual_ts[0] if isinstance(actual_ts, (tuple, list)) else None
        if actual_stage != exp_stage:
            failures.append(f"time_stage: 기대={exp_stage!r} 실제={actual_stage!r}")

    # drug_compare 검증
    if "drug_compare" in expected and expected["drug_compare"] is not None:
        actual_dc = actual.get("drug_compare") is not None
        if actual_dc != expected["drug_compare"]:
            failures.append(
                f"drug_compare: 기대={expected['drug_compare']} 실제={actual_dc}"
            )

    # ex_contra 검증
    if "ex_contra" in expected and expected["ex_contra"] is not None:
        actual_ec = bool(actual.get("exercise_contraindication"))
        if actual_ec != expected["ex_contra"]:
            failures.append(f"ex_contra: 기대={expected['ex_contra']} 실제={actual_ec}")

    # ex_catalog 검증 (Sprint 14)
    if "ex_catalog" in expected and expected["ex_catalog"] is not None:
        ec = actual.get("exercise_catalog") or {}
        actual_ex_cat = bool(ec.get("movements") or ec.get("principles"))
        if actual_ex_cat != expected["ex_catalog"]:
            failures.append(f"ex_catalog: 기대={expected['ex_catalog']} 실제={actual_ex_cat}")

    # top1_slug 검증
    if "top1_slug" in expected and expected["top1_slug"] is not None:
        results = actual.get("results", [])
        top1_slug = results[0]["chunk"]["slug"] if results else None
        if top1_slug != expected["top1_slug"]:
            failures.append(f"top1_slug: 기대={expected['top1_slug']!r} 실제={top1_slug!r}")

    # top1_heading_contains 검증
    if "top1_heading_contains" in expected and expected["top1_heading_contains"] is not None:
        results = actual.get("results", [])
        top1_heading = results[0]["chunk"]["heading"] if results else ""
        sub = expected["top1_heading_contains"]
        if sub not in top1_heading:
            failures.append(
                f"top1_heading: {sub!r} 미포함 (실제: {top1_heading!r})"
            )

    # top1_category 검증
    if "top1_category" in expected and expected["top1_category"] is not None:
        results = actual.get("results", [])
        top1_cat = results[0]["cat"] if results else None
        if top1_cat != expected["top1_category"]:
            failures.append(
                f"top1_category: 기대={expected['top1_category']!r} 실제={top1_cat!r}"
            )

    # any_result_heading_contains 검증 (AND — 모든 키워드가 어딘가에 들어가야 합격)
    if "any_result_heading_contains" in expected and expected["any_result_heading_contains"]:
        results = actual.get("results", [])
        all_headings = " ".join(r["chunk"]["heading"] for r in results)
        for sub in expected["any_result_heading_contains"]:
            if sub not in all_headings:
                failures.append(
                    f"any_result_heading: {sub!r} 어떤 결과에도 미포함"
                )

    # negated_categories 검증
    if "negated_categories" in expected and expected["negated_categories"] is not None:
        expected_cats = set(expected["negated_categories"])
        actual_cats = set(n["category"] for n in actual.get("negated", []))
        if not expected_cats.issubset(actual_cats):
            failures.append(
                f"negated: 기대={sorted(expected_cats)} 실제={sorted(actual_cats)}"
            )

    return (len(failures) == 0), failures


def run_tests(filter_category: str | None = None,
              verbose: bool = False) -> dict:
    """전체 테스트 실행 후 결과 dict 반환."""
    if not TEST_PATH.exists():
        print(f"[ERROR] 테스트 파일 없음: {TEST_PATH}", file=sys.stderr)
        sys.exit(2)

    suite = json.loads(TEST_PATH.read_text(encoding="utf-8"))
    tests = suite.get("tests", [])
    if filter_category:
        tests = [t for t in tests if t.get("category") == filter_category]

    index = load_index()
    intents = load_intents()

    started = time.time()
    results_by_cat = {}  # category -> {pass:int, fail:int, total:int, failures:[]}
    overall_pass = 0
    overall_fail = 0
    all_failures = []

    for test in tests:
        tid = test["id"]
        category = test.get("category", "uncategorized")
        query = test["query"]
        expected = test.get("expected", {})

        try:
            actual = full_search(query, top_k=5, index=index, intents=intents)
        except Exception as e:
            ok, failures = False, [f"실행 에러: {e}"]
            actual = {}
        else:
            ok, failures = check_assertion(expected, actual)

        bucket = results_by_cat.setdefault(category, {
            "pass": 0, "fail": 0, "total": 0, "failures": []
        })
        bucket["total"] += 1
        if ok:
            bucket["pass"] += 1
            overall_pass += 1
        else:
            bucket["fail"] += 1
            overall_fail += 1
            failure_detail = {
                "id": tid, "category": category, "query": query,
                "expected": expected, "failures": failures,
                "actual_summary": {
                    "detected_slug": actual.get("detected_slug"),
                    "is_emergency": actual.get("is_emergency"),
                    "time_stage": actual.get("time_stage"),
                    "drug_compare": actual.get("drug_compare") is not None,
                    "ex_contra": bool(actual.get("exercise_contraindication")),
                    "ex_catalog": bool((actual.get("exercise_catalog") or {}).get("movements")
                                       or (actual.get("exercise_catalog") or {}).get("principles")),
                    "top3": [
                        {"slug": r["chunk"].get("slug"),
                         "heading": r["chunk"].get("heading")[:50],
                         "cat": r.get("cat"),
                         "score": round(r.get("s", 0), 1)}
                        for r in actual.get("results", [])[:3]
                    ],
                }
            }
            bucket["failures"].append(failure_detail)
            all_failures.append(failure_detail)

        if verbose:
            mark = "✅" if ok else "❌"
            print(f"  {mark} {tid} [{category:15}] {query[:50]}")
            if not ok and failures:
                for f in failures:
                    print(f"       · {f}")

    duration = time.time() - started
    total = overall_pass + overall_fail
    pass_rate = overall_pass / total if total > 0 else 0

    return {
        "total": total,
        "pass": overall_pass,
        "fail": overall_fail,
        "pass_rate": pass_rate,
        "duration_sec": duration,
        "by_category": results_by_cat,
        "failures": all_failures,
    }


def print_report(result: dict, threshold: float):
    total = result["total"]
    p = result["pass"]
    f = result["fail"]
    rate = result["pass_rate"]
    dur = result["duration_sec"]

    print("\n" + "=" * 70)
    print(" ortho-kb 검색 회귀 테스트 결과")
    print("=" * 70)
    print(f"\n  총 {total}개 · 합격 {p}개 · 실패 {f}개")
    print(f"  합격률: {rate * 100:.1f}%  (임계: {threshold * 100:.0f}%)")
    print(f"  실행 시간: {dur:.2f}초")

    print("\n  카테고리별 결과:")
    for category, b in sorted(result["by_category"].items()):
        cat_rate = b["pass"] / b["total"] if b["total"] > 0 else 0
        bar = "█" * int(cat_rate * 20) + "░" * (20 - int(cat_rate * 20))
        print(f"    {category:18} {bar} {b['pass']:>3}/{b['total']:<3} ({cat_rate*100:.0f}%)")

    if result["failures"]:
        print("\n" + "-" * 70)
        print(f" 실패 케이스 ({len(result['failures'])}개)")
        print("-" * 70)
        for ff in result["failures"][:20]:  # 최대 20개만 자세히
            print(f"\n  [{ff['id']}] [{ff['category']}] {ff['query']!r}")
            for line in ff["failures"]:
                print(f"    ✗ {line}")
            if ff.get("actual_summary", {}).get("top3"):
                print(f"    Top3 실제:")
                for t in ff["actual_summary"]["top3"]:
                    print(f"      [{t['score']:5.1f}] [{t['cat']:11}] [{t['slug']}] {t['heading']}")
        if len(result["failures"]) > 20:
            print(f"\n  ... ({len(result['failures']) - 20}개 더)")

    print("\n" + "=" * 70)
    if rate >= threshold:
        print(f" ✅ PASS  ({rate*100:.1f}% ≥ {threshold*100:.0f}%)")
    else:
        print(f" ❌ FAIL  ({rate*100:.1f}% < {threshold*100:.0f}%)")
    print("=" * 70 + "\n")


def main():
    global TEST_PATH  # noqa: PLW0603 — 옵션으로 테스트 파일 갈아끼우기 위해
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", "-v", action="store_true")
    ap.add_argument("--category", default=None,
                    help="특정 카테고리만 실행 (예: emergency)")
    ap.add_argument("--threshold", type=float, default=0.7,
                    help="합격 임계 (0.0~1.0, 기본 0.7)")
    ap.add_argument("--json-out", default=None,
                    help="JSON 리포트 출력 경로 (CI 통합용)")
    ap.add_argument("--test-file", default=str(TEST_PATH),
                    help="테스트 시나리오 JSON 경로")
    args = ap.parse_args()

    TEST_PATH = Path(args.test_file)

    result = run_tests(filter_category=args.category, verbose=args.verbose)
    print_report(result, args.threshold)

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  JSON 리포트: {args.json_out}\n")

    sys.exit(0 if result["pass_rate"] >= args.threshold else 1)


if __name__ == "__main__":
    main()
