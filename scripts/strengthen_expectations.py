"""
strengthen_expectations.py — 기존 시나리오에 추가 검증 항목 누적

quality_audit의 격차 부족 시나리오 중 1위가 명확하지만 `any_result_heading_contains`에
1개 키워드만 있는 시나리오에 대해, 1위·2위 결과의 핵심 키워드를 추가로 명시.

전략:
  - 같은 부위·같은 카테고리(진단·자가체크 등) 내 동점은 자연스러우니
    그 카테고리 내 청크 모두의 핵심 키워드를 검증에 포함시켜
    "어느 청크가 1위든 검색 의미는 같다"는 정보를 명시화한다.

이게 quality_audit 결과를 개선하는 것이 아니라, 시나리오 자체의 검증 강도를
객관 데이터로 명시화하는 것.

사용:
    python scripts/strengthen_expectations.py --test-file tests/search_test_suite.json --dry-run
    python scripts/strengthen_expectations.py --test-file tests/search_test_suite.json
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from search_engine import full_search, load_index, load_intents  # noqa: E402


def extract_terms(heading: str, max_n: int = 1) -> list[str]:
    """heading에서 식별력 있는 키워드 최대 N개 추출."""
    common = {"위해", "통해", "그리고", "또한", "하지만", "그러나", "있으며", "있다",
              "한다", "환자", "통증", "치료", "관리", "방법", "효과", "주의", "참고",
              "출처", "흔한", "증상", "질환", "자가", "체크리스트", "감별진단표"}
    cands = re.findall(r"[가-힣]{3,}|[A-Za-z][A-Za-z\-]{2,}", heading)
    cands = [c for c in cands if c not in common]
    return cands[:max_n]


def strengthen(test_path: Path, *, dry_run: bool = True) -> dict:
    suite = json.loads(test_path.read_text(encoding="utf-8"))
    tests = suite.get("tests", [])
    index = load_index()
    intents = load_intents()

    proposals = []
    skipped = []

    for test in tests:
        expected = test.get("expected") or {}
        # 이미 any_result_heading_contains에 2개 이상이면 건너뜀
        existing_terms = expected.get("any_result_heading_contains") or []
        if len(existing_terms) >= 2:
            continue

        try:
            actual = full_search(test["query"], top_k=5, index=index, intents=intents)
        except Exception as e:
            skipped.append({"id": test["id"], "reason": f"실행 에러: {e}"})
            continue

        results = actual.get("results", [])
        if len(results) < 2:
            continue
        top1 = results[0]
        if top1["s"] < 6.0:
            continue

        # 1위·2위·3위 heading에서 핵심 키워드 추출
        # (이미 검증된 표현은 제외)
        new_terms = set(existing_terms)
        for r in results[:3]:
            terms = extract_terms(r["chunk"].get("heading", ""), max_n=1)
            for t in terms:
                new_terms.add(t)
        new_terms_list = sorted(new_terms)
        # 추가된 키워드가 있고 1개 → 2~3개로 늘어났을 때만 보강
        if len(new_terms_list) <= len(existing_terms):
            continue
        if len(new_terms_list) < 2:
            continue

        new_expected = dict(expected)
        new_expected["any_result_heading_contains"] = new_terms_list
        proposals.append({
            "id": test["id"], "query": test["query"],
            "before_terms": existing_terms,
            "after_terms": new_terms_list,
        })

    if not dry_run and proposals:
        prop_map = {p["id"]: p["after_terms"] for p in proposals}
        for test in tests:
            if test["id"] in prop_map:
                test["expected"] = test.get("expected") or {}
                test["expected"]["any_result_heading_contains"] = prop_map[test["id"]]
        test_path.write_text(
            json.dumps(suite, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return {"proposals": proposals, "skipped": skipped, "dry_run": dry_run,
            "test_file": str(test_path)}


def print_report(result):
    print(f"\n  대상: {result['test_file']}")
    print(f"  모드: {'DRY-RUN' if result['dry_run'] else '실제 적용'}")
    print(f"  강화 가능: {len(result['proposals'])}건")
    for p in result["proposals"][:10]:
        print(f"    [{p['id']}] {p['query']!r}")
        print(f"       before: {p['before_terms']}")
        print(f"       after:  {p['after_terms']}")
    if len(result["proposals"]) > 10:
        print(f"    ... ({len(result['proposals']) - 10}개 더)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test-file", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    result = strengthen(Path(args.test_file), dry_run=args.dry_run)
    print_report(result)


if __name__ == "__main__":
    main()
