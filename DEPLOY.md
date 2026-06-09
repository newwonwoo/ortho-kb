# 🚀 ortho-kb 배포 안내서 (창업자 전용)

> 본 안내서는 창업자(newwonwoo) PowerShell 환경 기준입니다.
> 한 줄씩 따라 실행하면 됩니다. 각 명령어 옆 #에 뜻을 적었습니다.

## 0. 준비 확인 (한 번만)

PowerShell에 다음 도구가 설치되어 있는지 확인:

```powershell
git --version       # git이 설치되어 있어야 함 (없으면 https://git-scm.com/)
gh --version        # GitHub CLI (선택, 있으면 더 편함, 없어도 됨)
python --version    # Python 3.10+ (로컬 빌드 확인용, 선택)
```

GitHub 로그인 (한 번만):
```powershell
gh auth login       # 브라우저 열려서 인증 — gh 없으면 push 단계에서 비번 물어봄
```

## 1. 압축 해제 + 폴더 들어가기

```powershell
# Claude가 제공한 ortho-kb.zip을 원하는 위치(예: C:\projects)에 풀고
cd C:\projects\ortho-kb
```

## 2. Git 초기화 + 첫 커밋

```powershell
git init                                       # 새 git 저장소 시작
git add .                                      # _unverified/ 빼고 모든 파일 스테이지
git status                                     # _unverified/ 가 안 보이면 정상 (.gitignore 작동)
git commit -m "Initial commit: ortho-kb v2.0.0 (Sprint 1~19, 4도메인 일제 100%)"
git branch -M main                             # 기본 브랜치 이름 main으로
```

**v2.0.0 핵심 내용 (커밋 메시지에 포함되는 변경 사항)**:
- 7페이지 콘텐츠 (6부위 + 운동 일반 카탈로그)
- 226 검색 인덱스 청크 + 동의어 399+ 매핑
- 4도메인 자동 회귀 400/400 PASS (일반·약물·운동·응급진단)
- 품질 자체 점검 무이슈율 100% (4도메인 일제)
- GUI 카드 6종 (Red Flag·운동 금기·약물 비교/상호작용·인구학·운동 카탈로그)
- CI: GitHub Actions push마다 400개 회귀 자동
- 라이선스: 콘텐츠 CC BY-NC-SA 4.0, 코드 MIT

## 3. GitHub에 리포지토리 만들기

### 옵션 A — `gh` CLI 사용 (한 줄로 끝남)
```powershell
gh repo create newwonwoo/ortho-kb --public --source=. --push
# Public이라 누구나 읽을 수 있음. CC BY-NC-SA 4.0 + MIT.
```

### 옵션 B — 웹에서 만들기
1. https://github.com/new 접속
2. Repository name: `ortho-kb`
3. Public 선택
4. **README·.gitignore·라이선스 추가 옵션 모두 OFF** (이미 다 있음)
5. Create 클릭
6. PowerShell로 돌아와서:
   ```powershell
   git remote add origin https://github.com/newwonwoo/ortho-kb.git
   git push -u origin main
   ```

## 4. GitHub Pages 활성화

브라우저로:
1. https://github.com/newwonwoo/ortho-kb/settings/pages
2. **Source** 드롭다운에서 **"Deploy from a branch"** 선택
3. **Branch** 드롭다운에서 **`main`** + **`/docs`** 선택 → Save
4. 1~2분 기다림
5. 같은 페이지 상단에 사이트 주소가 뜸:
   👉 **`https://newwonwoo.github.io/ortho-kb/`**

## 5. 배포 적합성 체크리스트 (사이트 뜬 후)

### 5.1 메인 페이지
- [ ] https://newwonwoo.github.io/ortho-kb/ 접속됨
- [ ] 6부위(어깨/무릎/발목/발바닥/손목/허리) 링크 보임
- [ ] 상단 면책 배너 노란색으로 표시됨

### 5.2 어깨 페이지 (대표 페이지)
- [ ] https://newwonwoo.github.io/ortho-kb/body/01_shoulder.html 접속됨
- [ ] Codman pendulum SVG 표시됨 (막대인간 그림)
- [ ] Theraband 외회전 SVG 표시됨
- [ ] 면책 배너 페이지 상단에 보임
- [ ] 표 3개 모두 정렬 정상 (감별진단·상호작용·신체검사)

### 5.3 허리 페이지 (SVG가 가장 많은 페이지)
- [ ] https://newwonwoo.github.io/ortho-kb/body/06_lowback.html 접속됨
- [ ] SVG 5종 모두 표시 (펠빅 틸트·캣카우·데드버그·버드독·브릿지)
- [ ] **마미증후군** 섹션이 빨간 강조로 보임

### 5.4 챗봇 검색 (Sprint 19 v2.0.0 카드 6종)
- [ ] https://newwonwoo.github.io/ortho-kb/search/ 접속됨
- [ ] 검색창에 `어깨 야간통` 입력 후 Enter → 결과 3개 표시
- [ ] `데드버그 코어` 검색 → 허리 3단계 1위
- [ ] `동결견` 검색 → 어깨 1.3 섹션 1위
- [ ] **Red Flag 카드**: `마미증후군` 또는 `대소변 장애 동반 허리` → 빨강 카드
- [ ] **운동 금기 카드**: `디스크 환자 윗몸일으키기` → 노란 카드
- [ ] **약물 상호작용 카드**: `셀레콕시브 와파린` → 파란 카드
- [ ] **W4 인구학 카드**: `50대 여성 어깨` → 위험인자 카드
- [ ] **운동 카탈로그 카드**: `데드리프트` → teal 카드 (금기 환자군 포함)
- [ ] **약물 비교 카드**: `이부프로펜 vs 나프록센` → 비교 카드
- [ ] 응답 말미에 면책 경고 문구 보임

### 5.5 면책 조항 전문
- [ ] https://newwonwoo.github.io/ortho-kb/DISCLAIMER.html 접속됨
- [ ] 7개 항목 모두 보임

## 6. 만약 어딘가 깨졌으면

### Pages가 안 뜸
- Settings → Pages에서 Branch=`main` `/docs` 다시 확인
- Actions 탭에서 deploy job이 성공인지 확인
- 5~10분 더 기다림 (첫 배포는 느림)

### CSS가 안 먹음
- 브라우저 캐시 초기화 (Ctrl+Shift+R)
- `docs/assets/style.css`가 push에 포함됐는지 확인:
  ```powershell
  git ls-files docs/assets/style.css
  ```

### 챗봇 검색 결과가 안 나옴
- `docs/search/index.json`이 push에 포함됐는지 확인:
  ```powershell
  git ls-files docs/search/index.json
  ```
- 브라우저 개발자도구(F12) → Console에 에러 메시지 확인

## 7. 이후 콘텐츠 업데이트 흐름

콘텐츠를 수정하고 다시 배포:

```powershell
# 1) 마크다운 수정 (예: 어깨)
notepad body_md/01_shoulder.md

# 2) 로컬에서 빌드 (Python 설치되어 있으면)
pip install -r requirements.txt
python scripts/validate.py        # 검증
python scripts/build_all.py        # 빌드 (docs/ 갱신)

# 3) push
git add .
git commit -m "어깨: 회전근개 단락 보강"
git push
```

> 💡 Python 설치가 어려우면, 마크다운만 수정해서 push해도 됩니다.
> 단, 그러면 HTML이 갱신 안 돼서 사이트에는 반영 안 됨.
> 이 경우 GitHub Actions를 활성화해서 자동 빌드 받는 것이 권장.

## 8. GitHub Actions 자동 빌드 (선택)

Settings → Pages → Source를 **"GitHub Actions"**로 변경하면
`.github/workflows/build.yml`이 push마다 자동 빌드함. 이렇게 하면 마크다운만
수정·push해도 사이트 자동 갱신됨.

다만 **첫 배포는 위의 옵션 A(deploy from /docs)로 안전하게 띄우고**, 나중에
Actions로 전환하는 것을 권장.

---

## 도움말

- 문제 발생 시 GitHub Issues: https://github.com/newwonwoo/ortho-kb/issues
- 배포 작업 자체에 대한 질문은 이 대화 세션에서 다음 턴에 이어서 가능

*문서 작성: 2026-06-06 · 팀장 (Claude)*
