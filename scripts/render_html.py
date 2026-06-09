"""
render_html.py — ortho-kb 마크다운 → HTML 렌더러 (Sprint 6 SEO 강화)

핵심 기능:
1) YAML front matter 파싱
2) 마크다운 → HTML
3) 면책 배너 자동 삽입
4) SEO 메타 자동 삽입 (data/seo_meta.json 기반)
   - <meta description>, keywords
   - Open Graph, Twitter Card
   - Canonical URL
5) JSON-LD 구조화 데이터
   - MedicalWebPage (의료 콘텐츠 전용)
   - BreadcrumbList
   - FAQPage
6) Breadcrumb UI 자동 삽입
7) 본문 끝에 FAQ 섹션 자동 삽입
"""
from __future__ import annotations
import sys
import re
import json
import argparse
from pathlib import Path

try:
    import yaml
    import markdown
except ImportError as e:
    print(f"[render_html] 의존성 누락: {e}", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
SEO_META_PATH = ROOT / "data" / "seo_meta.json"

SLUG_TITLE = {
    "shoulder": "어깨", "knee": "무릎", "ankle": "발목",
    "foot": "발바닥", "wrist": "손목", "lowback": "허리",
}
SLUG_TO_FILENAME = {
    "shoulder": "01_shoulder", "knee": "02_knee", "ankle": "03_ankle",
    "foot": "04_foot", "wrist": "05_wrist", "lowback": "06_lowback",
}

DISCLAIMER_BANNER_HTML = """
<div class="ortho-disclaimer">
  <strong>⚠️ 본 문서는 교육 목적의 정보입니다.</strong>
  진단·처방을 대체하지 않습니다. 증상이 지속·악화되면
  정형외과 전문의 진료를 받으세요.
  <a href="../DISCLAIMER.html">전체 면책 조항 →</a>
</div>
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{seo_title}</title>
<meta name="description" content="{seo_description}">
<meta name="keywords" content="{seo_keywords}">
<meta name="author" content="{seo_publisher}">
<link rel="canonical" href="{canonical_url}">

<!-- Open Graph (카카오톡·페이스북·LinkedIn 공유 시 미리보기) -->
<meta property="og:type" content="article">
<meta property="og:title" content="{seo_title}">
<meta property="og:description" content="{seo_description}">
<meta property="og:url" content="{canonical_url}">
<meta property="og:site_name" content="{seo_site_name}">
<meta property="og:locale" content="ko_KR">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{seo_title}">
<meta name="twitter:description" content="{seo_description}">

<link rel="stylesheet" href="../assets/style.css">

<!-- JSON-LD: MedicalWebPage (Google 의료 콘텐츠 E-E-A-T 우대) -->
<script type="application/ld+json">
{jsonld_medical}
</script>

<!-- JSON-LD: BreadcrumbList -->
<script type="application/ld+json">
{jsonld_breadcrumb}
</script>
{jsonld_faq_block}
</head>
<body>
<header class="ortho-header">
  <nav class="ortho-breadcrumb" aria-label="breadcrumb">
    <a href="../index.html">홈</a> ›
    <span aria-current="page">{title} 통증</span>
  </nav>
  <span class="ortho-version">v{version} · 최종수정: {last_updated}</span>
</header>
<main class="ortho-main">
{body_html}
</main>
<footer class="ortho-footer">
  <div>작성자: {authors_str}</div>
  <div>검수: {reviewer}</div>
  <div>라이선스: {license}</div>
  <div><a href="../search/">🔍 위키 검색</a> · <a href="../DISCLAIMER.html">면책 조항</a></div>
</footer>
</body>
</html>
"""


def parse_front_matter(text: str) -> tuple[dict, str]:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if not m:
        raise ValueError("YAML front matter 누락")
    meta = yaml.safe_load(m.group(1)) or {}
    return meta, m.group(2)


def inject_disclaimer(body_md: str) -> str:
    if "<!-- DISCLAIMER_BANNER_AUTO -->" in body_md:
        return body_md.replace("<!-- DISCLAIMER_BANNER_AUTO -->", DISCLAIMER_BANNER_HTML)
    return re.sub(r"(^# .+\n)", r"\1\n" + DISCLAIMER_BANNER_HTML + "\n",
                  body_md, count=1, flags=re.MULTILINE)


def md_to_html(body_md: str) -> str:
    return markdown.markdown(
        inject_disclaimer(body_md),
        extensions=["tables", "fenced_code", "toc", "sane_lists"],
        output_format="html5",
    )


def format_authors(meta: dict) -> str:
    authors = meta.get("authors", []) or []
    return ", ".join(f"{a.get('role', '?')}({a.get('name', 'TBD')})" for a in authors)


def load_seo_meta() -> dict:
    if not SEO_META_PATH.exists():
        return {"site": {}, "pages": {}, "faq": {}}
    return json.loads(SEO_META_PATH.read_text(encoding="utf-8"))


def build_jsonld_medical(seo_site: dict, page_seo: dict, canonical: str,
                         title: str, last_updated: str) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "MedicalWebPage",
        "name": page_seo.get("title_seo", title),
        "url": canonical,
        "description": page_seo.get("description", ""),
        "inLanguage": "ko-KR",
        "datePublished": "2026-06-06",
        "dateModified": str(last_updated),
        "publisher": {
            "@type": "Organization",
            "name": seo_site.get("name", "ortho-kb"),
            "url": seo_site.get("url", ""),
        },
        "about": {
            "@type": "MedicalCondition",
            "name": title + " 통증",
        },
        "audience": {
            "@type": "MedicalAudience",
            "audienceType": "Patient",
        },
        "specialty": {
            "@type": "MedicalSpecialty",
            "name": "Orthopedic",
        },
        "lastReviewed": str(last_updated),
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def build_jsonld_breadcrumb(site_url: str, title: str, page_url: str) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "ortho-kb 홈",
             "item": site_url + "/"},
            {"@type": "ListItem", "position": 2, "name": f"{title} 통증",
             "item": page_url},
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def build_jsonld_faq(faq_items: list[dict]) -> str:
    if not faq_items:
        return ""
    data = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item["q"],
                "acceptedAnswer": {"@type": "Answer", "text": item["a"]},
            } for item in faq_items
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def append_faq_section(html: str, faq_items: list[dict]) -> str:
    if not faq_items:
        return html
    lines = ['<section class="ortho-faq"><h2>자주 묻는 질문 (FAQ)</h2>']
    for item in faq_items:
        lines.append(
            f'  <details class="ortho-faq-item">\n'
            f'    <summary>{item["q"]}</summary>\n'
            f'    <div class="ortho-faq-answer">{item["a"]}</div>\n'
            f'  </details>'
        )
    lines.append('</section>')
    return html + "\n" + "\n".join(lines) + "\n"


def render(md_path: Path, out_dir: Path) -> Path:
    raw = md_path.read_text(encoding="utf-8")
    meta, body_md = parse_front_matter(raw)
    body_html = md_to_html(body_md)

    seo_all = load_seo_meta()
    seo_site = seo_all.get("site", {})
    slug = meta.get("slug", md_path.stem)
    page_seo = seo_all.get("pages", {}).get(slug, {})
    faq_items = seo_all.get("faq", {}).get(slug, [])

    site_url = seo_site.get("url", "https://example.com")
    fname = SLUG_TO_FILENAME.get(slug, md_path.stem)
    canonical = f"{site_url}/body/{fname}.html"
    title = meta.get("title", slug)
    last_updated = meta.get("last_updated", "unknown")

    if faq_items:
        body_html = append_faq_section(body_html, faq_items)
        faq_jsonld = build_jsonld_faq(faq_items)
        jsonld_faq_block = f'\n<script type="application/ld+json">\n{faq_jsonld}\n</script>'
    else:
        jsonld_faq_block = ""

    html = HTML_TEMPLATE.format(
        seo_title=page_seo.get("title_seo", f"{title} · ortho-kb"),
        seo_description=page_seo.get("description", seo_site.get("description_ko", "")),
        seo_keywords=", ".join(page_seo.get("keywords", [])) or seo_site.get("keywords_ko", ""),
        seo_publisher=seo_site.get("publisher", "ortho-kb"),
        seo_site_name=seo_site.get("name_ko", "ortho-kb"),
        canonical_url=canonical,
        title=title,
        version=meta.get("version", "0.0.0"),
        last_updated=last_updated,
        body_html=body_html,
        authors_str=format_authors(meta),
        reviewer=meta.get("reviewer", "TBD"),
        license=meta.get("license", "CC BY-NC-SA 4.0"),
        jsonld_medical=build_jsonld_medical(seo_site, page_seo, canonical, title, last_updated),
        jsonld_breadcrumb=build_jsonld_breadcrumb(site_url, title, canonical),
        jsonld_faq_block=jsonld_faq_block,
    )
    out_path = out_dir / (md_path.stem + ".html")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("md_path", type=Path)
    p.add_argument("--out", type=Path, default=Path("docs/body"))
    args = p.parse_args()
    if not args.md_path.exists():
        print(f"[render_html] 파일 없음: {args.md_path}", file=sys.stderr)
        sys.exit(2)
    print(f"[render_html] {args.md_path} → {render(args.md_path, args.out)}")


if __name__ == "__main__":
    main()
