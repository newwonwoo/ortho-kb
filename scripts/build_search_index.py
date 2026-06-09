"""
build_search_index.py — body_md/*.md를 청크 단위로 잘라 검색 인덱스 생성.

API 호출 없음. 모든 검색은 클라이언트 JS에서 정적 인덱스로 처리.

청크 전략:
- 각 마크다운을 H3(### 또는 ####) 단위로 분리
- 각 청크에 부위·섹션·앵커·내용 메타 부여
- 출력: docs/search/index.json

토크나이저(한국어):
- 단순 어절 + 영문 단어 동시 추출. 형태소 분석 미사용(라이브러리 의존 회피).
- 클라이언트에서 동일 토크나이저 사용해야 매칭 가능 → search.js와 동기화.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BODY_MD = ROOT / "body_md"
OUT = ROOT / "docs" / "search" / "index.json"

# YAML front matter 추출
FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)

# 청크 분리: H2 또는 H3 헤더 기준
SECTION_RE = re.compile(r"^(#{2,4})\s+(.+)$", re.MULTILINE)


def split_chunks(body: str, slug: str, title: str) -> list[dict]:
    """헤더 기준으로 본문을 청크로 분리. 청크 = 헤더 + 다음 헤더 전까지."""
    headers = list(SECTION_RE.finditer(body))
    chunks = []
    for i, m in enumerate(headers):
        level = len(m.group(1))
        heading = m.group(2).strip()
        start = m.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(body)
        content = body[start:end].strip()
        # 빈 청크 또는 TODO만 있는 청크는 제외
        plain = re.sub(r"\s+", " ", content)
        if not plain or plain.startswith("TODO"):
            continue
        chunk_id = f"{slug}__{i}"
        anchor = re.sub(r"[^\w가-힣\-]", "-", heading).strip("-").lower()
        chunks.append({
            "id": chunk_id,
            "slug": slug,
            "title": title,
            "level": level,
            "heading": heading,
            "anchor": anchor,
            "url": f"body/{slug_to_filename(slug)}.html#{anchor}",
            "text": content[:1200],   # 응답 표시용 발췌
            "tokens": tokenize(heading + " " + content),
        })
    return chunks


SLUG_TO_FNAME = {
    "shoulder": "01_shoulder", "knee": "02_knee", "ankle": "03_ankle",
    "foot": "04_foot", "wrist": "05_wrist", "lowback": "06_lowback",
}


def slug_to_filename(slug: str) -> str:
    return SLUG_TO_FNAME.get(slug, slug)


# 한국어·영문 동시 토크나이저
KOREAN_WORD = re.compile(r"[가-힣]+")            # 길이 제한은 조사 분리 후 적용
ENG_WORD = re.compile(r"[A-Za-z]{2,}")            # 2글자 이상 영문 토큰

# 한국어 조사 (긴 것부터 매칭해서 "에서"가 "에"로 잘리는 일 방지)
KOREAN_PARTICLES = sorted([
    # 부사격·접속
    "에서는", "에서도", "에서", "으로", "에게서", "에게", "에는", "에도", "에",
    "와는", "과는", "와", "과", "랑", "이랑", "처럼", "같이", "보다", "마저",
    # 주격·목적격·보격
    "께서는", "께서", "이가", "가", "이", "을", "를",
    # 보조사
    "은", "는", "도", "만", "조차", "마다", "뿐", "라도", "이라도",
    # 소유격
    "의",
    # 서술격·종결
    "이다", "입니다", "이며", "이고", "이고요", "이에요", "예요",
    "있어요", "있어", "있다", "없어", "없다", "있는", "없는",
    "한다", "합니다", "해요", "한", "할", "함",
    # 일반 종결
    "다", "요", "지", "네", "야", "어", "아", "냐", "요",
    # 시제·태
    "었다", "었던", "였다", "였던", "겠다", "겠습니다",
], key=len, reverse=True)


def strip_particle(word: str) -> str:
    """어절 끝의 한국어 조사 제거. 어간 길이 2 이상 유지."""
    for p in KOREAN_PARTICLES:
        if word.endswith(p) and len(word) - len(p) >= 2:
            return word[:-len(p)]
    return word


def tokenize(text: str) -> list[str]:
    """한글 어절 + 조사 제거한 어간 + 영문 토큰 동시 저장.
    예) "어깨를" → ["어깨를", "어깨"] 모두 인덱싱.
    검색 시 사용자 입력에도 동일한 strip_particle 적용."""
    tokens = set()
    for m in KOREAN_WORD.finditer(text):
        word = m.group(0)
        if len(word) >= 2:
            tokens.add(word)               # 원형 (예: "어깨를")
        stem = strip_particle(word)
        if len(stem) >= 2 and stem != word:
            tokens.add(stem)               # 어간 (예: "어깨")
    for m in ENG_WORD.finditer(text.lower()):
        tokens.add(m.group(0))
    return sorted(tokens)


def build_index() -> list[dict]:
    # 동의어 사전 로드 (SEO 전문가 정의)
    synonyms = load_synonyms()
    chunks: list[dict] = []
    for md_path in sorted(BODY_MD.glob("*.md")):
        raw = md_path.read_text(encoding="utf-8")
        m = FM_RE.match(raw)
        if not m:
            print(f"[skip] {md_path.name}: front matter 누락", file=sys.stderr)
            continue
        meta_text, body = m.group(1), m.group(2)
        slug_m = re.search(r"slug:\s*(\S+)", meta_text)
        title_m = re.search(r"title:\s*(\S+)", meta_text)
        slug = slug_m.group(1) if slug_m else md_path.stem
        title = title_m.group(1) if title_m else slug
        page_chunks = split_chunks(body, slug, title)
        # 동의어 토큰 확장
        page_syns = synonyms.get(slug, {})
        for chunk in page_chunks:
            extra_tokens = set(chunk["tokens"])
            for canonical_term, variants in page_syns.items():
                # 청크에 canonical term 또는 variant가 등장하면 모든 variant 토큰 추가
                has_match = any(
                    v in chunk["text"] or v in chunk["heading"]
                    for v in [canonical_term] + variants
                )
                if has_match:
                    for v in [canonical_term] + variants:
                        for tok in tokenize(v):
                            extra_tokens.add(tok)
            chunk["tokens"] = sorted(extra_tokens)
        chunks.extend(page_chunks)
        print(f"  {md_path.name}: {len(page_chunks)}개 청크 (동의어 확장 적용)")
    return chunks


def load_synonyms() -> dict:
    """동의어 사전 통합 로드.
    우선순위: data/search_intents.json > data/intents.json > data/seo_meta.json.
    구조: { slug: { canonical_term: [variants...], ... }, ... }"""
    result: dict[str, dict] = {}
    # 1) intents 파일 — search_intents.json 또는 intents.json
    intents_path = None
    for candidate in ["search_intents.json", "intents.json"]:
        p = ROOT / "data" / candidate
        if p.exists():
            intents_path = p
            break
    if intents_path:
        try:
            d = json.loads(intents_path.read_text(encoding="utf-8"))
            for slug, syns in d.get("body_synonyms", {}).items():
                result.setdefault(slug, {})
                for term, vars_ in syns.items():
                    if term.startswith("_"):
                        continue
                    result[slug][term] = vars_
            # 글로벌 동의어 추가
            global_syns = d.get("global_synonyms", {})
            for slug in result:
                for term, vars_ in global_syns.items():
                    if term.startswith("_"):
                        continue
                    result[slug][term] = vars_
            # Sprint 7 — 환자 표현 + 외래어 사전을 모든 부위에 글로벌 적용
            #  (환자 표현이 어떤 부위에 매칭될지는 표현에 포함된 부위 키워드로 자동 판별됨)
            for sect_name in ["patient_phrases", "loanword_dictionary"]:
                sect = d.get(sect_name, {})
                if not isinstance(sect, dict):
                    continue
                for slug in result:
                    for term, vars_ in sect.items():
                        if term.startswith("_") or not isinstance(vars_, list):
                            continue
                        if term not in result[slug]:
                            result[slug][term] = vars_
            print(f"[synonyms] {intents_path.name} 로드 ({sum(len(v) for v in result.values())}개 매핑)")
        except Exception as e:
            print(f"[synonyms] {intents_path.name} 로드 실패: {e}", file=sys.stderr)
    # 2) seo_meta.json (백업)
    seo_path = ROOT / "data" / "seo_meta.json"
    if seo_path.exists():
        try:
            d = json.loads(seo_path.read_text(encoding="utf-8"))
            for slug, page in d.get("pages", {}).items():
                result.setdefault(slug, {})
                for term, vars_ in page.get("synonyms", {}).items():
                    if term not in result[slug]:
                        result[slug][term] = vars_
        except Exception as e:
            print(f"[synonyms] seo_meta.json 로드 실패: {e}", file=sys.stderr)
    return result


def main():
    chunks = build_index()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps({"version": "0.2", "chunks": chunks}, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    print(f"[build_search_index] {OUT} ({len(chunks)} chunks)")
    # intents 파일을 docs/search/intents.json으로 복사 (클라이언트 챗봇이 로딩)
    import shutil
    for candidate in ["search_intents.json", "intents.json"]:
        src = ROOT / "data" / candidate
        if src.exists():
            dst = OUT.parent / "intents.json"
            shutil.copy(src, dst)
            print(f"[build_search_index] intents 복사: {src.name} → {dst}")
            break


if __name__ == "__main__":
    main()
