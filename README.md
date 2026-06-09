# ortho-kb · 정형외과 증상 위키

> ⚠️ **본 위키는 교육 목적의 정보 모음입니다. 진단·처방을 대체하지 않습니다.**
> 증상이 지속되거나 악화되면 반드시 정형외과 전문의 진료를 받으세요.
> 전체 면책 조항은 [DISCLAIMER.md](./DISCLAIMER.md) 참조.

## 무엇인가요

부위별 통증의 **진단 → 치료(약물·물리치료·스트레칭·재활운동)**를
하나의 위키로 묶은 한국어 지식베이스입니다.

참고한 운영 모델: [baojie/shiji-kb](https://github.com/baojie/shiji-kb)
(마크다운 원본 → 정적 HTML → GitHub Pages 패턴 그대로 차용)

## 1차 수록 부위 (7페이지)

- 어깨 (`body_md/01_shoulder.md`)
- 무릎 (`body_md/02_knee.md`)
- 발목 (`body_md/03_ankle.md`)
- 발바닥 (`body_md/04_foot.md`)
- 손목 (`body_md/05_wrist.md`)
- 허리 (`body_md/06_lowback.md`)
- **운동 일반** (`body_md/07_exercise_general.md`) — 9종 운동 카탈로그 + 일반 안전 원칙

## v2.0.0 현황 (Sprint 1~19)

- 4도메인 자동 회귀 **400/400 PASS**
- 품질 자체 점검 무이슈 **100%** × 4 (일반·약물·운동·응급진단)
- GUI 카드 6종 (Red Flag · 운동 금기 · 약물 비교 · 약물 상호작용 · 인구학 W4 · 운동 카탈로그)
- CI 자동: GitHub Actions push마다 400 시나리오 회귀

## 페이지 표준 구조 (모든 부위 공통)

```
0. 해부학 개요
1. 흔한 증상·질환 (감별진단표 + 본문)
2. 자가 체크리스트 (Red Flag 포함)
3. 진단 (신체검사 / 영상 / 검사실)
4. 치료
   4.1 약물 (성분·기전·용법·상호작용)
   4.2 물리치료 (단계별 모달리티)
   4.3 스트레칭·재활운동 (단계별)
5. 수술·전문의 의뢰 기준
6. 참고문헌 (DOI/PMID/공식 가이드라인)
7. 작성·검토·최종수정일
```

## 빠른 시작

```bash
# 1. 클론
git clone https://github.com/newwonwoo/ortho-kb.git
cd ortho-kb

# 2. 의존성 설치 (Python 3.10+)
pip install -r requirements.txt

# 3. 단일 부위 렌더
python scripts/render_html.py body_md/01_shoulder.md

# 4. 전체 빌드
python scripts/build_all.py

# 5. 검증 (면책·출처·스키마)
python scripts/validate.py

# 6. 결과 확인
# docs/body/*.html  또는  GitHub Pages: https://newwonwoo.github.io/ortho-kb
```

## 역할 분담

| 역할 | 책임 |
|---|---|
| 창업자 (newwonwoo) | 지분 100%, 모든 의사결정 |
| 감사역 | 면책·과장·출처 검수, 창업자 직속 |
| 팀장 | 일정·품질 게이트, 반복 지시 |
| 의사 연구원 | 해부·감별·진단·수술 적응증 |
| 약사 연구원 | 약물 풀세트 (OTC·처방·상호작용) |
| 물리치료사 연구원 | 모달리티·도수치료 |
| 재활치료사 연구원 | 단계별 스트레칭·재활운동 |
| 개발자(코더) | 렌더·빌드·배포 파이프라인 |
| 개발자(테스터) | 자동 검증, 품질확인서 |

## 라이선스

- **콘텐츠 (body_md/, wiki/)**: CC BY-NC-SA 4.0 (저작자 표시-비영리-동일조건변경허락)
- **코드 (scripts/, .github/)**: MIT License

## 기여 및 오류 신고

- GitHub Issues: 스크린샷 + 한 줄 설명이면 충분
- 약물·시술 관련 정정 요청은 출처(논문 DOI / 식약처 자료) 첨부 권장

## 신뢰성 정책

- 모든 약물·시술 정보는 **출처 2개 이상 교차 인용** 강제 (감사역 검수)
- 단정형 표현 회피 ("~할 수 있다", "~가 권고된다" 톤)
- 페이지 상단에 면책 배너 고정 (렌더링 시 자동 삽입)
