"""
tighten_test_expectations.py — 헐거운 기대값을 자동으로 엄격화

목적:
  Sprint 11에서 quality_audit이 발견한 "빈 기대값(expected: {})" 시나리오들을
  실제 검색 결과 기반으로 의미있는 기대값으로 보강한다.

전략:
  - 각 시나리오의 실제 검색 결과를 본 후,
  - 1위 점수가 충분히 높고 (>= 6.0)
  - 1위·2위 점수 격차가 충분하면 (>= 2.0)
  - 그 결과를 "기대값"으로 자동 채워넣는다 (top1_heading_contains 또는 slug)

안전 장치:
  - 1위 점수가 약하거나 격차가 부족하면 보강 안 함 (사람 검토 권고)
  - 콘텐츠 자체가 약한 경우는 시나리오를 그대로 두고 보고서에 표시
  - --dry-run 모드 지원 — 실제 파일은 수정 안 하고 변경 사항만 출력

사용:
    python scripts/tighten_test_expectations.py --dry-run
    python scripts/tighten_test_expectations.py --test-file tests/drug_test_suite.json
    python scripts/tighten_test_expectations.py --test-file tests/search_test_suite.json
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from search_engine import full_search, load_index, load_intents  # noqa: E402


def extract_distinctive_heading_term(top1_heading: str, query: str) -> str | None:
    """1위 청크 heading에서 가장 식별력 있는 부분을 추출 (기대값 키워드용).

    전략:
      - 헤딩에 query 토큰이 그대로 있으면 그 토큰 사용
      - 없으면 한국어 단어 중 길이 ≥3 인 첫 단어
    """
    import re

    # 짧은 한국어 단어 + 영문 후보 추출
    candidates = re.findall(r"[가-힣]{3,}|[A-Za-z][A-Za-z\-]{2,}", top1_heading)
    if not candidates:
        return None

    # 의미없는 일반어 제거
    common = {"위해", "통해", "그리고", "또한", "하지만", "그러나", "있으며", "있다", "한다",
              "환자", "통증", "치료", "관리", "방법", "효과", "주의", "참고", "출처"}
    candidates = [c for c in candidates if c not in common]
    if not candidates:
        return None

    return candidates[0]


def suggest_expectation(test: dict, actual: dict,
                        min_score: float = 6.0,
                        min_gap: float = 2.0) -> dict | None:
    """단일 시나리오의 보강 기대값 제안.

    반환:
      - dict: 새 expected 제안
      - None: 보강 보류 (콘텐츠 약함 또는 검증 보류)
    """
    results = actual.get("results", [])
    if not results:
        return None

    top1 = results[0]
    top1_score = top1.get("s", 0)
    if top1_score < min_score:
        return None  # 1위가 너무 약하면 신뢰 못함

    gap = top1_score - (results[1].get("s", 0) if len(results) > 1 else 0)
    if gap < min_gap and len(results) > 1:
        return None  # 격차가 부족하면 우연성 가능

    expected = dict(test.get("expected") or {})  # 기존 보존
    chunk = top1["chunk"]

    # 1) slug 보강
    if not expected.get("slug") and chunk.get("slug"):
        # raw 쿼리에 부위 명시가 있으면 강한 신호
        from search_engine import detect_body_part, tokenize
        raw_slug = detect_body_part(tokenize(test["query"]), test["query"])
        if raw_slug:
            expected["slug"] = raw_slug

    # 2) any_result_heading_contains 보강 (식별력 있는 키워드)
    if not expected.get("any_result_heading_contains"):
        term = extract_distinctive_heading_term(chunk.get("heading", ""), test["query"])
        if term:
            expected["any_result_heading_contains"] = [term]

    # 변경이 없으면 None
    if expected == (test.get("expected") or {}):
        return None
    return expected


def tighten(test_path: Path, *, dry_run: bool = True,
            min_score: float = 6.0, min_gap: float = 2.0,
            include_strong: bool = False) -> dict:
    """자동 보강.

    include_strong: True면 기대값이 이미 있어도 격차 부족 시나리오에 대해
                    any_result_heading_contains 보강.
                    1위 점수가 충분히 높을 때만 (기대값 약하지 않음 보장).
    """
    suite = json.loads(test_path.read_text(encoding="utf-8"))
    tests = suite.get("tests", [])
    index = load_index()
    intents = load_intents()

    proposals = []
    skipped = []

    for test in tests:
        expected = test.get("expected") or {}
        meaningful_keys = {"slug", "emergency", "time_stage", "drug_compare",
                           "ex_contra", "top1_slug", "top1_heading_contains",
                           "top1_category", "any_result_heading_contains",
                           "negated_categories"}
        has_meaningful = any(k in expected and expected[k] is not None
                             for k in meaningful_keys)

        # 기본 모드: 의미있는 기대값이 있으면 건너뜀
        # include_strong 모드: 의미있는 기대값이라도 any_result_heading_contains가 없으면 처리
        if has_meaningful and not include_strong:
            continue
        if has_meaningful and include_strong and \
                expected.get("any_result_heading_contains"):
            continue  # 이미 heading 검증 있으면 건너뜀

        try:
            actual = full_search(test["query"], top_k=5,
                                 index=index, intents=intents)
        except Exception as e:
            skipped.append({"id": test["id"], "reason": f"실행 에러: {e}"})
            continue

        results = actual.get("results", [])
        if not results:
            skipped.append({
                "id": test["id"], "query": test["query"],
                "reason": "결과 0건", "top1_score": 0, "top1_heading": "",
            })
            continue

        top1 = results[0]
        top1_score = top1.get("s", 0)
        gap = top1_score - (results[1].get("s", 0) if len(results) > 1 else 0)

        # 임계 확인
        if top1_score < min_score:
            skipped.append({
                "id": test["id"], "query": test["query"],
                "reason": "1위 점수 약함",
                "top1_score": round(top1_score, 1),
                "top1_heading": top1["chunk"].get("heading", "")[:50],
            })
            continue

        # 보강 제안 생성
        new_expected = dict(expected)
        changed = False

        # slug 보강 (기존 모드)
        if not new_expected.get("slug"):
            from search_engine import detect_body_part, tokenize
            raw_slug = detect_body_part(tokenize(test["query"]), test["query"])
            if raw_slug:
                new_expected["slug"] = raw_slug
                changed = True

        # any_result_heading_contains 보강
        if not new_expected.get("any_result_heading_contains"):
            # include_strong이거나 gap이 충분할 때만 신뢰
            if include_strong or gap >= min_gap:
                term = extract_distinctive_heading_term(
                    top1["chunk"].get("heading", ""), test["query"])
                if term:
                    new_expected["any_result_heading_contains"] = [term]
                    changed = True

        if not changed:
            skipped.append({
                "id": test["id"], "query": test["query"],
                "reason": "보강 가능한 항목 없음",
                "top1_score": round(top1_score, 1),
                "top1_heading": top1["chunk"].get("heading", "")[:50],
            })
            continue

        proposals.append({
            "id": test["id"], "query": test["query"],
            "before": dict(expected),
            "after": new_expected,
        })

    # 실제 적용
    if not dry_run and proposals:
        prop_map = {p["id"]: p["after"] for p in proposals}
        for test in tests:
            if test["id"] in prop_map:
                test["expected"] = prop_map[test["id"]]
        test_path.write_text(
            json.dumps(suite, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return {
        "proposals": proposals,
        "skipped": skipped,
        "dry_run": dry_run,
        "test_file": str(test_path),
    }


def print_report(result: dict):
    print("\n" + "=" * 70)
    print(" 기대값 자동 보강 결과")
    print("=" * 70)
    print(f"\n  대상: {result['test_file']}")
    print(f"  모드: {'DRY-RUN (저장 안 함)' if result['dry_run'] else '실제 적용'}")
    print(f"  보강 가능:  {len(result['proposals'])}개")
    print(f"  보강 보류:  {len(result['skipped'])}개 (콘텐츠 약함 또는 격차 부족)")

    if result["proposals"]:
        print("\n  보강 제안 (앞 15개):")
        for p in result["proposals"][:15]:
            print(f"\n    [{p['id']}] {p['query']!r}")
            print(f"      이전: {p['before'] or '{}'}")
            print(f"      이후: {p['after']}")
        if len(result["proposals"]) > 15:
            print(f"\n    ... ({len(result['proposals']) - 15}개 더)")

    if result["skipped"]:
        print("\n  보류 사유 (앞 10개) — 사람 검토 필요:")
        for s in result["skipped"][:10]:
            print(f"    [{s['id']}] {s.get('query', '?')!r}")
            print(f"      이유: {s['reason']}")
            if "top1_score" in s:
                print(f"      1위 점수 {s['top1_score']}: {s['top1_heading']!r}")
        if len(result["skipped"]) > 10:
            print(f"    ... ({len(result['skipped']) - 10}개 더)")

    print("\n" + "=" * 70 + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test-file",
                    default=str(ROOT / "tests" / "search_test_suite.json"))
    ap.add_argument("--dry-run", action="store_true",
                    help="파일을 실제로 수정하지 않고 변경 사항만 출력")
    ap.add_argument("--min-score", type=float, default=6.0,
                    help="1위 점수 최소 임계 (기본 6.0)")
    ap.add_argument("--min-gap", type=float, default=2.0,
                    help="1위·2위 점수 격차 최소 (기본 2.0)")
    ap.add_argument("--include-strong", action="store_true",
                    help="기대값이 이미 있어도 1위 명확한 시나리오에 heading 검증 추가")
    args = ap.parse_args()

    result = tighten(Path(args.test_file), dry_run=args.dry_run,
                     min_score=args.min_score, min_gap=args.min_gap,
                     include_strong=args.include_strong)
    print_report(result)


if __name__ == "__main__":
    main()
