# Content Strategy Google Docs 업데이트 가이드

## 목표

`03-content-strategy.md` 문서를 Google Docs에 업로드하면서:
- Mermaid 다이어그램 → PNG 이미지로 변환
- 마크다운 테이블 → Google Docs 네이티브 테이블로 변환
- 문서 구조 유지 (제목, 볼드, 인용 등)

---

## 실행 순서

### 1단계: Mermaid 다이어그램 PNG 생성

```powershell
cd D:\AI\claude01\wsoptv_v2\frontend
node capture-content-strategy.js
```

**생성되는 파일 (9개):**
- `docs/wireframes/v2/cs-core-content.png`
- `docs/wireframes/v2/cs-content-pie.png` ← **NEW: 파이차트**
- `docs/wireframes/v2/cs-content-detail.png`
- `docs/wireframes/v2/cs-bracelet-structure.png`
- `docs/wireframes/v2/cs-main-event.png`
- `docs/wireframes/v2/cs-other-events.png`
- `docs/wireframes/v2/cs-youtube-wsoptv.png`
- `docs/wireframes/v2/cs-curation-roadmap.png`
- `docs/wireframes/v2/cs-season-calendar.png`

**확인 방법:**
```powershell
ls D:\AI\claude01\wsoptv_v2\docs\wireframes\v2\cs-*.png
```

9개 파일이 모두 있어야 다음 단계 진행 가능.

---

### 2단계: Google Docs 업로드

```powershell
cd D:\AI\claude01\wsoptv_v2
python scripts/upload_content_strategy.py
```

**스크립트가 수행하는 작업:**

1. **Google Drive 이미지 업로드**
   - 9개의 PNG 이미지를 Google Drive에 업로드
   - 각 이미지를 "Anyone with link" 권한으로 설정
   - 이미지 ID를 `docs/wireframes/v2/image_ids.json`에 저장

2. **새 Google Docs 문서 생성**
   - 제목: "WSOPTV - 콘텐츠 전략 (03-content-strategy)"
   - 자동으로 고유 Document ID 생성

3. **마크다운 파싱 및 변환**
   - `#` → Heading 1
   - `##` → Heading 2
   - `###` → Heading 3
   - `**Bold**` → Bold
   - `> Quote` → Blockquote (들여쓰기 + 이탤릭)
   - ` ```mermaid ... ``` ` → PNG 이미지 삽입
   - `| Table |` → Google Docs 네이티브 테이블

4. **테이블 삽입**
   - 마크다운 테이블을 Google Docs 테이블로 변환
   - 첫 번째 행은 자동으로 Bold 처리
   - API 제한 회피를 위해 10초 대기 (5개 테이블마다)

---

## 출력 예시

```
Loading credentials...
Building Drive service...

Uploading Content Strategy diagram images to Google Drive...
  Updated: cs-core-content.png (ID: 1ABC...)
  Updated: cs-content-pie.png (ID: 1DEF...)
  Updated: cs-content-detail.png (ID: 1GHI...)
  ...

--- Uploaded 9 images ---

Loading PRD content...
Building Docs service...
Creating new Google Doc...
  Created document ID: 1gelKPXZBtNoJpTJOg7aCWqWYdHdUk5VwvL8by8ln82o

Parsing markdown with images...
Applying 1200+ updates to document...
  Applied requests 1 to 100
  Applied requests 101 to 200
  ...

Inserting 25 tables...
  Inserted table: 6x2
  Inserted table: 3x4
  ...

Document created successfully!
View at: https://docs.google.com/document/d/1gelKPXZBtNoJpTJOg7aCWqWYdHdUk5VwvL8by8ln82o/edit
```

---

## 예상 소요 시간

| 단계 | 시간 |
|------|------|
| PNG 생성 (Playwright) | 10초 |
| 이미지 업로드 (9개) | 30초 |
| 문서 생성 및 파싱 | 20초 |
| 테이블 삽입 (25개) | 120초 (API 제한) |
| **총 소요 시간** | **약 3분** |

---

## 트러블슈팅

### 문제 1: PNG 파일이 생성되지 않음

**원인:** Playwright가 설치되지 않음

**해결:**
```powershell
cd D:\AI\claude01\wsoptv_v2\frontend
npm install @playwright/test
npx playwright install chromium
```

### 문제 2: "token.json not found"

**원인:** Google API 인증 토큰이 없음

**해결:**
1. `D:\AI\claude01\json\token.json` 파일이 있는지 확인
2. 없으면 Google Cloud Console에서 OAuth 2.0 인증 재설정

### 문제 3: "Quota exceeded" 오류

**원인:** Google Docs API 요청 제한 초과

**해결:**
- 스크립트가 자동으로 10초 대기 (5개 테이블마다)
- 그래도 실패 시 30초 후 재실행

### 문제 4: 테이블이 깨짐

**원인:** 마크다운 테이블 구문 오류

**해결:**
- 원본 마크다운 파일에서 테이블 구문 확인
- 모든 행이 동일한 열 개수를 가져야 함
- 구분자 행 (`|---|---|`) 필수

---

## 기대 결과

Google Docs 문서 URL:
```
https://docs.google.com/document/d/1gelKPXZBtNoJpTJOg7aCWqWYdHdUk5VwvL8by8ln82o/edit
```

**문서 구조:**
- ✅ 모든 제목이 올바른 스타일 적용
- ✅ 9개의 다이어그램 이미지가 본문에 삽입
- ✅ 25개 이상의 테이블이 네이티브 Google Docs 테이블로 변환
- ✅ Bold, Blockquote 등 서식 유지
- ✅ 구분선 (`---`) → 수평선 (─────)

---

## 검증 체크리스트

- [ ] PNG 파일 9개 모두 생성됨
- [ ] `image_ids.json`에 9개 이미지 ID 저장됨
- [ ] Google Docs 문서가 생성됨
- [ ] 문서 내 이미지가 모두 표시됨 (깨진 이미지 없음)
- [ ] 테이블이 올바르게 렌더링됨
- [ ] 제목 스타일이 적용됨
- [ ] Blockquote가 들여쓰기 + 이탤릭으로 표시됨

---

## 다음 단계

문서 업데이트 완료 후:

1. **수동 검토**
   - Google Docs에서 문서 열기
   - 이미지 크기 조정 (필요 시)
   - 테이블 정렬 확인

2. **체크리스트 업데이트**
   ```powershell
   # wsoptv_checklist.yaml 편집
   # status: completed로 변경
   # last_sync: 현재 시간 기록
   ```

3. **Git 커밋**
   ```powershell
   git add docs/wireframes/v2/cs-*.png
   git add docs/wireframes/v2/image_ids.json
   git add tasks/prds/0010-prd-wsoptv/03-content-strategy-gdocs.md
   git commit -m "docs: add content strategy Google Docs with Mermaid images"
   ```

---

*생성 일시: 2025-12-19*
