# 집필 스타일 가이드 (STYLE_GUIDE.md)

## 1. 톤과 어조

- **단정형 금지**:
  - ❌ "~를 치료한다", "~를 처방한다", "~가 정답이다"
  - ✅ "~가 권고된다 (출처)", "~를 고려할 수 있다 (출처)", "~보고가 있다 (출처)"
- 의학적 불확실성을 솔직하게 표현. "근거가 제한적이다", "메타분석은 일관되지 않다" 등 OK.

## 2. 출처 형식 (강제)

모든 의학적 진술은 **출처 2개 이상 교차 인용**.

### 논문
```
저자. 제목. 저널. 연도;권(호):페이지. doi:10.xxxx/yyyy
```
예:
```
Trelle S, et al. Cardiovascular safety of non-steroidal anti-inflammatory drugs:
network meta-analysis. BMJ. 2011;342:c7086. doi:10.1136/bmj.c7086
```

### 가이드라인
```
발행기관. 제목. 연도. URL
```
예:
```
NICE Guideline NG226. Osteoarthritis in over 16s: diagnosis and management. 2022.
https://www.nice.org.uk/guidance/ng226
```

### 식약처
```
식약처 의약품안전나라. [성분명] 허가사항. 조회일: YYYY-MM-DD.
URL (nedrug.mfds.go.kr/...)
```

### UpToDate / Lexicomp 등 구독 자료
- 단독 인용 금지. 반드시 1차 자료(논문·가이드라인)와 병기.
- 형식: `UpToDate. [Topic]. (보조 참고)`

## 3. 약물 표기 표준

- 형식: `성분명 (영문) — 대표 상품명`
  - 예: `이부프로펜 (Ibuprofen) — 부루펜`
- 처방약/일반의약품 명시
- 용법: `용량 단위 × 횟수/일 (최대 일일용량)`
- 상호작용: 별도 표로 정리

## 4. 운동·스트레칭 표기

- 자세 / 동작 / 횟수·세트 / 목적 / 금기 / 단계 명시
- 단계: 급성기(0~2주) / 아급성기(2~6주) / 만성기(6주~) / 복귀기
- 통증 척도: NRS 0~10 사용 ("통증 5점 초과 시 중단")

## 5. 감별진단표 형식

| 양상 | 의심 질환 |
|---|---|
| 구체적 임상 양상 | 가능한 질환명 |

- 양상 칸은 검사자(독자)가 관찰 가능한 표현으로
- 절대 판단 금지: "이러면 X다" → "이러면 X 가능성을 고려한다"

## 6. Red Flag 섹션

각 부위 문서 상단 가까이 배치. 다음 항목 누락 금지:
- 외상 후 변형 / 즉시 사용 불능
- 발열 동반 (감염 감별)
- 야간통 (악성·심한 염증 감별)
- 신경학적 결손 (마비·감각저하·괄약근 장애)
- 양측성 + 체중감소 (전신질환·악성종양 감별)

## 7. 면책 배너 (자동 삽입)

- 모든 마크다운 파일은 `# 제목` 아래 빈 줄 다음에 면책 배너가 자동 삽입됨.
- 작성자는 면책 배너를 직접 쓰지 않음. 렌더링 단계에서 `scripts/render_html.py`가 삽입.
- 배너 텍스트는 `DISCLAIMER.md`에서 발췌.

## 8. 파일명 규칙

- `body_md/NN_부위영문.md` (예: `01_shoulder.md`)
- 자산: `assets/NN_부위/` 하위에 이미지·SVG·도해
- 영문 슬러그 강제: shoulder / knee / ankle / foot / wrist / lowback

## 9. 메타데이터 헤더 (YAML front matter)

각 마크다운 파일 최상단에 다음 헤더 필수:

```yaml
---
slug: shoulder
title: 어깨
authors:
  - role: 의사
    name: TBD
  - role: 약사
    name: TBD
  - role: 물리치료사
    name: TBD
  - role: 재활치료사
    name: TBD
reviewer: 감사역
last_updated: 2026-06-06
version: 0.1.0
license: CC BY-NC-SA 4.0
---
```

## 10. 검증 통과 기준 (validate.py)

- [ ] YAML front matter 존재 + 필수 필드 충족
- [ ] H1 제목 1개만 존재
- [ ] 면책 배너 위치 정확 (제목 직후)
- [ ] 섹션 0~7 모두 존재
- [ ] 약물 섹션 각 항목에 출처 2개 이상
- [ ] 단정형 금지 표현 검출 (워치리스트 워드)
- [ ] 깨진 링크 없음
- [ ] last_updated 6개월 이내

자동 검증 실패 시 머지 차단(CI).
