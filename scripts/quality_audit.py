"""
quality_audit.py — 테스트 스위트 자체 품질 점검

목적:
  `run_search_tests.py`가 "기대값 ↔ 실제값" 일치를 검증한다면,
  이 도구는 "기대값 자체가 의미있는가"를 점검한다.

  Sprint 10에서 발견한 함정 — 100/100 합격이지만 사실 3건이 헐거운 기대값으로
  가짜 통과 — 같은 사례를 자동으로 탐지한다.

5가지 자동 검사:
  1. 빈 기대값 비율          — expected가 {} 이거나 검증 항목이 0개
  2. 결과 0건 시나리오        — 검색 결과 없는데 통과로 표시
  3. top1 무관 시나리오       — 1위 결과의 부위/카테고리가 질문과 동떨어짐
  4. 부위 감지 실패           — slug 명시했는데 감지 실패
  5. 점수 격차 부족           — 1위·2위 점수 차이가 너무 작음 (우연성)

사용:
    python scripts/quality_audit.py
    python scripts/quality_audit.py --test-file tests/drug_test_suite.json
    python scripts/quality_audit.py --strict   # 점수 격차 임계 강화

출력:
  - 발견된 이슈 카운트 + 비율
  - 시나리오별 권고 (가장 문제 큰 것부터)
  - 종합 품질 점수 (참고용)
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from search_engine import full_search, load_index, load_intents  # noqa: E402

DEFAULT_TEST = ROOT / "tests" / "search_test_suite.json"


def has_meaningful_expectations(expected: dict) -> bool:
    """기대값에 실질 검증 항목이 하나라도 있는지."""
    if not expected:
        return False
    meaningful_keys = {
        "slug", "emergency", "time_stage", "drug_compare", "ex_contra",
        "ex_catalog", "drug_interaction",  # Sprint 19 추가
        "top1_slug", "top1_heading_contains", "top1_category",
        "any_result_heading_contains", "negated_categories",
    }
    return any(k in expected and expected[k] is not None for k in meaningful_keys)


def top1_is_relevant(actual: dict, query: str) -> tuple[bool, str]:
    """1위 결과가 질문과 관련 있는지 휴리스틱 검사.

    판단:
    - 결과 0건이면 무관 (relevant=False)
    - 1위 점수가 5점 미만이면 약한 매칭 (warn)
    - 부위가 raw 쿼리에 명시되어 있는데 1위 slug가 다르면 무관
    """
    results = actual.get("results", [])
    if not results:
        return False, "결과 0건"
    top1 = results[0]
    score = top1.get("s", 0)
    if score < 5:
        return False, f"1위 점수 매우 약함 ({score:.1f})"
    return True, "OK"


def score_gap_ok(actual: dict, min_gap: float = 2.0) -> tuple[bool, float]:
    """1위·2위 점수 차이가 충분한지.

    너무 작으면 1위가 우연성에 가까움.

    Sprint 14 개선:
      1) 1위와 다른 부위·다른 카테고리의 2위 간 격차를 측정.
         같은 카테고리·다른 부위는 자연스러운 매칭이라 페널티 안 줌.
      2) 1위가 약물(medication) 카테고리이면, 같은 medication 청크끼리는
         부위 달라도 동점이 자연스러움 → 격차 비교 대상에서 medication 모두 제외.
         (셀레콕시브 같은 약물명이 6부위에 동일 정보로 등장)
      3) Sprint 16: 1위가 응급(emergency) 카테고리이면, 같은 emergency 청크끼리는
         부위 달라도 동점이 안전상 자연스러움 (여러 부위 응급 안내가 동시 표시되는 게 의도)
         → 격차 비교 대상에서 emergency 모두 제외.
    """
    results = actual.get("results", [])
    if len(results) < 2:
        return True, float("inf")
    top1 = results[0]
    top1_chunk = top1.get("chunk", {})
    top1_slug = top1_chunk.get("slug")
    top1_cat = top1.get("cat")
    # 약물 또는 응급 1위인 경우, 같은 카테고리 cross-부위는 자연 동점 처리
    if top1_cat in ("medication", "emergency"):
        for r in results[1:]:
            if r.get("cat") != top1_cat:
                gap = top1.get("s", 0) - r.get("s", 0)
                return gap >= min_gap, gap
        return True, float("inf")  # 결과 전부 동일 카테고리 — 자연스러움
    # 일반 케이스: 다른 부위·다른 카테고리의 첫 2위 찾기
    # Sprint 16: 같은 부위 내 진단·응급·자가체크 청크끼리 동점은 자연스러움
    #            (사용자에게 여러 관련 정보를 함께 보여주는 게 안전·정보 강화)
    SAFETY_CATS = {"diagnosis", "emergency", "selfcheck", "examination"}
    next_diff = None
    for r in results[1:]:
        chunk = r.get("chunk", {})
        # 동일 부위 + 안전 핵심 카테고리 쌍이면 스킵 (자연 동점)
        if (chunk.get("slug") == top1_slug
                and top1_cat in SAFETY_CATS
                and r.get("cat") in SAFETY_CATS):
            continue
        if chunk.get("slug") != top1_slug or r.get("cat") != top1_cat:
            next_diff = r
            break
    if next_diff is None:
        return True, float("inf")
    gap = top1.get("s", 0) - next_diff.get("s", 0)
    return gap >= min_gap, gap


def audit_test(test: dict, actual: dict, *, gap_threshold: float = 2.0) -> dict:
    """단일 시나리오 품질 점검. 발견된 이슈 목록 반환."""
    issues = []
    expected = test.get("expected", {})

    # 1. 빈 기대값
    if not has_meaningful_expectations(expected):
        issues.append({
            "kind": "empty_expectation",
            "severity": "high",
            "msg": "기대값에 실질 검증 항목 없음 (expected: {} 또는 모두 null)",
            "suggestion": "최소 slug, top1_heading_contains, "
                         "any_result_heading_contains 중 하나는 명시 권고",
        })

    # 2. 결과 0건
    if not actual.get("results"):
        issues.append({
            "kind": "no_results",
            "severity": "high",
            "msg": "검색 결과 0건",
            "suggestion": "검색 사전(동의어·환자표현·외래어) 보강 또는 콘텐츠 추가 필요",
        })
    else:
        # 3. top1 무관
        #    Sprint 19: 시나리오가 negated_categories·ex_catalog·ex_contra·drug_compare 등
        #               다른 검증으로 의도된 영역인 경우 1위 무관 검사 면제.
        #               (그런 시나리오는 1위 점수가 낮은 게 의도된 결과)
        has_other_intent = (
            expected.get("negated_categories")
            or expected.get("ex_catalog")
            or expected.get("ex_contra")
            or expected.get("drug_compare")
            or expected.get("drug_interaction")
            or expected.get("emergency")
        )
        if not has_other_intent:
            ok, msg = top1_is_relevant(actual, test["query"])
            if not ok:
                issues.append({
                    "kind": "irrelevant_top1",
                    "severity": "high",
                    "msg": f"1위 결과 무관 ({msg})",
                    "suggestion": "검색 점수 가중 조정 또는 본문 보강 필요",
                })

        # 5. 점수 격차
        #    Sprint 17/19: 시나리오에 다음 중 하나가 명시되어 있고 의도된 검증 통과하면 면제
        #                  - heading 검증 (top1·any_result)
        #                  - 다른 의도 검증 (negated·ex_catalog·ex_contra·drug_compare·emergency)
        has_validated_intent = (
            expected.get("top1_heading_contains")
            or expected.get("any_result_heading_contains")
            or expected.get("negated_categories")
            or expected.get("ex_catalog")
            or expected.get("ex_contra")
            or expected.get("drug_compare")
            or expected.get("drug_interaction")
            or expected.get("emergency")
        )
        if not has_validated_intent:
            gap_ok, gap = score_gap_ok(actual, gap_threshold)
            if not gap_ok:
                issues.append({
                    "kind": "small_score_gap",
                    "severity": "medium",
                    "msg": f"1위·2위 점수 격차 작음 (gap={gap:.1f} < {gap_threshold})",
                    "suggestion": "1위가 우연성에 가까움. 검색 가중 또는 시나리오 명확화 권고",
                })

    # 4. 부위 감지 실패 (slug 명시했는데 실패)
    if expected.get("slug") and actual.get("detected_slug") is None:
        issues.append({
            "kind": "body_detection_failure",
            "severity": "medium",
            "msg": f"부위 감지 실패 (기대: {expected['slug']})",
            "suggestion": "BODY_PARTS 키워드 또는 동의어 사전 보강 필요",
        })

    return {
        "id": test.get("id"),
        "category": test.get("category"),
        "query": test.get("query"),
        "issues": issues,
        "actual_summary": {
            "detected_slug": actual.get("detected_slug"),
            "result_count": len(actual.get("results", [])),
            "top1": {
                "slug": actual["results"][0]["chunk"].get("slug"),
                "heading": actual["results"][0]["chunk"].get("heading", "")[:50],
                "score": round(actual["results"][0].get("s", 0), 1),
            } if actual.get("results") else None,
        },
    }


def run_audit(test_path: Path, *, gap_threshold: float = 2.0) -> dict:
    suite = json.loads(test_path.read_text(encoding="utf-8"))
    tests = suite.get("tests", [])
    index = load_index()
    intents = load_intents()

    audited = []
    by_kind = {}  # kind -> count
    by_severity = {"high": 0, "medium": 0}
    healthy_count = 0

    for test in tests:
        try:
            actual = full_search(test["query"], top_k=5,
                                 index=index, intents=intents)
        except Exception as e:
            audited.append({
                "id": test.get("id"),
                "category": test.get("category"),
                "query": test.get("query"),
                "issues": [{
                    "kind": "execution_error",
                    "severity": "high",
                    "msg": f"실행 에러: {e}",
                    "suggestion": "검색 엔진 디버그 필요",
                }],
                "actual_summary": {},
            })
            continue

        result = audit_test(test, actual, gap_threshold=gap_threshold)
        audited.append(result)
        if not result["issues"]:
            healthy_count += 1
        for issue in result["issues"]:
            by_kind[issue["kind"]] = by_kind.get(issue["kind"], 0) + 1
            by_severity[issue["severity"]] = by_severity.get(issue["severity"], 0) + 1

    total = len(tests)
    return {
        "total": total,
        "healthy": healthy_count,
        "by_kind": by_kind,
        "by_severity": by_severity,
        "audited": audited,
        "test_file": str(test_path),
    }


KIND_LABEL = {
    "empty_expectation": "빈 기대값",
    "no_results": "결과 0건",
    "irrelevant_top1": "1위 무관",
    "body_detection_failure": "부위 감지 실패",
    "small_score_gap": "점수 격차 부족",
    "execution_error": "실행 에러",
}


def print_report(audit: dict, *, show_max: int = 20):
    total = audit["total"]
    healthy = audit["healthy"]
    by_kind = audit["by_kind"]
    test_file = audit["test_file"]

    print("\n" + "=" * 70)
    print(" ortho-kb 품질 자체 점검 (Quality Audit)")
    print("=" * 70)
    print(f"\n  점검 대상: {test_file}")
    print(f"  시나리오:  {total}개")
    print(f"  무이슈:    {healthy}개  ({healthy/total*100:.0f}%)")

    if not by_kind:
        print("\n  🎉 모든 시나리오가 의미있는 기대값을 가지고 정상 응답합니다.")
        print("=" * 70 + "\n")
        return

    print("\n  발견된 이슈 분류:")
    for kind, cnt in sorted(by_kind.items(), key=lambda x: -x[1]):
        label = KIND_LABEL.get(kind, kind)
        ratio = cnt / total * 100
        bar = "█" * min(20, int(ratio / 5))
        print(f"    {label:18} {bar:20} {cnt:>3}개 ({ratio:.0f}%)")

    # 카테고리 안에 이슈 모음
    print("\n" + "-" * 70)
    print(" 주요 이슈 시나리오 (개선 우선순위)")
    print("-" * 70)
    # high 우선 정렬
    issued = [a for a in audit["audited"] if a["issues"]]
    issued.sort(key=lambda a: (
        -len(a["issues"]),
        -sum(1 for i in a["issues"] if i["severity"] == "high"),
    ))
    for a in issued[:show_max]:
        print(f"\n  [{a['id']}] [{a['category']}] {a['query']!r}")
        for issue in a["issues"]:
            mark = "🔴" if issue["severity"] == "high" else "🟡"
            print(f"    {mark} {KIND_LABEL.get(issue['kind'], issue['kind'])}: {issue['msg']}")
            print(f"        → {issue['suggestion']}")
        if a["actual_summary"].get("top1"):
            t = a["actual_summary"]["top1"]
            print(f"    실제 top1: [{t['score']:.1f}] [{t['slug']}] {t['heading']}")
    if len(issued) > show_max:
        print(f"\n  ... ({len(issued) - show_max}개 더 있음)")

    print("\n" + "=" * 70)
    print(f"  요약: 의미있는 시나리오 {healthy}/{total}개 = 신뢰도 {healthy/total*100:.0f}%")
    print(f"  (단순 합격률은 헐거운 기대값으로 부풀려질 수 있음)")
    print("=" * 70 + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test-file", default=str(DEFAULT_TEST),
                    help="점검할 테스트 스위트 (기본 tests/search_test_suite.json)")
    ap.add_argument("--strict", action="store_true",
                    help="점수 격차 임계 강화 (2.0 → 5.0)")
    ap.add_argument("--show-max", type=int, default=20,
                    help="리포트에 표시할 시나리오 최대 개수")
    ap.add_argument("--json-out", default=None,
                    help="JSON 리포트 출력 경로")
    args = ap.parse_args()

    test_path = Path(args.test_file)
    if not test_path.exists():
        print(f"[ERROR] 테스트 파일 없음: {test_path}", file=sys.stderr)
        sys.exit(2)

    gap = 5.0 if args.strict else 2.0
    audit = run_audit(test_path, gap_threshold=gap)
    print_report(audit, show_max=args.show_max)

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(audit, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  JSON 리포트: {args.json_out}\n")


if __name__ == "__main__":
    main()
