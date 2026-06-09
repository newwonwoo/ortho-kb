"""
generate_quality_report.py — quality_audit + tighten 결과를 합쳐 사람 검토용 보고서 생성.

용도:
  자동 보강이 안 되는 시나리오들의 패턴·원인을 모아서
  콘텐츠 보강 또는 검색 사전 보강 우선순위 결정에 사용.

사용:
    python scripts/generate_quality_report.py --out reports/quality_review.md
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from search_engine import full_search, load_index, load_intents  # noqa: E402

SUITES = [
    ("일반", ROOT / "tests" / "search_test_suite.json"),
    ("약물", ROOT / "tests" / "drug_test_suite.json"),
    ("운동", ROOT / "tests" / "exercise_test_suite.json"),
    ("응급·진단", ROOT / "tests" / "emergency_diagnosis_test_suite.json"),
]


def has_meaningful_expectations(expected: dict) -> bool:
    if not expected:
        return False
    keys = {
        "slug", "emergency", "time_stage", "drug_compare", "ex_contra",
        "top1_slug", "top1_heading_contains", "top1_category",
        "any_result_heading_contains", "negated_categories",
    }
    return any(k in expected and expected[k] is not None for k in keys)


def analyze_suite(name: str, path: Path) -> dict:
    suite = json.loads(path.read_text(encoding="utf-8"))
    tests = suite.get("tests", [])
    index = load_index()
    intents = load_intents()

    # 카테고리별 보류 분석
    empty_no_results = []        # 빈 기대값 + 결과 0건 (콘텐츠 부재)
    empty_weak_top1 = []         # 빈 기대값 + 1위 약함 (검색·콘텐츠 보강 후보)
    empty_strong_top1 = []       # 빈 기대값 + 1위 명확 (보강 가능했어야 — 격차 부족)

    for t in tests:
        if has_meaningful_expectations(t.get("expected") or {}):
            continue
        try:
            actual = full_search(t["query"], top_k=5, index=index, intents=intents)
        except Exception:
            continue
        results = actual.get("results", [])
        if not results:
            empty_no_results.append({"id": t["id"], "category": t["category"], "query": t["query"]})
            continue
        top1 = results[0]
        gap = top1["s"] - (results[1]["s"] if len(results) > 1 else 0)
        if top1["s"] < 6.0:
            empty_weak_top1.append({
                "id": t["id"], "category": t["category"], "query": t["query"],
                "top1_score": round(top1["s"], 1),
                "top1_heading": top1["chunk"]["heading"][:50],
                "top1_slug": top1["chunk"]["slug"],
            })
        elif gap < 2.0:
            empty_strong_top1.append({
                "id": t["id"], "category": t["category"], "query": t["query"],
                "top1_score": round(top1["s"], 1),
                "gap": round(gap, 1),
                "top1_heading": top1["chunk"]["heading"][:50],
                "top1_slug": top1["chunk"]["slug"],
            })

    return {
        "suite_name": name,
        "total": len(tests),
        "empty_no_results": empty_no_results,
        "empty_weak_top1": empty_weak_top1,
        "empty_strong_top1": empty_strong_top1,
    }


def render_markdown(suites_data: list[dict]) -> str:
    lines = []
    lines.append("# ortho-kb 품질 보강 검토 보고서")
    lines.append("")
    lines.append("> 자동 보강이 안 된 시나리오의 사람 검토용 정리.")
    lines.append("> 3가지 분류로 우선순위를 잡는다.")
    lines.append("")

    lines.append("## 📊 전체 요약")
    lines.append("")
    lines.append("| 스위트 | 총 | 결과 0건 | 1위 약함 | 1위 명확·격차 부족 |")
    lines.append("|---|---|---|---|---|")
    for s in suites_data:
        lines.append(f"| {s['suite_name']} | {s['total']} | "
                     f"{len(s['empty_no_results'])} | "
                     f"{len(s['empty_weak_top1'])} | "
                     f"{len(s['empty_strong_top1'])} |")
    lines.append("")

    lines.append("## 🔴 우선순위 1: 결과 0건 (콘텐츠 부재)")
    lines.append("")
    lines.append("> 검색 결과가 아예 없음 = 사용자가 빈 화면을 본다.")
    lines.append("> **콘텐츠 추가 또는 검색 사전 보강 필요**.")
    lines.append("")
    has_any = False
    for s in suites_data:
        if not s["empty_no_results"]:
            continue
        has_any = True
        lines.append(f"### {s['suite_name']}")
        for item in s["empty_no_results"]:
            lines.append(f"- `{item['id']}` [{item['category']}] {item['query']!r}")
        lines.append("")
    if not has_any:
        lines.append("**없음** — 모든 시나리오가 최소 1개의 결과를 반환합니다.")
        lines.append("")

    lines.append("## 🟡 우선순위 2: 1위 점수 약함 (< 6.0)")
    lines.append("")
    lines.append("> 검색이 답을 찾긴 했지만 점수가 약함 = 우연 매칭 가능성.")
    lines.append("> **검색 사전(동의어·키워드) 보강 또는 본문 보강 후보**.")
    lines.append("")
    for s in suites_data:
        if not s["empty_weak_top1"]:
            continue
        lines.append(f"### {s['suite_name']} ({len(s['empty_weak_top1'])}건)")
        lines.append("")
        lines.append("| ID | 카테고리 | 쿼리 | 1위 점수 | 1위 청크 |")
        lines.append("|---|---|---|---|---|")
        for item in s["empty_weak_top1"]:
            lines.append(f"| `{item['id']}` | {item['category']} | "
                         f"{item['query']!r} | {item['top1_score']} | "
                         f"[{item['top1_slug']}] {item['top1_heading']} |")
        lines.append("")

    lines.append("## 🟢 우선순위 3: 1위 명확하지만 격차 부족")
    lines.append("")
    lines.append("> 1위 점수는 충분히 높지만 2위와의 격차가 작음 = 안정성 부족.")
    lines.append("> **검색 점수 가중 조정 또는 시나리오 명확화** (예: any_result_heading_contains 명시).")
    lines.append("")
    for s in suites_data:
        if not s["empty_strong_top1"]:
            continue
        lines.append(f"### {s['suite_name']} ({len(s['empty_strong_top1'])}건)")
        lines.append("")
        lines.append("| ID | 카테고리 | 쿼리 | 1위 | 격차 | 1위 청크 |")
        lines.append("|---|---|---|---|---|---|")
        for item in s["empty_strong_top1"]:
            lines.append(f"| `{item['id']}` | {item['category']} | "
                         f"{item['query']!r} | {item['top1_score']} | {item['gap']} | "
                         f"[{item['top1_slug']}] {item['top1_heading']} |")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("### 권고 행동")
    lines.append("")
    lines.append("1. **우선순위 1**: 가장 큰 위험. 콘텐츠 보강 또는 동의어 사전 추가.")
    lines.append("2. **우선순위 2**: 검색 사전 보강 후 자동 보강 재실행으로 해결 가능.")
    lines.append("3. **우선순위 3**: 시나리오에 `any_result_heading_contains: [...]` 추가하여 명시.")
    lines.append("")

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "reports" / "quality_review.md"),
                    help="보고서 출력 경로 (기본 reports/quality_review.md)")
    args = ap.parse_args()

    suites_data = [analyze_suite(name, path) for name, path in SUITES]

    md = render_markdown(suites_data)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding="utf-8")
    print(f"\n  품질 검토 보고서: {out_path}")

    # 요약 한 줄
    total_no_results = sum(len(s["empty_no_results"]) for s in suites_data)
    total_weak = sum(len(s["empty_weak_top1"]) for s in suites_data)
    total_strong = sum(len(s["empty_strong_top1"]) for s in suites_data)
    print(f"\n  요약: 우선순위1={total_no_results} / 우선순위2={total_weak} / 우선순위3={total_strong}")


if __name__ == "__main__":
    main()
