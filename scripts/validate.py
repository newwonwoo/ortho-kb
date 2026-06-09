"""
validate.py — ortho-kb 콘텐츠 자동 검증

검사 항목 (STYLE_GUIDE.md §10):
  1) YAML front matter 존재 + 필수 필드
  2) H1 1개만 존재
  3) 면책 배너 자리(<!-- DISCLAIMER_BANNER_AUTO --> 또는 H1 직후) 존재
  4) 섹션 0~7 모두 존재
  5) 약물 섹션에 출처 2개 이상 (DOI/PMID/URL)
  6) 단정형 금지 표현 검출
  7) last_updated 6개월 이내

종료코드: 0=합격, 1=경고, 2=실패
"""
from __future__ import annotations
import sys
import re
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field

try:
    import yaml
except ImportError:
    print("[validate] PyYAML 설치 필요", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
BODY_MD = ROOT / "body_md"

REQUIRED_META = ["slug", "title", "authors", "reviewer", "last_updated", "version", "license"]

REQUIRED_SECTIONS = [
    "## 0. 해부학 개요",
    "## 1. 흔한 증상",          # 부분 일치 허용
    "## 2. 자가 체크리스트",
    "## 3. 진단",
    "## 4. 치료",
    "## 5. 수술",
    "## 6.",                     # 참고문헌 (제목 변형 허용)
    "## 7. 작성",                # 작성·검토·최종수정일
]

# 단정형 금지 표현 (감사역 워치리스트)
FORBIDDEN_PATTERNS = [
    r"반드시\s+\S+해야\s*한다",
    r"\S+로\s+치료한다(?!\s*는)",   # "~로 치료한다" 단정 (인용 제외)
    r"\S+를\s+처방한다(?!\s*는)",
    r"정답이다",
    r"틀림없이",
    r"100%\s*효과",
]

# 출처 패턴 (느슨한 매칭)
SOURCE_PATTERNS = [
    r"doi:\s*10\.\S+",
    r"PMID:\s*\d+",
    r"https?://\S+",
    r"NICE\s+Guideline",
    r"식약처",
    r"Cochrane",
    r"AAOS",
    r"UpToDate",
    r"Lexicomp",
]


@dataclass
class FileResult:
    path: Path
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.errors

    def summary(self) -> str:
        status = "✅ PASS" if self.passed else "❌ FAIL"
        if self.warnings and self.passed:
            status = "⚠️ WARN"
        return f"{status}  {self.path.name}  (errors={len(self.errors)}, warnings={len(self.warnings)})"


def check_file(md_path: Path) -> FileResult:
    r = FileResult(path=md_path)
    raw = md_path.read_text(encoding="utf-8")

    # 1) front matter
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, re.DOTALL)
    if not m:
        r.errors.append("YAML front matter 누락")
        return r
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        r.errors.append(f"YAML 파싱 실패: {e}")
        return r
    body = m.group(2)

    for k in REQUIRED_META:
        if k not in meta:
            r.errors.append(f"front matter 필수키 누락: {k}")

    # 2) H1 1개
    h1s = re.findall(r"^# .+$", body, re.MULTILINE)
    if len(h1s) != 1:
        r.errors.append(f"H1 제목은 정확히 1개여야 합니다 (현재 {len(h1s)}개)")

    # 3) 면책 배너 자리
    if "<!-- DISCLAIMER_BANNER_AUTO -->" not in body:
        r.warnings.append("면책 배너 자리 마커 없음 — H1 직후 자동 삽입으로 폴백됨")

    # 4) 섹션 존재
    for sec_prefix in REQUIRED_SECTIONS:
        if sec_prefix not in body:
            r.errors.append(f"필수 섹션 누락: '{sec_prefix}'")

    # 5) 약물 섹션 출처 2개 이상
    drug_match = re.search(r"### 4\.1 약물.*?(?=^### 4\.2)", body, re.DOTALL | re.MULTILINE)
    if drug_match:
        drug_block = drug_match.group(0)
        source_hits = sum(len(re.findall(pat, drug_block, re.IGNORECASE)) for pat in SOURCE_PATTERNS)
        if source_hits < 2:
            r.errors.append(f"약물 섹션 출처 부족 ({source_hits}개, 최소 2개)")
    else:
        r.warnings.append("약물 섹션(### 4.1 약물) 구조 매칭 실패")

    # 6) 단정형 표현
    for pat in FORBIDDEN_PATTERNS:
        hits = re.findall(pat, body)
        if hits:
            r.warnings.append(f"단정형 의심 표현: {pat} → {hits[:3]}")

    # 7) last_updated 6개월 이내
    lu = meta.get("last_updated")
    if isinstance(lu, str):
        try:
            lu_dt = datetime.strptime(lu, "%Y-%m-%d")
        except ValueError:
            r.warnings.append(f"last_updated 형식 오류: {lu} (YYYY-MM-DD 기대)")
            lu_dt = None
    elif hasattr(lu, "year"):
        # YAML이 date 객체로 파싱한 경우
        lu_dt = datetime(lu.year, lu.month, lu.day)
    else:
        lu_dt = None
        r.warnings.append("last_updated 누락")
    if lu_dt and (datetime.now() - lu_dt) > timedelta(days=183):
        r.warnings.append(f"last_updated 6개월 초과: {lu}")

    return r


def main():
    files = sorted(BODY_MD.glob("*.md"))
    if not files:
        print("[validate] 검사 대상 없음")
        sys.exit(0)

    results = [check_file(f) for f in files]
    total_errors = sum(len(r.errors) for r in results)
    total_warnings = sum(len(r.warnings) for r in results)

    print("─" * 60)
    print("ortho-kb validation report")
    print("─" * 60)
    for r in results:
        print(r.summary())
        for e in r.errors:
            print(f"   ✗ ERROR: {e}")
        for w in r.warnings:
            print(f"   ! WARN : {w}")
    print("─" * 60)
    print(f"총 파일: {len(results)}, 합격: {sum(1 for r in results if r.passed)}, "
          f"실패: {sum(1 for r in results if not r.passed)}, "
          f"오류: {total_errors}, 경고: {total_warnings}")

    if total_errors > 0:
        sys.exit(2)
    if total_warnings > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
