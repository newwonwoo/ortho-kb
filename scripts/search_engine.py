"""
search_engine.py — ortho-kb 검색 엔진 Python 포팅

목적:
  docs/search/index.html의 검색 로직을 Python으로 1:1 재현하여
  매 빌드마다 회귀 테스트를 자동 실행할 수 있게 한다.

이 모듈은 read-only — 실제 사용자 검색은 JS가 처리한다.
이건 오직 자동 테스트 스위트(run_search_tests.py)에서 호출된다.

JS와 동기화 주의:
  - docs/search/index.html의 score/detectBodyPart/normalizeQuery 변경 시
  - 본 파일도 같이 수정하지 않으면 테스트가 실제 동작과 어긋남
  - 차이 발생 시 GROUND TRUTH는 항상 JS (사용자가 보는 것)
"""
from __future__ import annotations
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "docs" / "search" / "index.json"
INTENTS_PATH = ROOT / "docs" / "search" / "intents.json"

# ─── 한국어 조사 (긴 것부터 매칭) ─────────────────────────────────
KOREAN_PARTICLES = sorted([
    "에서는","에서도","에서","으로","에게서","에게","에는","에도","에",
    "와는","과는","와","과","랑","이랑","처럼","같이","보다","마저",
    "께서는","께서","이가","가","이","을","를",
    "은","는","도","만","조차","마다","뿐","라도","이라도","의",
    "이다","입니다","이며","이고","이고요","이에요","예요",
    "있어요","있어","있다","없어","없다","있는","없는",
    "한다","합니다","해요","한","할","함",
    "다","요","지","네","야","어","아","냐",
    "었다","었던","였다","였던","겠다","겠습니다",
], key=len, reverse=True)


def strip_particle(word: str) -> str:
    for p in KOREAN_PARTICLES:
        if word.endswith(p) and len(word) - len(p) >= 2:
            return word[:-len(p)]
    return word


def tokenize(text: str) -> list[str]:
    """JS tokenize와 동일 — 한글 어절 + 조사 제거 어간 + 영문."""
    tokens = set()
    for m in re.finditer(r"[가-힣]+", text):
        w = m.group(0)
        if len(w) >= 2:
            tokens.add(w)
        stem = strip_particle(w)
        if len(stem) >= 2 and stem != w:
            tokens.add(stem)
    for m in re.finditer(r"[a-z]{2,}", text.lower()):
        tokens.add(m.group(0))
    return list(tokens)


# ─── 부위 키워드 (JS BODY_PARTS와 동기화) ─────────────────────────
BODY_PARTS = {
    "shoulder": ["어깨", "회전근개", "동결견", "오십견", "견관절", "GH",
                 "임핀지먼트", "RCRSP", "이두건", "Codman", "pendulum", "유착성 관절낭염",
                 "ROM 제한", "Wand exercise", "막대운동", "Theraband", "진자운동",
                 "석회화건염", "석회화", "Hawkins", "Hawkins-Kennedy", "Neer", "painful arc", "견갑골", "견갑간", "팔 들면", "팔 못 들"],
    "neck":     ["목", "경추", "경부", "C1", "C2", "C3", "C4", "C5", "C6", "C7",
                 "사경", "torticollis", "거북목", "일자목", "흉쇄유돌근", "SCM",
                 "승모근", "견갑거근", "후두하근", "trigger point", "트리거 포인트",
                 "Spurling", "Hoffman sign", "Lhermitte", "ACDF", "TDR", "myelopathy",
                 "척수병증", "CSM", "Cervical Spondylotic Myelopathy",
                 "경추 디스크", "경추 HIVD", "C5-6", "C6-7",
                 "담 결렸", "담 결림", "목이 안 돌아", "목 안 돌아", "팔 저림",
                 "강한 마사지 후", "마사지 후 통증",
                 "chin tuck", "턱 당기기", "고개 숙이면", "고개 숙일 때", "머리 숙이면 손저", "고개 숙이면 손이 저"],
    "thoracic": ["등", "흉추", "T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10", "T11", "T12",
                 "능형근", "광배근", "기립근", "어깨뼈 사이", "견갑간",
                 "후만증", "곱사등", "kyphoplasty", "vertebroplasty",
                 "강직성 척추염", "AS", "Ankylosing Spondylitis", "HLA-B27",
                 "Cat-cow", "고양이 소 자세", "폼롤러 흉추", "Wall angels", "벽 천사",
                 "Face pull", "페이스 풀", "옆구리", "옆구리 위", "갈비뼈 옆", "옆구리 통", "등이 결려", "등 결려", "가운데 등", "등 가운데"],
    "hip":      ["고관절", "엉덩이", "사타구니", "대퇴골", "대퇴", "비구", "골반",
                 "FABER", "FADIR", "Patrick", "Trendelenburg",
                 "AVN", "무혈성 괴사", "avascular necrosis", "대퇴골두",
                 "FAI", "Femoroacetabular Impingement",
                 "대퇴 점액낭염", "Trochanteric bursitis", "대전자",
                 "이상근", "piriformis", "Sports hernia", "내전근",
                 "THA", "Total Hip Arthroplasty",
                 "고관절 골절", "Hip fracture", "대퇴골 근위부 골절",
                 "clamshell", "사이드 클램쉘"],
    "headache": ["두통", "머리 아파", "머리가 아", "긴장형", "tension-type",
                 "근막성 두통", "myofascial headache", "경부성 두통", "cervicogenic",
                 "자세성 두통", "후두신경통", "occipital neuralgia",
                 "MOH", "약물 과용 두통", "medication overuse",
                 "ICHD", "편두통 감별",
                 "테니스공 self-release", "후두하근 이완"],
    "calf":     ["종아리", "하퇴부", "비복근", "gastrocnemius", "가자미근", "soleus",
                 "정강이", "경골", "tibia", "비골", "fibula", "신스플린트", "shin splint",
                 "전경골근", "DVT", "심부정맥혈전증", "deep vein thrombosis",
                 "Homan", "Wells score", "폐색전증", "정맥류",
                 "Thompson test", "정강이 안쪽", "정강이 화끈",
                 "종아리 쥐남", "야간 근경련", "쥐가 나", "다리 쥐", "쥐가 계속", "calf strain", "비복근 파열"],
    "finger":   ["손가락", "엄지", "검지", "중지", "약지", "소지", "새끼손가락",
                 "MCP", "PIP", "DIP", "방아쇠수지", "trigger finger", "Mallet",
                 "Jersey finger", "Boxer's fracture", "boxer 골절", "복서 골절",
                 "Heberden", "Bouchard", "Kanavel",
                 "Skier's thumb", "Gamekeeper", "Stener", "엄지 척측",
                 "류마티스 관절염", "RA", "rheumatoid arthritis", "swan neck",
                 "boutonniere", "ulnar deviation", "척측 편위", "아침 강직",
                 "손가락 잠김", "탁 소리 손가락", "DMARDs", "주먹 쥐기", "주먹 못 쥐", "악력 약화"],
    "sij":      ["천장관절", "sacroiliac", "SI joint", "SIJ", "천골", "장골",
                 "강직성 척추염", "Ankylosing Spondylitis", "AS", "HLA-B27",
                 "axSpA", "spondyloarthritis", "MCP/PIP",
                 "FABER", "Patrick", "Compression test", "Distraction test",
                 "Gaenslen", "Thigh thrust", "천장관절염", "sacroiliitis",
                 "임신 골반 통증", "임신 천장관절", "릴랙신",
                 "엉덩이 깊은 통증", "엉덩이 깊은 안쪽", "엉덩이 안쪽 깊", "한 발로 서기", "골반 한쪽"],
    "knee":     ["무릎", "슬관절", "반월상", "연골판", "슬개", "ACL", "PCL", "MCL", "LCL",
                 "PFPS", "러너스니", "runners knee", "점퍼스니",
                 "메니스커스", "meniscus", "OA", "관절염", "슬개대퇴", "PRP", "히알루론산",
                 "직거상", "Bucket handle", "bucket handle", "Apley", "McMurray", "Lachman",
                 "골관절염", "결정성 관절염", "통풍", "가성통풍"],
    "ankle":    ["발목", "거골", "족관절", "아킬레스", "achilles", "CAI", "PTTD", "PTOA", "외상 후 관절염", "Broström", "접합 수술", "발목 인대 수술",
                 "삠", "접질림", "염좌", "alphabet",
                 "후경골건", "거골 골연골", "OCL", "Thompson test", "Ottawa"],
    "foot":     ["발바닥", "발뒤꿈치", "뒤꿈치", "뒷꿈치", "족저", "중족", "족지", "첫 걸음", "첫걸음", "디딜 때마다", "발 옆쪽", "발 가장자리", "발끝 감각", "발끝 저", "당뇨발",
                 "발가락", "무지외반", "당뇨발", "모턴", "Morton", "plantar", "족저근막", "아침 첫걸음",
                 "Haglund", "중족골 피로골절"],
    "elbow":    ["팔꿈치", "주관절", "외측 상과", "내측 상과", "lateral epicondyle", "medial epicondyle",
                 "테니스엘보", "tennis elbow", "골프엘보", "golfer's elbow", "골퍼스엘보",
                 "Cubital tunnel", "주관절 터널", "큐비탈 터널",
                 "척골신경", "ulnar nerve", "Cozen", "Mill test",
                 "UCL", "Tommy John", "olecranon", "점액낭염", "팔꿈치 점액낭",
                 "외측 상과염", "내측 상과염", "epicondylitis",
                 "새끼손가락 저림", "약지 저림", "엄지 외 손가락 저림",
                 "팔꿈치 굽힐 때 새끼", "팔꿈치 굽힐 때마다",
                 "편심 강화", "eccentric loading", "ESWT"],
    "wrist":    ["손목", "수근", "수근관", "carpal", "CTS", "정중신경",
                 "드퀘르벵", "Quervain", "TFCC", "요수근",
                 "방아쇠수지", "방아쇠 수지", "trigger finger", "Colles", "주상골", "scaphoid",
                 "Kanavel", "엄지", "엄지 CMC", "Phalen", "Tinel", "Finkelstein",
                 "원위요골", "화농성 건초염", "엄지 손목", "엄지 손목쪽", "엄지 손목 쪽"],
    "lowback":  ["허리", "요추", "척추", "디스크", "좌골", "sciatica",
                 "마미", "협착", "HIVD", "요통", "신경원성 파행", "후관절증후군", "비특이성 요통",
                 "경막외", "epidural", "TFESI", "신경근 차단",
                 "데드버그", "버드독", "코어 강화",
                 "SLR", "압박골절", "cauda equina"],
}


def detect_body_part(query_tokens: list[str], query_raw: str) -> str | None:
    """JS detectBodyPart와 동일 — 2단계: raw substring → token 정확 일치.

    Sprint 13 픽스: 매칭된 키워드 중 가장 긴 것을 채택 (예: '엄지 CMC' > '관절염').
    짧은 일반어가 부위 감지를 좌우하면 오인식이 잦으니 length-priority로 안정화.
    """
    lower_raw = (query_raw or "").lower()
    # 1차: raw 문자열에 등장하는 모든 키워드 수집 → 가장 긴 키워드의 slug 채택
    best = None  # (length, slug)
    for slug, keywords in BODY_PARTS.items():
        for kw in keywords:
            if kw.lower() in lower_raw:
                if best is None or len(kw) > best[0]:
                    best = (len(kw), slug)
    if best:
        return best[1]
    # 2차: 토큰 정확 일치 (raw에 안 나타나는 경우만)
    best = None
    for slug, keywords in BODY_PARTS.items():
        for kw in keywords:
            kw_lower = kw.lower()
            for qt in query_tokens:
                if qt.lower() == kw_lower:
                    if best is None or len(kw) > best[0]:
                        best = (len(kw), slug)
                    break
    return best[1] if best else None


# ─── 응급 키워드 (JS EMERGENCY_KEYWORDS와 동기화) ─────────────────
EMERGENCY_KEYWORDS = [
    "대소변", "회음부", "마미", "마비", "감각소실", "감각저하",
    "발열", "화농", "악취", "당뇨발", "고름", "감염성", "감염성 관절염",
    "뚝", "외상", "변형", "체중부하", "즉시",
    "진행성", "약화", "쇠약", "괄약근",
    "야간통", "체중감소", "종양",
    "호흡곤란", "흉통", "가슴까지", "가슴 통증",
    "잠겨서", "잠겼", "잠긴", "잠김", "안 펴", "안펴", "locking",
    "kanavel", "Kanavel",
    "점차 약해", "점점 약해", "점점 없어", "힘이 빠",
    "안장", "안장 감각", "소변이 안 나", "소변 안 나", "소변 장애", "대변 장애",
    "엉덩이 감각", "엉덩이가 무감각",
    "파열 의심", "아킬레스 파열", "수동 신전",
]


def detect_emergency(query_tokens: list[str], query_raw: str) -> bool:
    lower_raw = (query_raw or "").lower()
    for kw in EMERGENCY_KEYWORDS:
        if kw.lower() in lower_raw:
            return True
        for qt in query_tokens:
            if kw.lower() in qt.lower():
                return True
    return False


# ─── 카테고리 분류 (JS categorize와 동기화) ───────────────────────
def categorize(chunk: dict) -> str:
    h = chunk.get("heading", "")
    if re.search(r"마미|Red\s*Flag|Kanavel|응급|즉시\s*의뢰", h, re.I):
        return "emergency"
    if re.search(r"^1\.|흔한\s*증상|감별진단|^진단", h, re.I):
        return "diagnosis"
    if re.search(r"^2\.|자가\s*체크", h, re.I):
        return "selfcheck"
    if re.search(r"^3\.", h, re.I):
        return "examination"
    if re.search(r"약물|상호작용|일반의약품|처방약|주사|OTC", h, re.I):
        return "medication"
    if re.search(r"물리치료|모달리티|체외충격파|TENS|도수치료", h, re.I):
        return "physiotherapy"
    if re.search(r"운동|스트레칭|단계|재활|복귀", h, re.I):
        return "exercise"
    if re.search(r"수술|봉합|재건|치환|절제술|관절경", h, re.I):
        return "surgery"
    if re.search(r"출처|참고|References", h, re.I):
        return "reference"
    return "general"


# ─── 약물 키워드 (Sprint 12 W12: 단일 약물명 검색 강화) ─────────
#   쿼리에 이 키워드가 나타나면 약물 카테고리 청크에 추가 부스트(+6)를 준다.
#   목적: "셀레콕시브" 같은 단독 검색 시 약물 섹션이 확실히 1위가 되도록.
DRUG_KEYWORDS = [
    # NSAID 비선택적
    "이부프로펜", "나프록센", "디클로페낙", "케토프로펜", "ibuprofen", "naproxen",
    "부루펜", "낙센", "탁센", "ibu", "advil",
    # NSAID COX-2 선택적
    "셀레콕시브", "쎄레브렉스", "celecoxib", "celebrex",
    # 아세트아미노펜
    "아세트아미노펜", "타이레놀", "paracetamol", "acetaminophen",
    # 약한 오피오이드
    "트라마돌", "tramadol", "울트라셋", "트리돌",
    # 항응고제
    "와파린", "warfarin",
    # 항혈소판
    "아스피린", "aspirin",
    # 항우울제 (만성 통증)
    "듀록세틴", "duloxetine", "심발타",
    # 신경병성 통증
    "가바펜틴", "gabapentin", "프레가발린", "pregabalin", "리리카",
    # 근이완제
    "에페리손", "톨페리손", "사이클로벤자프린",
    # 위장 보호제
    "PPI", "오메프라졸", "에소메프라졸", "란소프라졸",
    # 주사·시술
    "스테로이드", "코르티코", "트리암시놀론", "덱사메타손",
    "히알루론산", "PRP", "PRF",
    # 보충제
    "글루코사민", "콘드로이틴",
    # 외용제
    "케토톱", "볼타렌", "트라스트", "겔", "패치",
    # 카테고리
    "NSAID", "OTC", "진통제", "소염제", "해열제", "근이완제",
]


def is_drug_query(query_tokens: list[str], raw_query: str) -> bool:
    """쿼리에 약물 키워드가 등장하는지."""
    raw_l = (raw_query or "").lower()
    for kw in DRUG_KEYWORDS:
        if kw.lower() in raw_l:
            return True
    for qt in query_tokens:
        for kw in DRUG_KEYWORDS:
            if qt.lower() == kw.lower():
                return True
    return False


EXERCISE_HINTS = ["운동", "스트레칭", "데드버그", "버드독", "슬라이드",
                  "직거상", "set", "tilt", "curl", "glide", "squat", "bridge",
                  "pendulum", "theraband", "alphabet"]
SYMPTOM_HINTS = ["통증", "아파", "아프", "저림", "저린", "뻐근", "시큰",
                 "잠김", "잠겨", "붓고", "부어", "부종", "거슬리", "욱신",
                 "찌릿", "쑤시", "약해져", "약화", "들어올", "굽힐", "펼때",
                 "들때", "끊어", "삐어", "삐었"]


def _raw_score(chunk: dict, query_tokens: list[str]) -> float:
    """부정 페널티용 — 부스트 없는 원점수."""
    ht = set(tokenize(chunk.get("heading", "")))
    bt = set(chunk.get("tokens", []))
    text = chunk.get("text", "")
    s = 0.0
    for qt in query_tokens:
        if qt in ht:
            s += 8
        tf = len(re.findall(re.escape(qt), text, re.I))
        if tf > 0:
            s += 1 + math.log(1 + tf) * 1.5
        for h in ht:
            if qt in h and h != qt:
                s += 3
        for b in bt:
            if qt in b and b != qt:
                s += 0.3
    return s


def score(chunk: dict, query_tokens: list[str],
          detected_slug: str | None,
          negated_categories: list[str] | None = None,
          time_stage: tuple[str, str] | None = None,
          drug_query: bool = False,
          red_flag_active: bool = False) -> float:
    """JS score()와 동일 — 부위·운동·증상·시간·부정·약물·Red Flag 부스트 반영.

    red_flag_active: Red Flag 트리거가 발동된 쿼리이면 응급 청크에 +8 부스트.
    """
    if not query_tokens:
        return 0
    heading = chunk.get("heading", "")
    text = chunk.get("text", "")
    heading_tokens = set(tokenize(heading))
    body_set = set(chunk.get("tokens", []))

    # (A) 부위 일치
    if detected_slug and chunk.get("slug") != detected_slug:
        return 0
    part_boost = 10 if detected_slug and chunk.get("slug") == detected_slug else 0

    # (D) 부정 페널티
    chunk_cat = categorize(chunk)
    if negated_categories and chunk_cat != "emergency" and chunk_cat in negated_categories:
        return max(0, _raw_score(chunk, query_tokens) - 15)

    # (E) Sprint 12 약물 부스트 — 약물 쿼리이면 약물 카테고리 청크에 +6
    drug_boost = 0
    if drug_query and chunk_cat == "medication":
        drug_boost = 6

    # (F) Sprint 13 Red Flag 부스트 — 응급 트리거 발동 시 emergency 청크에 +8
    #     의료 위키 안전 핵심: 응급 안내가 최상단·고점수로 잡혀야 함
    red_flag_boost = 0
    if red_flag_active and chunk_cat == "emergency":
        red_flag_boost = 8

    # (B) 운동 + 시간 부스트
    exercise_query = any(
        qt == h or h in qt or qt in h
        for qt in query_tokens for h in EXERCISE_HINTS
    )
    stage_boost = 4 if (exercise_query and "단계" in heading) else 0
    if time_stage:
        stage_name = time_stage[0] if isinstance(time_stage, tuple) else time_stage.get("stage")
        if stage_name == "acute" and re.search(r"1단계|급성기", heading):
            stage_boost += 6
        elif stage_name == "subacute" and re.search(r"2단계|아급성|ROM", heading, re.I):
            stage_boost += 6
        elif stage_name == "chronic" and re.search(
                r"3단계|4단계|만성|근력|코어\s*강화|복귀", heading, re.I):
            stage_boost += 6
        elif stage_name == "trauma" and re.search(
                r"외상|즉시|Red\s*Flag|응급", heading, re.I):
            stage_boost += 8

    # (C) 증상 + 진단 섹션 부스트
    symptom_query = any(
        qt == h or h in qt or qt in h
        for qt in query_tokens for h in SYMPTOM_HINTS
    )
    diag_section = bool(re.match(
        r"^(1\.|1\s|2\.|2\s|흔한|감별|증상|Red\s*Flag|자가)", heading, re.I))
    symptom_boost = 6 if symptom_query and diag_section else 0

    s = part_boost + stage_boost + symptom_boost + drug_boost + red_flag_boost
    for qt in query_tokens:
        if qt in heading_tokens:
            s += 8
        tf = len(re.findall(re.escape(qt), text, re.I))
        if tf > 0:
            s += 1 + math.log(1 + tf) * 1.5
        for h in heading_tokens:
            if qt in h and h != qt:
                s += 3
        for b in body_set:
            if qt in b and b != qt:
                s += 0.3
    return s


# ─── normalizeQuery (JS와 동일) ───────────────────────────────────
def normalize_query(raw_query: str, intents: dict) -> dict:
    q = raw_query
    typos = []
    # 1) 오타 교정
    for wrong, right in (intents.get("common_typos") or {}).items():
        if wrong.startswith("_"):
            continue
        if wrong in q and wrong != right:
            q = q.replace(wrong, right)
            typos.append((wrong, right))

    expansions = set()
    # 2) 부위별 동의어
    for slug, syns in (intents.get("body_synonyms") or {}).items():
        for canonical, vars_ in syns.items():
            if canonical.startswith("_"):
                continue
            for v in vars_:
                if v in q:
                    expansions.add(canonical)
            if canonical in q:
                for v in vars_:
                    expansions.add(v)
    # 글로벌 동의어
    for canonical, vars_ in (intents.get("global_synonyms") or {}).items():
        if canonical.startswith("_"):
            continue
        for v in vars_:
            if v in q:
                expansions.add(canonical)
        if canonical in q:
            for v in vars_:
                expansions.add(v)

    # 3) 환자 표현
    patient_phrases = []
    for phrase, med_terms in (intents.get("patient_phrases") or {}).items():
        if phrase.startswith("_"):
            continue
        if phrase in q:
            patient_phrases.append({"phrase": phrase, "medTerms": med_terms})
            for t in med_terms:
                expansions.add(t)

    # 4) 외래어
    loanwords = []
    for loan, terms in (intents.get("loanword_dictionary") or {}).items():
        if loan.startswith("_"):
            continue
        if loan in q:
            loanwords.append({"loan": loan, "terms": terms})
            for t in terms:
                expansions.add(t)

    # 5) 부정 표현
    negated = []
    neg_map = (intents.get("negation_patterns") or {}).get("negate_categories") or {}
    for phrase, cat in neg_map.items():
        if phrase.startswith("_"):
            continue
        if phrase in q:
            negated.append({"phrase": phrase, "category": cat})

    # 6) 복수 부위
    compound = None
    for key, cfg in (intents.get("compound_body_patterns") or {}).items():
        if key.startswith("_"):
            continue
        matched = False
        if isinstance(cfg.get("require_all"), list):
            matched = all(kw in q for kw in cfg["require_all"])
        elif cfg.get("match_any"):
            for pat in cfg["match_any"]:
                try:
                    if re.search(pat, q):
                        matched = True
                        break
                except re.error:
                    if pat in q:
                        matched = True
                        break
        if matched:
            compound = {"key": key, "primary": cfg.get("primary"),
                        "note": cfg.get("note")}
            break

    # 7) 시간 표현 — trauma > acute > subacute > chronic
    time_stage = None
    te = intents.get("time_expressions") or {}
    for stage in ["trauma", "acute", "subacute", "chronic"]:
        cfg = te.get(stage) or {}
        for p in cfg.get("patterns") or []:
            if p in q:
                time_stage = (stage, p)
                break
        if time_stage:
            break

    return {
        "normalized": q,
        "expansions": sorted(expansions),
        "typos": typos,
        "patient_phrases": patient_phrases,
        "loanwords": loanwords,
        "negated": negated,
        "compound": compound,
        "time_stage": time_stage,
    }


# ─── W7 약물 비교 ─────────────────────────────────────────────────
def detect_drug_comparison(query: str, intents: dict) -> dict | None:
    dc = intents.get("drug_comparison") or {}
    pairs = dc.get("comparable_pairs") or dc.get("pairs") or []
    lower_q = query.lower()
    for pair in pairs:
        drugs = pair.get("drugs") or []
        aliases = pair.get("aliases") or []
        if len(drugs) < 2 or len(aliases) < 2:
            continue
        groups = [[d] + (aliases[i] if i < len(aliases) else [])
                  for i, d in enumerate(drugs)]
        hits = []
        for g in groups:
            hit = next((n for n in g if n.lower() in lower_q), None)
            hits.append(hit)
        if all(hits):
            return {"pair": pair, "hits": hits, "intent": "explicit"}
    return None


# ─── W8 운동 금기 ─────────────────────────────────────────────────
def detect_exercise_contraindication(query: str, intent_list: list[str],
                                      intents: dict) -> list | None:
    ec = intents.get("exercise_contraindications") or {}
    rules = ec.get("rules") or []
    if not rules:
        return None
    has_exercise = ("exercise" in (intent_list or [])) or bool(re.search(
        r"운동|스트레칭|체조|해도\s*돼|해도\s*되|할\s*수\s*있|괜찮|금기|"
        r"스쿼트|점프|런지|데드리프트|벤치프레스|푸쉬업|플랭크|"
        r"오버헤드|윗몸일으키기|달리기|줄넘기|등산|자전거",
        query, re.I))
    if not has_exercise:
        return None
    matched = []
    for rule in rules:
        keys = rule.get("condition_keywords") or rule.get("aliases") or []
        for kw in keys:
            if kw in query:
                matched.append({"rule": rule, "hit": kw})
                break
    return matched or None


# ─── 약물 상호작용 (intents.drug_interaction_triggers) ─────────────
def detect_drug_interaction(query: str, intents: dict) -> dict | None:
    di = intents.get("drug_interaction_triggers") or {}
    drugs = di.get("drugs") or []
    present = [d for d in drugs if d in query]
    if len(present) < 2:
        return None
    found = []
    for inter in di.get("interactions") or []:
        a, b = inter.get("a", ""), inter.get("b", "")
        a_hit = any(d == a or a in d or d in a or
                    (a == "NSAID" and d in ["이부프로펜", "나프록센", "셀레콕시브", "아스피린"])
                    for d in present)
        b_hit = any(d == b or b in d or d in b
                    for d in present)
        if a_hit and b_hit:
            found.append(inter)
    return {"drugs": present, "interactions": found}


# ─── Sprint 14 Step 3: 운동 일반 카탈로그 감지 ─────────────────────
#   데드리프트·벤치프레스·런지 등 일반 운동을 검색하면
#   해당 운동의 관련 부위·금기·폼 팁을 카드로 제공
def detect_exercise_catalog(query: str, intents: dict) -> dict | None:
    ec = intents.get("exercise_catalog") or {}
    exercises = ec.get("exercises") or []
    if not exercises:
        return None
    matched_ex = []
    lower_q = query.lower()
    for ex in exercises:
        names = [ex["name"].lower()] + [a.lower() for a in ex.get("aliases", [])]
        for n in names:
            if n in lower_q:
                matched_ex.append(ex)
                break
    matched_principles = []
    for p in ec.get("general_principles", []):
        if p["title"] in query:
            matched_principles.append(p)
    if not matched_ex and not matched_principles:
        return None
    return {
        "exercises": matched_ex,
        "principles": matched_principles,
    }


# ─── Sprint 14 운동 카탈로그 감지 ──────────────────────────────────
#   환자가 데드리프트·푸쉬업 등 운동명 검색 시 안내 카드용 정보 반환.
#   안전 핵심: avoid_conditions(금기 환자군) 항상 명시.
def detect_exercise_catalog(query: str, intents: dict) -> list | None:
    ec = intents.get("exercise_catalog") or {}
    movements = ec.get("movements") or []
    principles = ec.get("general_principles") or []
    matched_movements = []
    for m in movements:
        for alias in m.get("aliases", []):
            if alias in query:
                matched_movements.append(m)
                break
    matched_principles = []
    for p in principles:
        for kw in p.get("matches", []):
            if kw in query:
                matched_principles.append(p)
                break
    if not matched_movements and not matched_principles:
        return None
    return {
        "movements": matched_movements,
        "principles": matched_principles,
    }


# ─── Sprint 13 W4: 인구학 맥락 감지 ────────────────────────────────
#   안전 원칙:
#   - 진단 단정 절대 금지. '~의 위험인자가 보고됩니다' 정보 카드만 노출.
#   - 한 시나리오에서 여러 패턴 매칭 가능. 모두 반환.
def detect_demographic_context(query: str, intents: dict) -> list | None:
    dc = intents.get("demographic_context") or {}
    patterns = dc.get("patterns") or []
    if not patterns:
        return None
    matched = []
    for p in patterns:
        if p.get("match_all"):
            if not all(k in query for k in p["match_all"]):
                continue
        if p.get("match_any"):
            if not any(k in query for k in p["match_any"]):
                continue
        if p.get("match_any_age"):
            if not any(k in query for k in p["match_any_age"]):
                continue
        if p.get("match_any_part"):
            if not any(k in query for k in p["match_any_part"]):
                continue
        matched.append({
            "id": p.get("id"),
            "title": p.get("title"),
            "note": p.get("note"),
            "related_slug": p.get("related_slug"),
        })
    return matched or None


# ─── Sprint 14: 운동 카탈로그 감지 ────────────────────────────────
#   운동 이름 (데드리프트·벤치프레스 등) 검색 시 부위·금기·폼팁 카드 노출.
# ─── Red Flag 감지 ────────────────────────────────────────────────
def detect_red_flag(query: str, intents: dict) -> dict | None:
    """Red Flag 트리거 감지.

    지원 매칭 방식:
    - match_any: 키워드 중 하나라도 매칭 (정확 구문)
    - match_all_groups: 키워드 그룹들의 AND. 각 그룹은 OR 매칭.
      예: [["카이로", "도수", "마사지"], ["어지", "시야", "두통"]]
          → "카이로|도수|마사지" 그룹과 "어지|시야|두통" 그룹 양쪽 모두 매칭 시 트리거.
          자연어 매칭에 강함.

    Sprint 22 (라운드 3 후): 트리거에 `priority` (낮은 숫자 = 높은 우선) 지원.
      - 자살 위기·소아 등 안전 핵심을 먼저 노출하기 위함.
      - priority 미명시 시 기본값 100.
    """
    triggers = intents.get("red_flag_triggers") or {}
    matched = []
    for key, t in triggers.items():
        if key.startswith("_"):
            continue
        # 1) match_any (단일 OR)
        hits = [k for k in (t.get("match_any") or []) if k in query]
        if hits:
            matched.append({**t, "key": key, "hits": hits, "_prio": t.get("priority", 100)})
            continue
        # 2) match_all_groups (다중 그룹 AND of OR)
        groups = t.get("match_all_groups") or []
        if groups:
            all_groups_ok = True
            group_hits = []
            for group in groups:
                group_hit = next((k for k in group if k in query), None)
                if group_hit is None:
                    all_groups_ok = False
                    break
                group_hits.append(group_hit)
            if all_groups_ok and group_hits:
                matched.append({**t, "key": key, "hits": group_hits, "_prio": t.get("priority", 100)})
    if not matched:
        return None
    # 우선순위 정렬 (낮은 _prio가 먼저)
    matched.sort(key=lambda x: x.get("_prio", 100))
    chosen = matched[0]
    chosen.pop("_prio", None)
    return chosen


# ─── 의도 분류 ────────────────────────────────────────────────────
def classify_intent(query: str, intents: dict) -> list[str]:
    ic = intents.get("intent_classifier") or {}
    out = []
    for intent, kws in ic.items():
        if intent.startswith("_"):
            continue
        if any(k in query for k in kws):
            out.append(intent)
    return out


# ─── 메인 검색 함수 (JS search와 동일) ────────────────────────────
def search(query: str, top_k: int = 6,
           negated_categories: list[str] | None = None,
           time_stage: tuple[str, str] | None = None,
           index: dict | None = None,
           prefer_raw_for_body: str | None = None,
           red_flag_active: bool = False) -> list[dict]:
    """검색.

    prefer_raw_for_body: 원본 쿼리(부위 감지 raw 우선용). None이면 query 사용.
    red_flag_active: Red Flag 트리거 활성화 (응급 청크 +8 부스트).
    """
    if index is None:
        index = load_index()
    q_tokens = tokenize(query)
    if not q_tokens:
        return []
    # 부위 감지: raw 우선 → enriched 폴백
    if prefer_raw_for_body:
        raw_tokens = tokenize(prefer_raw_for_body)
        detected_slug = detect_body_part(raw_tokens, prefer_raw_for_body)
        if detected_slug is None:
            detected_slug = detect_body_part(q_tokens, query)
    else:
        detected_slug = detect_body_part(q_tokens, query)
    is_emergency = detect_emergency(q_tokens, query)
    # Sprint 12 — 약물 쿼리 감지 (raw 우선 → enriched 폴백)
    drug_query = is_drug_query(q_tokens, prefer_raw_for_body or query)

    scored = []
    for c in index["chunks"]:
        s = score(c, q_tokens, detected_slug, negated_categories, time_stage,
                  drug_query, red_flag_active)
        if s > 0:
            scored.append({"chunk": c, "s": s, "cat": categorize(c)})
    scored.sort(key=lambda x: -x["s"])

    if not scored:
        return []

    # 카테고리 다양화 + 응급 우선
    selected = []
    used_ids = set()
    cat_count = {}
    if is_emergency:
        for item in scored:
            if item["cat"] == "emergency" and item["chunk"].get("id") not in used_ids:
                selected.append(item)
                used_ids.add(item["chunk"].get("id"))
                if len(selected) >= 2:
                    break
    for item in scored:
        if item["chunk"].get("id") in used_ids:
            continue
        if len(selected) >= top_k:
            break
        cat = item["cat"]
        if cat_count.get(cat, 0) >= 2:
            continue
        selected.append(item)
        used_ids.add(item["chunk"].get("id"))
        cat_count[cat] = cat_count.get(cat, 0) + 1

    return selected[:top_k]


# ─── 통합 검색 (handleSearch 1턴 전체) ────────────────────────────
def full_search(query: str, top_k: int = 5,
                index: dict | None = None,
                intents: dict | None = None) -> dict:
    """JS handleSearch와 동일한 흐름 — 모든 신호 추출 + 검색."""
    if index is None:
        index = load_index()
    if intents is None:
        intents = load_intents()

    norm = normalize_query(query, intents)
    red_flag = detect_red_flag(norm["normalized"], intents)
    drug_hit = detect_drug_interaction(norm["normalized"], intents)
    intent_list = classify_intent(norm["normalized"], intents)
    drug_compare = detect_drug_comparison(norm["normalized"], intents)
    ex_contra = detect_exercise_contraindication(norm["normalized"],
                                                  intent_list, intents)
    ex_catalog = detect_exercise_catalog(norm["normalized"], intents)
    demographic = detect_demographic_context(norm["normalized"], intents)
    exercise_catalog = detect_exercise_catalog(norm["normalized"], intents)

    enriched = norm["normalized"] + " " + " ".join(norm["expansions"])
    q_tokens = tokenize(enriched)
    # 부위 감지: raw 우선 → 없으면 enriched 폴백
    # (raw에 부위가 명시되면 그것을 절대 우선, 환자표현으로만 추론되는 경우만 enriched 사용)
    detected_slug = detect_body_part(tokenize(norm["normalized"]), norm["normalized"])
    if detected_slug is None:
        detected_slug = detect_body_part(q_tokens, enriched)
    is_emergency = detect_emergency(q_tokens, enriched)
    negated_cats = [n["category"] for n in norm["negated"]]
    # Red Flag 트리거 또는 응급 키워드 감지 시 응급 청크 부스트
    red_flag_active = bool(red_flag) or is_emergency
    results = search(enriched, top_k, negated_cats, norm["time_stage"], index,
                     prefer_raw_for_body=norm["normalized"],
                     red_flag_active=red_flag_active)

    return {
        "query": query,
        "normalized": norm["normalized"],
        "expansions": norm["expansions"],
        "typos": norm["typos"],
        "patient_phrases": norm["patient_phrases"],
        "loanwords": norm["loanwords"],
        "negated": norm["negated"],
        "compound": norm["compound"],
        "time_stage": norm["time_stage"],
        "red_flag": red_flag,
        "drug_hit": drug_hit,
        "drug_compare": drug_compare,
        "exercise_contraindication": ex_contra,
        "exercise_catalog": ex_catalog,
        "demographic": demographic,
        "intent_list": intent_list,
        "detected_slug": detected_slug,
        "is_emergency": is_emergency,
        "results": results,
    }


# ─── 로딩 ─────────────────────────────────────────────────────────
def load_index(path: Path = INDEX_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_intents(path: Path = INTENTS_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    # 간단한 자체 검사
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "어깨 야간통"
    r = full_search(q)
    print(f"\n[Q] {q}")
    print(f"  부위감지: {r['detected_slug']}")
    print(f"  응급: {r['is_emergency']}")
    print(f"  시간: {r['time_stage']}")
    print(f"  의도: {r['intent_list']}")
    print(f"  Top 결과:")
    for item in r["results"][:3]:
        c = item["chunk"]
        print(f"    [{item['s']:5.1f}] [{item['cat']:11}] {c['title']} · {c['heading'][:50]}")
