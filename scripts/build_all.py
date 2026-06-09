"""
build_all.py — body_md/*.md 전체를 docs/body/*.html로 일괄 렌더링.

추가로 docs/index.html(부위 목록 페이지)도 생성.
"""
from __future__ import annotations
import sys
from pathlib import Path

# render_html.render 직접 import
sys.path.insert(0, str(Path(__file__).parent))
from render_html import render, parse_front_matter  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
BODY_MD = ROOT / "body_md"
DOCS = ROOT / "docs"
DOCS_BODY = DOCS / "body"

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ortho-kb · 정형외과 통증 위키 (어깨·무릎·발목·발바닥·손목·허리)</title>
<meta name="description" content="어깨·무릎·발목·발바닥·손목·허리 통증의 진단과 치료(약물·물리치료·재활운동)를 정리한 정형외과 한국어 위키. 교육 목적이며 전문의 진료를 대체하지 않습니다.">
<meta name="keywords" content="정형외과, 통증, 위키, 어깨 통증, 무릎 통증, 발목 통증, 발바닥 통증, 손목 통증, 허리 통증, 진단, 치료, 재활운동, 스트레칭">
<link rel="canonical" href="https://newwonwoo.github.io/ortho-kb/">

<meta property="og:type" content="website">
<meta property="og:title" content="ortho-kb · 정형외과 통증 위키">
<meta property="og:description" content="6부위 정형외과 통증의 진단·치료·재활운동 위키">
<meta property="og:url" content="https://newwonwoo.github.io/ortho-kb/">
<meta property="og:site_name" content="ortho-kb">
<meta property="og:locale" content="ko_KR">
<meta name="twitter:card" content="summary">

<link rel="stylesheet" href="assets/style.css">

<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "ortho-kb",
  "alternateName": "정형외과 증상 위키",
  "url": "https://newwonwoo.github.io/ortho-kb/",
  "inLanguage": "ko-KR",
  "description": "어깨·무릎·발목·발바닥·손목·허리 통증의 진단과 치료를 정리한 한국어 정형외과 위키",
  "potentialAction": {{
    "@type": "SearchAction",
    "target": "https://newwonwoo.github.io/ortho-kb/search/?q={{search_term_string}}",
    "query-input": "required name=search_term_string"
  }}
}}
</script>
</head>
<body>
<header class="ortho-header">
  <h1>ortho-kb · 정형외과 통증 위키</h1>
  <div class="ortho-disclaimer">
    ⚠️ 본 위키는 교육 목적입니다. 진단·처방을 대체하지 않습니다.
    <a href="DISCLAIMER.html">전체 면책 조항 →</a>
  </div>
</header>
<main class="ortho-main">
  <p style="margin: 1rem 0;">
    <a href="search/" style="display:inline-block;padding:0.6rem 1rem;background:#1d4ed8;color:white;border-radius:8px;text-decoration:none;font-weight:600;">🔍 위키 검색 (챗봇)</a>
  </p>
  <h2>부위별 페이지</h2>
  <ul class="ortho-body-list">
{items}
  </ul>
</main>
<footer class="ortho-footer">
  <a href="https://github.com/newwonwoo/ortho-kb">GitHub</a> ·
  콘텐츠 CC BY-NC-SA 4.0 · 코드 MIT
</footer>
</body>
</html>
"""


def collect_pages() -> list[dict]:
    """body_md/*.md 의 메타데이터 수집 후 파일명 순 정렬."""
    pages = []
    for md_path in sorted(BODY_MD.glob("*.md")):
        meta, _ = parse_front_matter(md_path.read_text(encoding="utf-8"))
        pages.append({
            "slug": meta.get("slug", md_path.stem),
            "title": meta.get("title", md_path.stem),
            "version": meta.get("version", "0.0.0"),
            "last_updated": meta.get("last_updated", "unknown"),
            "filename": md_path.stem + ".html",
            "md_path": md_path,
        })
    return pages


def build_index(pages: list[dict]) -> Path:
    items = "\n".join(
        f'    <li><a href="body/{p["filename"]}">{p["title"]}</a> '
        f'<small>v{p["version"]} · {p["last_updated"]}</small></li>'
        for p in pages
    )
    html = INDEX_TEMPLATE.format(items=items)
    out = DOCS / "index.html"
    out.write_text(html, encoding="utf-8")
    return out


def main():
    if not BODY_MD.exists():
        print(f"[build_all] body_md/ 없음: {BODY_MD}", file=sys.stderr)
        sys.exit(2)

    pages = collect_pages()
    if not pages:
        print("[build_all] 렌더할 마크다운 없음", file=sys.stderr)
        sys.exit(0)

    print(f"[build_all] {len(pages)}개 페이지 빌드 시작")
    for p in pages:
        out = render(p["md_path"], DOCS_BODY)
        print(f"  ✓ {p['title']} → {out.name}")

    idx = build_index(pages)
    print(f"[build_all] 인덱스: {idx}")

    # ─── assets/svg_exercises를 docs로 복사 (정적 배포용) ───
    import shutil
    svg_src = ROOT / "assets" / "svg_exercises"
    if svg_src.exists():
        svg_dst = DOCS / "assets" / "svg_exercises"
        if svg_dst.exists():
            shutil.rmtree(svg_dst)
        shutil.copytree(svg_src, svg_dst)
        print(f"[build_all] SVG 자산 복사: {svg_dst} ({len(list(svg_dst.glob('*.svg')))}개)")

    # ─── DISCLAIMER.md → docs/DISCLAIMER.html ───
    disclaimer_md = ROOT / "DISCLAIMER.md"
    if disclaimer_md.exists():
        import markdown as md_lib
        body_html = md_lib.markdown(
            disclaimer_md.read_text(encoding="utf-8"),
            extensions=["tables", "fenced_code", "sane_lists"],
        )
        disclaimer_html = f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>면책 조항 · ortho-kb</title>
<link rel="stylesheet" href="assets/style.css">
</head><body>
<header class="ortho-header">
  <a href="index.html">← ortho-kb 홈</a>
  <span class="ortho-version">면책 조항 전문</span>
</header>
<main class="ortho-main">{body_html}</main>
</body></html>"""
        (DOCS / "DISCLAIMER.html").write_text(disclaimer_html, encoding="utf-8")
        print(f"[build_all] 면책 조항 페이지: {DOCS / 'DISCLAIMER.html'}")

    # ─── sitemap.xml 자동 생성 (SEO Sprint 6) ───
    import json as _json
    seo_meta_path = ROOT / "data" / "seo_meta.json"
    site_url = "https://newwonwoo.github.io/ortho-kb"
    if seo_meta_path.exists():
        try:
            site_url = _json.loads(seo_meta_path.read_text(encoding="utf-8")).get(
                "site", {}).get("url", site_url)
        except Exception:
            pass
    today = "2026-06-06"
    sitemap_urls = [
        (f"{site_url}/", "1.0", "weekly"),
        (f"{site_url}/search/", "0.9", "weekly"),
        (f"{site_url}/DISCLAIMER.html", "0.3", "yearly"),
    ]
    for p in pages:
        sitemap_urls.append((f"{site_url}/body/{p['filename']}", "0.9", "monthly"))
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url, priority, freq in sitemap_urls:
        sitemap_xml += f"  <url>\n"
        sitemap_xml += f"    <loc>{url}</loc>\n"
        sitemap_xml += f"    <lastmod>{today}</lastmod>\n"
        sitemap_xml += f"    <changefreq>{freq}</changefreq>\n"
        sitemap_xml += f"    <priority>{priority}</priority>\n"
        sitemap_xml += f"  </url>\n"
    sitemap_xml += '</urlset>\n'
    (DOCS / "sitemap.xml").write_text(sitemap_xml, encoding="utf-8")
    print(f"[build_all] sitemap.xml: {len(sitemap_urls)}개 URL")

    # ─── robots.txt 자동 생성 ───
    robots = f"""User-agent: *
Allow: /

# AI 학습 크롤러 정책 (선택적으로 제한)
# 의료 콘텐츠는 검색 발견은 허용하되 LLM 학습 데이터 사용은 제한 권고
User-agent: GPTBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Google-Extended
Allow: /

Sitemap: {site_url}/sitemap.xml
"""
    (DOCS / "robots.txt").write_text(robots, encoding="utf-8")
    print(f"[build_all] robots.txt 생성")

    # ─── 검색 인덱스 빌드 (build_search_index.py 호출) ───
    try:
        import subprocess
        r = subprocess.run(
            [sys.executable, str(Path(__file__).parent / "build_search_index.py")],
            capture_output=True, text=True, check=True,
        )
        print("[build_all] 검색 인덱스:")
        for line in r.stdout.strip().splitlines():
            print(f"  {line}")
    except Exception as e:
        print(f"[build_all] 검색 인덱스 빌드 실패 (무시): {e}")

    print(f"[build_all] 완료: {DOCS}")


if __name__ == "__main__":
    main()
