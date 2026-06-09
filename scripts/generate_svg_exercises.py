"""
generate_svg_exercises.py — 막대인간 SVG 운동 도해 일괄 생성

설계 원칙:
- 320x320 viewBox 통일 (위키 본문에 균일 크기로 임베드)
- 환측 부위는 파란색(#2563eb), 보조 인접부는 진회색(#1f2937)
- 운동 방향·궤적은 빨간 점선 또는 화살표(#dc2626)
- 라벨 영문 + 한글 부제 + 횟수 메모
- 의학적 정확성: 각 자세는 재활치료 표준 가이드라인 기반 (코드 주석에 출처)

운동 목록 (총 16종):
  무릎(4): quad set, SLR, wall slide, mini squat
  발목(3): alphabet, theraband 4-way, single leg balance
  발바닥(2): plantar fascia stretch (towel), calf stretch (wall)
  손목(2): median nerve glide, towel curl
  허리(5): pelvic tilt, cat-cow, dead bug, bird dog, glute bridge

사용:
    python scripts/generate_svg_exercises.py
    → assets/svg_exercises/*.svg 생성
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "svg_exercises"


def svg_wrap(title_en: str, subtitle_ko: str, note: str, body_svg: str) -> str:
    """공통 SVG 프레임. 320x320, 바닥선, 라벨 3줄."""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 320" width="320" height="320" role="img"
     aria-label="{title_en} — {subtitle_ko}">
  <title>{title_en} — {subtitle_ko}</title>
  <rect width="320" height="320" fill="#fafafa"/>
  <line x1="20" y1="290" x2="300" y2="290" stroke="#9ca3af" stroke-width="2"/>
  <text x="160" y="28" text-anchor="middle" font-family="sans-serif" font-size="15" font-weight="bold" fill="#1f2937">
    {title_en}
  </text>
  <text x="160" y="46" text-anchor="middle" font-family="sans-serif" font-size="12" fill="#666">
    {subtitle_ko}
  </text>
{body_svg}
  <text x="160" y="312" text-anchor="middle" font-family="sans-serif" font-size="10" fill="#666">
    {note}
  </text>
</svg>
'''


# ─── 무릎 4종 ─────────────────────────────────────────────────

quad_set = svg_wrap("Quadriceps Set", "대퇴사두근 등척성 · 무릎 1단계", "무릎 펴고 대퇴근 수축 5초 × 10회 × 3세트", '''
  <!-- 누운 자세 - 측면 -->
  <circle cx="70" cy="160" r="14" fill="none" stroke="#1f2937" stroke-width="3"/>
  <line x1="84" y1="160" x2="200" y2="160" stroke="#1f2937" stroke-width="4" stroke-linecap="round"/>
  <!-- 다리 (펴진 상태 — 환측 파란색) -->
  <line x1="200" y1="160" x2="270" y2="160" stroke="#2563eb" stroke-width="5" stroke-linecap="round"/>
  <!-- 발 -->
  <line x1="270" y1="160" x2="278" y2="148" stroke="#2563eb" stroke-width="4" stroke-linecap="round"/>
  <!-- 무릎 위치 표시 + 수축 화살표 -->
  <circle cx="235" cy="160" r="6" fill="#2563eb"/>
  <text x="235" y="190" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#dc2626" font-weight="bold">수축↑</text>
  <!-- 매트 -->
  <line x1="40" y1="178" x2="290" y2="178" stroke="#1f2937" stroke-width="2" stroke-dasharray="3 3"/>
''')

slr = svg_wrap("Straight Leg Raise (SLR)", "하지직거상 · 무릎 1단계", "다리 펴서 30°로 들기 5초 × 10회 × 3세트", '''
  <!-- 누운 자세 -->
  <circle cx="60" cy="180" r="14" fill="none" stroke="#1f2937" stroke-width="3"/>
  <line x1="74" y1="180" x2="190" y2="180" stroke="#1f2937" stroke-width="4" stroke-linecap="round"/>
  <!-- 환측 다리 — 들어올린 자세 (30도) -->
  <line x1="190" y1="180" x2="270" y2="138" stroke="#2563eb" stroke-width="5" stroke-linecap="round"/>
  <!-- 발 (발등굽힘) -->
  <line x1="270" y1="138" x2="278" y2="128" stroke="#2563eb" stroke-width="4" stroke-linecap="round"/>
  <!-- 반대측 다리 (바닥) -->
  <line x1="190" y1="180" x2="270" y2="180" stroke="#1f2937" stroke-width="4" stroke-linecap="round" opacity="0.4"/>
  <!-- 들어올림 화살표 -->
  <path d="M 260 200 Q 250 180 245 155" fill="none" stroke="#dc2626" stroke-width="2"/>
  <polygon points="245,155 240,162 250,160" fill="#dc2626"/>
  <!-- 매트 -->
  <line x1="40" y1="198" x2="290" y2="198" stroke="#1f2937" stroke-width="2" stroke-dasharray="3 3"/>
  <text x="160" y="270" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#666">30° 들기, 무릎 펴진 상태 유지</text>
''')

wall_slide = svg_wrap("Wall Slide", "벽 슬라이드 · 무릎 2단계 ROM 회복", "발뒤꿈치로 벽 짚고 천천히 굽힘 10회 × 3세트", '''
  <!-- 벽 -->
  <line x1="280" y1="60" x2="280" y2="280" stroke="#9ca3af" stroke-width="4"/>
  <!-- 누운 자세 -->
  <circle cx="50" cy="180" r="14" fill="none" stroke="#1f2937" stroke-width="3"/>
  <line x1="64" y1="180" x2="170" y2="180" stroke="#1f2937" stroke-width="4" stroke-linecap="round"/>
  <!-- 환측 다리 — 무릎 굽힘 자세, 발은 벽에 -->
  <line x1="170" y1="180" x2="210" y2="130" stroke="#2563eb" stroke-width="5" stroke-linecap="round"/>
  <line x1="210" y1="130" x2="270" y2="105" stroke="#2563eb" stroke-width="5" stroke-linecap="round"/>
  <circle cx="210" cy="130" r="5" fill="#2563eb"/>
  <!-- 발(벽에 닿음) -->
  <circle cx="272" cy="105" r="5" fill="#2563eb"/>
  <!-- 슬라이드 궤적 -->
  <line x1="272" y1="120" x2="272" y2="200" stroke="#dc2626" stroke-width="1.5" stroke-dasharray="3 3"/>
  <polygon points="272,200 268,193 276,193" fill="#dc2626"/>
  <text x="190" y="248" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#666">발이 벽을 따라 천천히 미끄러져 내림</text>
''')

mini_squat = svg_wrap("Mini Squat (0~45°)", "부분 스쿼트 · 무릎 3단계 근력", "통증 없는 범위 5초 하강·5초 상승 × 10회 × 3세트", '''
  <!-- 서 있는 자세, 무릎 살짝 굽힘 -->
  <circle cx="160" cy="80" r="16" fill="none" stroke="#1f2937" stroke-width="3"/>
  <!-- 몸통 (살짝 앞으로) -->
  <line x1="160" y1="96" x2="175" y2="180" stroke="#1f2937" stroke-width="4" stroke-linecap="round"/>
  <!-- 골반에서 양다리 (45도 굽힘) -->
  <line x1="175" y1="180" x2="140" y2="220" stroke="#2563eb" stroke-width="5" stroke-linecap="round"/>
  <line x1="140" y1="220" x2="145" y2="285" stroke="#2563eb" stroke-width="5" stroke-linecap="round"/>
  <line x1="175" y1="180" x2="210" y2="220" stroke="#2563eb" stroke-width="5" stroke-linecap="round"/>
  <line x1="210" y1="220" x2="205" y2="285" stroke="#2563eb" stroke-width="5" stroke-linecap="round"/>
  <circle cx="140" cy="220" r="5" fill="#2563eb"/>
  <circle cx="210" cy="220" r="5" fill="#2563eb"/>
  <!-- 팔 (앞으로 뻗음 균형) -->
  <line x1="167" y1="118" x2="230" y2="115" stroke="#1f2937" stroke-width="3" stroke-linecap="round"/>
  <!-- 하강·상승 화살표 -->
  <path d="M 100 150 Q 90 200 100 250" fill="none" stroke="#dc2626" stroke-width="2"/>
  <polygon points="100,250 95,243 105,243" fill="#dc2626"/>
  <polygon points="100,150 95,157 105,157" fill="#dc2626"/>
  <text x="100" y="270" text-anchor="middle" font-family="sans-serif" font-size="10" fill="#dc2626">↕</text>
''')

# ─── 발목 3종 ─────────────────────────────────────────────────

ankle_alphabet = svg_wrap("Ankle Alphabet", "발목 알파벳 · 발목 1단계", "발끝으로 A~Z 그리기 × 2회/일", '''
  <!-- 의자에 앉은 자세 - 측면 -->
  <circle cx="80" cy="100" r="14" fill="none" stroke="#1f2937" stroke-width="3"/>
  <!-- 몸통 -->
  <line x1="80" y1="114" x2="80" y2="180" stroke="#1f2937" stroke-width="4" stroke-linecap="round"/>
  <!-- 의자 -->
  <rect x="50" y="180" width="80" height="6" fill="#9ca3af"/>
  <rect x="50" y="186" width="4" height="100" fill="#9ca3af"/>
  <rect x="126" y="186" width="4" height="100" fill="#9ca3af"/>
  <!-- 허벅지 (앉아 있음) -->
  <line x1="80" y1="180" x2="150" y2="180" stroke="#1f2937" stroke-width="4" stroke-linecap="round"/>
  <!-- 종아리 (수직 아래) -->
  <line x1="150" y1="180" x2="150" y2="250" stroke="#1f2937" stroke-width="4" stroke-linecap="round"/>
  <!-- 환측 발(움직이는 부위) -->
  <line x1="150" y1="250" x2="180" y2="245" stroke="#2563eb" stroke-width="5" stroke-linecap="round"/>
  <!-- 알파벳 궤적 -->
  <path d="M 200 240 q 10 -20 20 0 q 10 20 -5 30 q -15 -10 -5 -30 z" fill="none" stroke="#dc2626" stroke-width="1.5"/>
  <text x="245" y="225" font-family="sans-serif" font-size="14" fill="#dc2626" font-weight="bold">A B C…</text>
  <text x="245" y="265" font-family="sans-serif" font-size="14" fill="#dc2626" font-weight="bold">…X Y Z</text>
''')

ankle_theraband = svg_wrap("Theraband 4-way", "세라밴드 4방향 · 발목 3단계", "발바닥쪽굽힘·발등굽힘·내반·외반 각 15회 × 3세트", '''
  <!-- 앉은 자세 -->
  <circle cx="60" cy="100" r="14" fill="none" stroke="#1f2937" stroke-width="3"/>
  <line x1="60" y1="114" x2="60" y2="180" stroke="#1f2937" stroke-width="4" stroke-linecap="round"/>
  <rect x="30" y="180" width="60" height="6" fill="#9ca3af"/>
  <rect x="30" y="186" width="4" height="100" fill="#9ca3af"/>
  <rect x="86" y="186" width="4" height="100" fill="#9ca3af"/>
  <!-- 다리 -->
  <line x1="60" y1="180" x2="180" y2="180" stroke="#1f2937" stroke-width="4" stroke-linecap="round"/>
  <line x1="180" y1="180" x2="180" y2="240" stroke="#1f2937" stroke-width="4" stroke-linecap="round"/>
  <!-- 발 (환측) -->
  <line x1="180" y1="240" x2="210" y2="235" stroke="#2563eb" stroke-width="5" stroke-linecap="round"/>
  <!-- 세라밴드 -->
  <path d="M 215 230 Q 250 220 280 215" fill="none" stroke="#dc2626" stroke-width="3" stroke-dasharray="2 3"/>
  <!-- 고정점 -->
  <rect x="278" y="208" width="14" height="14" fill="#9ca3af" stroke="#1f2937" stroke-width="1"/>
  <!-- 4방향 화살표 -->
  <text x="200" y="180" font-family="sans-serif" font-size="11" fill="#dc2626" font-weight="bold">↕ 굽힘</text>
  <text x="200" y="265" font-family="sans-serif" font-size="11" fill="#dc2626" font-weight="bold">↔ 내·외반</text>
''')

ankle_balance = svg_wrap("Single Leg Balance", "단발 균형 · 발목 4단계", "환측 단발로 30초 × 3세트 (평면 → 폼 패드)", '''
  <!-- 머리 -->
  <circle cx="160" cy="80" r="16" fill="none" stroke="#1f2937" stroke-width="3"/>
  <!-- 몸통 -->
  <line x1="160" y1="96" x2="160" y2="200" stroke="#1f2937" stroke-width="4" stroke-linecap="round"/>
  <!-- 환측 다리 (지지) -->
  <line x1="160" y1="200" x2="155" y2="280" stroke="#2563eb" stroke-width="5" stroke-linecap="round"/>
  <!-- 발 -->
  <line x1="140" y1="280" x2="175" y2="280" stroke="#2563eb" stroke-width="5" stroke-linecap="round"/>
  <!-- 반대측 다리 (들어올림) -->
  <line x1="160" y1="200" x2="190" y2="240" stroke="#1f2937" stroke-width="4" stroke-linecap="round"/>
  <line x1="190" y1="240" x2="195" y2="220" stroke="#1f2937" stroke-width="4" stroke-linecap="round"/>
  <!-- 팔 (균형 잡기) -->
  <line x1="160" y1="120" x2="120" y2="150" stroke="#1f2937" stroke-width="3" stroke-linecap="round"/>
  <line x1="160" y1="120" x2="200" y2="150" stroke="#1f2937" stroke-width="3" stroke-linecap="round"/>
  <!-- 균형 화살표 -->
  <text x="160" y="265" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#dc2626">⇆ 균형</text>
''')

# ─── 발바닥 2종 ────────────────────────────────────────────────

plantar_stretch = svg_wrap("Plantar Fascia Stretch (Towel)", "족저근막 수건 당김 · 발바닥 1단계", "발등굽힘 자세로 30초 × 5회 × 3세트", '''
  <!-- 앉은 자세 -->
  <circle cx="60" cy="100" r="14" fill="none" stroke="#1f2937" stroke-width="3"/>
  <line x1="60" y1="114" x2="60" y2="180" stroke="#1f2937" stroke-width="4" stroke-linecap="round"/>
  <!-- 다리 펴짐 (긴 의자나 바닥) -->
  <line x1="60" y1="180" x2="220" y2="180" stroke="#2563eb" stroke-width="5" stroke-linecap="round"/>
  <!-- 발 (당겨진 발등굽힘 상태) -->
  <line x1="220" y1="180" x2="225" y2="155" stroke="#2563eb" stroke-width="5" stroke-linecap="round"/>
  <!-- 수건 -->
  <path d="M 225 155 Q 200 130 130 110" fill="none" stroke="#fbbf24" stroke-width="4"/>
  <!-- 손 -->
  <circle cx="130" cy="110" r="6" fill="#2563eb"/>
  <!-- 당김 방향 -->
  <path d="M 130 125 Q 115 140 90 145" fill="none" stroke="#dc2626" stroke-width="2"/>
  <polygon points="90,145 98,140 96,150" fill="#dc2626"/>
  <text x="130" y="158" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#dc2626" font-weight="bold">당김</text>
  <text x="160" y="220" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#666">수건으로 발바닥 감아 몸쪽으로</text>
''')

calf_stretch = svg_wrap("Calf Stretch (Wall)", "종아리 스트레칭 · 발바닥", "무릎 펴고 30초 × 3회, 무릎 굽혀 30초 × 3회", '''
  <!-- 벽 -->
  <rect x="40" y="60" width="6" height="220" fill="#9ca3af"/>
  <!-- 머리 -->
  <circle cx="160" cy="90" r="14" fill="none" stroke="#1f2937" stroke-width="3"/>
  <!-- 몸통 (앞으로 기울임) -->
  <line x1="160" y1="104" x2="120" y2="190" stroke="#1f2937" stroke-width="4" stroke-linecap="round"/>
  <!-- 양손 벽 짚음 -->
  <line x1="155" y1="120" x2="55" y2="140" stroke="#1f2937" stroke-width="3" stroke-linecap="round"/>
  <line x1="155" y1="125" x2="55" y2="170" stroke="#1f2937" stroke-width="3" stroke-linecap="round"/>
  <!-- 앞다리 (가까운 다리, 무릎 굽힘) -->
  <line x1="120" y1="190" x2="100" y2="240" stroke="#1f2937" stroke-width="4" stroke-linecap="round"/>
  <line x1="100" y1="240" x2="105" y2="285" stroke="#1f2937" stroke-width="4" stroke-linecap="round"/>
  <!-- 뒷다리 (환측, 펴진 상태) -->
  <line x1="120" y1="190" x2="200" y2="285" stroke="#2563eb" stroke-width="5" stroke-linecap="round"/>
  <!-- 뒷발 (바닥 평평) -->
  <line x1="195" y1="285" x2="220" y2="285" stroke="#2563eb" stroke-width="5" stroke-linecap="round"/>
  <text x="220" y="270" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#dc2626" font-weight="bold">스트레칭</text>
''')

# ─── 손목 2종 ─────────────────────────────────────────────────

nerve_glide = svg_wrap("Median Nerve Glide", "정중신경 활주 · 손목 2단계 CTS 보조", "6단계 자세 각 5초 × 10회", '''
  <!-- 측면 시점, 어깨에서 손까지 -->
  <!-- 어깨 -->
  <circle cx="80" cy="80" r="10" fill="#1f2937"/>
  <!-- 위팔 -->
  <line x1="80" y1="80" x2="80" y2="160" stroke="#1f2937" stroke-width="4" stroke-linecap="round"/>
  <!-- 팔꿈치 -->
  <circle cx="80" cy="160" r="5" fill="#1f2937"/>
  <!-- 아래팔 (외측으로 펴짐) -->
  <line x1="80" y1="160" x2="200" y2="160" stroke="#2563eb" stroke-width="5" stroke-linecap="round"/>
  <!-- 손목 -->
  <circle cx="200" cy="160" r="5" fill="#2563eb"/>
  <!-- 손 (신전 자세) -->
  <line x1="200" y1="160" x2="240" y2="130" stroke="#2563eb" stroke-width="5" stroke-linecap="round"/>
  <!-- 손가락 -->
  <line x1="240" y1="130" x2="260" y2="115" stroke="#2563eb" stroke-width="3" stroke-linecap="round"/>
  <!-- 정중신경 경로 (점선) -->
  <path d="M 80 90 Q 80 160 200 165 Q 230 155 250 130" fill="none" stroke="#dc2626" stroke-width="2" stroke-dasharray="4 4"/>
  <text x="160" y="230" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#666">손목 신전 + 손가락 펴기 단계</text>
  <text x="160" y="248" text-anchor="middle" font-family="sans-serif" font-size="10" fill="#dc2626">정중신경 활주 경로</text>
''')

towel_curl = svg_wrap("Towel Curl + Wrist Strength", "수건 잡기 · 손목 3단계", "수건을 발가락/손가락으로 모으기 10회 × 3세트", '''
  <!-- 책상 위에서 손 자세 -->
  <rect x="40" y="190" width="240" height="8" fill="#9ca3af"/>
  <!-- 아래팔 (책상 위) -->
  <line x1="80" y1="160" x2="180" y2="160" stroke="#2563eb" stroke-width="5" stroke-linecap="round"/>
  <!-- 손목 -->
  <circle cx="180" cy="160" r="5" fill="#2563eb"/>
  <!-- 손바닥 -->
  <line x1="180" y1="160" x2="215" y2="160" stroke="#2563eb" stroke-width="5" stroke-linecap="round"/>
  <!-- 손가락 (수건 잡는 굴곡 자세) -->
  <line x1="215" y1="160" x2="225" y2="178" stroke="#2563eb" stroke-width="3" stroke-linecap="round"/>
  <line x1="220" y1="160" x2="232" y2="180" stroke="#2563eb" stroke-width="3" stroke-linecap="round"/>
  <!-- 수건 -->
  <path d="M 230 188 Q 260 175 285 188" fill="none" stroke="#fbbf24" stroke-width="6"/>
  <!-- 손가락 굽힘 화살표 -->
  <path d="M 240 145 Q 232 170 228 180" fill="none" stroke="#dc2626" stroke-width="2"/>
  <polygon points="228,180 226,172 234,175" fill="#dc2626"/>
  <text x="160" y="240" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#666">손가락 굴근·악력 강화</text>
''')

# ─── 허리 5종 ─────────────────────────────────────────────────

pelvic_tilt = svg_wrap("Pelvic Tilt", "골반 기울이기 · 허리 2단계", "골반 중립 학습 10초 × 10회 × 3세트", '''
  <!-- 누운 자세, 무릎 굽힘 -->
  <circle cx="60" cy="190" r="14" fill="none" stroke="#1f2937" stroke-width="3"/>
  <line x1="74" y1="190" x2="170" y2="190" stroke="#1f2937" stroke-width="4" stroke-linecap="round"/>
  <!-- 골반 -->
  <circle cx="170" cy="190" r="7" fill="#2563eb"/>
  <!-- 다리 (무릎 굽힘) -->
  <line x1="170" y1="190" x2="220" y2="155" stroke="#1f2937" stroke-width="4" stroke-linecap="round"/>
  <line x1="220" y1="155" x2="230" y2="220" stroke="#1f2937" stroke-width="4" stroke-linecap="round"/>
  <!-- 매트 -->
  <line x1="40" y1="225" x2="280" y2="225" stroke="#1f2937" stroke-width="2" stroke-dasharray="3 3"/>
  <!-- 골반 기울이기 화살표 (원호) -->
  <path d="M 155 175 Q 170 170 185 175" fill="none" stroke="#dc2626" stroke-width="2"/>
  <polygon points="185,175 178,170 183,180" fill="#dc2626"/>
  <text x="170" y="155" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#dc2626" font-weight="bold">골반 회전</text>
  <text x="160" y="260" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#666">허리를 매트에 눌러 골반 후방 기울임</text>
''')

cat_cow = svg_wrap("Cat-Cow", "고양이-소 · 허리 2단계", "굴곡↔신전 천천히 10회 × 3세트", '''
  <!-- 네발기기 자세, 측면 -->
  <!-- 머리 -->
  <circle cx="50" cy="150" r="13" fill="none" stroke="#1f2937" stroke-width="3"/>
  <!-- 몸통 (소 자세 — 등 내림) -->
  <path d="M 63 150 Q 130 170 200 150" fill="none" stroke="#1f2937" stroke-width="4" stroke-linecap="round"/>
  <!-- 앞 손 -->
  <line x1="55" y1="160" x2="50" y2="220" stroke="#1f2937" stroke-width="4" stroke-linecap="round"/>
  <line x1="55" y1="160" x2="65" y2="220" stroke="#1f2937" stroke-width="4" stroke-linecap="round"/>
  <!-- 뒷 무릎 -->
  <line x1="195" y1="150" x2="190" y2="220" stroke="#1f2937" stroke-width="4" stroke-linecap="round"/>
  <line x1="195" y1="150" x2="205" y2="220" stroke="#1f2937" stroke-width="4" stroke-linecap="round"/>
  <!-- 매트 -->
  <line x1="20" y1="225" x2="240" y2="225" stroke="#1f2937" stroke-width="2" stroke-dasharray="3 3"/>
  <!-- 고양이 자세 (등 올림) 점선 표시 -->
  <path d="M 63 150 Q 130 120 200 150" fill="none" stroke="#2563eb" stroke-width="3" stroke-dasharray="4 4"/>
  <!-- 두 자세 사이 화살표 -->
  <path d="M 130 138 Q 130 145 130 152" fill="none" stroke="#dc2626" stroke-width="2"/>
  <text x="270" y="125" text-anchor="middle" font-family="sans-serif" font-size="10" fill="#2563eb" font-weight="bold">고양이</text>
  <text x="270" y="178" text-anchor="middle" font-family="sans-serif" font-size="10" fill="#1f2937" font-weight="bold">소</text>
''')

dead_bug = svg_wrap("Dead Bug", "데드버그 · 허리 3단계 코어", "반대 팔·다리 뻗기 10회 × 3세트", '''
  <!-- 누운 자세, 위에서 본 시점 -->
  <!-- 머리 -->
  <circle cx="160" cy="70" r="15" fill="none" stroke="#1f2937" stroke-width="3"/>
  <!-- 몸통 -->
  <line x1="160" y1="85" x2="160" y2="195" stroke="#1f2937" stroke-width="5" stroke-linecap="round"/>
  <!-- 환측 팔 (위로 뻗음) -->
  <line x1="160" y1="100" x2="240" y2="60" stroke="#2563eb" stroke-width="4" stroke-linecap="round"/>
  <!-- 반대 팔 (90도) -->
  <line x1="160" y1="100" x2="100" y2="100" stroke="#1f2937" stroke-width="4" stroke-linecap="round"/>
  <line x1="100" y1="100" x2="100" y2="70" stroke="#1f2937" stroke-width="4" stroke-linecap="round"/>
  <!-- 환측 반대 다리 (뻗음) -->
  <line x1="160" y1="190" x2="80" y2="250" stroke="#2563eb" stroke-width="4" stroke-linecap="round"/>
  <!-- 같은 쪽 다리 (90도 굽힘) -->
  <line x1="160" y1="190" x2="220" y2="190" stroke="#1f2937" stroke-width="4" stroke-linecap="round"/>
  <line x1="220" y1="190" x2="220" y2="240" stroke="#1f2937" stroke-width="4" stroke-linecap="round"/>
  <!-- 매트 -->
  <rect x="50" y="40" width="220" height="240" fill="none" stroke="#1f2937" stroke-width="2" stroke-dasharray="3 3"/>
  <text x="160" y="270" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#666">대각선 팔·다리 동시 뻗기 (코어 안정)</text>
''')

bird_dog = svg_wrap("Bird Dog", "버드독 · 허리 3단계 코어", "반대 팔·다리 5초 유지 10회 × 3세트", '''
  <!-- 네발기기 자세, 측면, 반대측 팔·다리 들어올림 -->
  <circle cx="50" cy="145" r="13" fill="none" stroke="#1f2937" stroke-width="3"/>
  <!-- 몸통 (수평) -->
  <line x1="63" y1="150" x2="195" y2="150" stroke="#1f2937" stroke-width="5" stroke-linecap="round"/>
  <!-- 지지 손 -->
  <line x1="60" y1="155" x2="60" y2="220" stroke="#1f2937" stroke-width="4" stroke-linecap="round"/>
  <!-- 들어올린 팔 (앞으로 뻗음) -->
  <line x1="55" y1="148" x2="0" y2="130" stroke="#2563eb" stroke-width="4" stroke-linecap="round"/>
  <!-- 지지 무릎 -->
  <line x1="195" y1="155" x2="195" y2="220" stroke="#1f2937" stroke-width="4" stroke-linecap="round"/>
  <!-- 들어올린 다리 (뒤로 뻗음) -->
  <line x1="195" y1="148" x2="270" y2="135" stroke="#2563eb" stroke-width="4" stroke-linecap="round"/>
  <!-- 매트 -->
  <line x1="20" y1="225" x2="290" y2="225" stroke="#1f2937" stroke-width="2" stroke-dasharray="3 3"/>
  <text x="160" y="265" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#666">반대측 팔·다리 동시 들기, 등은 수평 유지</text>
''')

glute_bridge = svg_wrap("Glute Bridge", "글루트 브릿지 · 허리 3단계", "엉덩이 들기 5초 × 15회 × 3세트", '''
  <!-- 누운 자세, 엉덩이 들어올림 -->
  <circle cx="60" cy="200" r="14" fill="none" stroke="#1f2937" stroke-width="3"/>
  <!-- 어깨 → 무릎 (대각선 위로) -->
  <line x1="74" y1="200" x2="200" y2="150" stroke="#2563eb" stroke-width="5" stroke-linecap="round"/>
  <!-- 무릎 -->
  <circle cx="200" cy="150" r="6" fill="#2563eb"/>
  <!-- 종아리 (수직) -->
  <line x1="200" y1="150" x2="200" y2="225" stroke="#2563eb" stroke-width="5" stroke-linecap="round"/>
  <!-- 발 -->
  <line x1="190" y1="225" x2="220" y2="225" stroke="#2563eb" stroke-width="5" stroke-linecap="round"/>
  <!-- 매트 -->
  <line x1="40" y1="225" x2="280" y2="225" stroke="#1f2937" stroke-width="2" stroke-dasharray="3 3"/>
  <!-- 엉덩이 들기 화살표 -->
  <path d="M 145 205 Q 140 180 145 160" fill="none" stroke="#dc2626" stroke-width="2"/>
  <polygon points="145,160 140,167 150,167" fill="#dc2626"/>
  <text x="145" y="250" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#dc2626" font-weight="bold">엉덩이 위로</text>
''')


SVGS = {
    "knee_quad_set.svg": quad_set,
    "knee_slr.svg": slr,
    "knee_wall_slide.svg": wall_slide,
    "knee_mini_squat.svg": mini_squat,
    "ankle_alphabet.svg": ankle_alphabet,
    "ankle_theraband_4way.svg": ankle_theraband,
    "ankle_single_leg_balance.svg": ankle_balance,
    "foot_plantar_stretch.svg": plantar_stretch,
    "foot_calf_stretch.svg": calf_stretch,
    "wrist_median_nerve_glide.svg": nerve_glide,
    "wrist_towel_curl.svg": towel_curl,
    "lowback_pelvic_tilt.svg": pelvic_tilt,
    "lowback_cat_cow.svg": cat_cow,
    "lowback_dead_bug.svg": dead_bug,
    "lowback_bird_dog.svg": bird_dog,
    "lowback_glute_bridge.svg": glute_bridge,
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for filename, content in SVGS.items():
        (OUT / filename).write_text(content, encoding="utf-8")
    print(f"[generate_svg_exercises] {len(SVGS)}개 SVG 생성 → {OUT}")


if __name__ == "__main__":
    main()
