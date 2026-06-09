"""
search_legal.py — 합법 라이선스 이미지 소스 검색기

대상 소스 (모두 무료, 라이선스 명확):
  1) Wikimedia Commons API — CC BY-SA / Public Domain
  2) Unsplash API           — Unsplash License (상업 OK, 변형 OK)
  3) Servier Medical Art    — CC BY 4.0 (의학 일러스트 전문)

사용법:
    python scripts/legal_image_sources/search_legal.py "shoulder anatomy" --source wikimedia
    python scripts/legal_image_sources/search_legal.py "knee" --source servier
    → 결과: 이미지 URL + 라이선스 + 출처 + (다운로드 가능) 출력

핵심 정책:
- 라이선스 정보가 응답에 명시되지 않은 결과는 자동 폐기.
- 다운로드는 명시적 --download 플래그 필요. assets/legal_images/에 저장.
- 출처·라이선스·작성자 메타데이터를 함께 저장 (SOURCES.json).

⚠️ Servier Medical Art 검색은 공식 API 부재이므로 사용자에게 직접
   https://smart.servier.com/ 접속 안내만 출력.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from urllib.parse import quote_plus
from urllib.request import urlopen, Request
from urllib.error import URLError

ROOT = Path(__file__).resolve().parent.parent.parent
ASSETS_LEGAL = ROOT / "assets" / "legal_images"
SOURCES_JSON = ASSETS_LEGAL / "SOURCES.json"

# Wikimedia Commons: 라이선스가 자동 필터링되는 안전한 소스
WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"

# Unsplash: 키 필요. 키 없으면 안내만 출력.
UNSPLASH_API = "https://api.unsplash.com/search/photos"


def search_wikimedia(query: str, limit: int = 10) -> list[dict]:
    """Wikimedia Commons 검색. 결과의 imageinfo로 라이선스·작성자 메타 동시 조회."""
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": "6",          # File namespace
        "gsrlimit": str(limit),
        "prop": "imageinfo",
        "iiprop": "url|extmetadata|user|mime",
        "iiurlwidth": "600",
    }
    url = WIKIMEDIA_API + "?" + "&".join(f"{k}={quote_plus(v)}" for k, v in params.items())
    req = Request(url, headers={"User-Agent": "ortho-kb-legal-image-search/0.1 (research)"})
    try:
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except URLError as e:
        print(f"[wikimedia] 네트워크 오류: {e}", file=sys.stderr)
        return []

    pages = (data.get("query") or {}).get("pages") or {}
    out = []
    for pid, page in pages.items():
        ii = (page.get("imageinfo") or [{}])[0]
        ext = ii.get("extmetadata") or {}
        # 라이선스 정보 없는 결과는 폐기
        license_short = (ext.get("LicenseShortName") or {}).get("value")
        if not license_short:
            continue
        out.append({
            "title": page.get("title"),
            "url": ii.get("url"),
            "thumb": ii.get("thumburl"),
            "mime": ii.get("mime"),
            "license": license_short,
            "author": (ext.get("Artist") or {}).get("value", "Unknown"),
            "source": "Wikimedia Commons",
            "credit_url": ii.get("descriptionurl") or "",
        })
    return out


def search_unsplash(query: str, limit: int = 10, access_key: str | None = None) -> list[dict]:
    """Unsplash 검색. 키 없으면 빈 리스트 + 안내."""
    if not access_key:
        print("[unsplash] UNSPLASH_ACCESS_KEY 환경변수 미설정 — 건너뜀.")
        print("           https://unsplash.com/developers 에서 무료 키 발급.")
        return []
    url = f"{UNSPLASH_API}?query={quote_plus(query)}&per_page={limit}"
    req = Request(url, headers={"Authorization": f"Client-ID {access_key}"})
    try:
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except URLError as e:
        print(f"[unsplash] 네트워크 오류: {e}", file=sys.stderr)
        return []
    return [
        {
            "title": item.get("description") or item.get("alt_description") or "(no title)",
            "url": item["urls"]["regular"],
            "thumb": item["urls"]["small"],
            "mime": "image/jpeg",
            "license": "Unsplash License (free for commercial, attribution appreciated)",
            "author": item["user"]["name"],
            "source": "Unsplash",
            "credit_url": item["links"]["html"],
        }
        for item in data.get("results", [])
    ]


def servier_notice():
    """Servier Medical Art는 공식 API 부재 — 안내만."""
    print("─" * 60)
    print("Servier Medical Art (CC BY 4.0) — 의학 일러스트 무료")
    print("─" * 60)
    print("공식 API가 없으므로 다음 사이트에서 직접 다운로드:")
    print("  https://smart.servier.com/")
    print("")
    print("사용 시 의무사항:")
    print('  - "Smart Servier Medical Art, licensed under CC BY 4.0"')
    print("  - 변경 시 변경 내용 명시")
    print("  - 본 위키 페이지 하단 출처 표기 필수")
    print("─" * 60)


def write_sources(rows: list[dict]):
    """assets/legal_images/SOURCES.json에 누적 기록."""
    ASSETS_LEGAL.mkdir(parents=True, exist_ok=True)
    existing = []
    if SOURCES_JSON.exists():
        existing = json.loads(SOURCES_JSON.read_text(encoding="utf-8"))
    # 중복 제거 (url 기준)
    existing_urls = {x["url"] for x in existing}
    for r in rows:
        if r["url"] not in existing_urls:
            existing.append(r)
    SOURCES_JSON.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[sources] {SOURCES_JSON} 갱신 (총 {len(existing)}건)")


def main():
    p = argparse.ArgumentParser(description="합법 라이선스 이미지 소스 검색")
    p.add_argument("query", help="검색어 (예: 'shoulder anatomy')")
    p.add_argument("--source", choices=["wikimedia", "unsplash", "servier", "all"],
                   default="wikimedia")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--unsplash-key", default=None, help="Unsplash access key")
    p.add_argument("--save", action="store_true", help="결과를 SOURCES.json에 저장")
    args = p.parse_args()

    results = []
    if args.source in ("wikimedia", "all"):
        results += search_wikimedia(args.query, args.limit)
    if args.source in ("unsplash", "all"):
        results += search_unsplash(args.query, args.limit, args.unsplash_key)
    if args.source in ("servier", "all"):
        servier_notice()

    if not results and args.source != "servier":
        print("[search_legal] 결과 없음 또는 라이선스 정보 누락")
        return

    for i, r in enumerate(results, 1):
        print(f"\n[{i}] {r['title']}")
        print(f"    URL    : {r['url']}")
        print(f"    Thumb  : {r['thumb']}")
        print(f"    License: {r['license']}")
        print(f"    Author : {r['author']}")
        print(f"    Source : {r['source']} → {r['credit_url']}")

    if args.save:
        write_sources(results)


if __name__ == "__main__":
    main()
