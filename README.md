# research-portfolio

박성현 · OPM(광펌핑 자력계) 연구 포트폴리오.

프레임워크 없음. 빌드 도구 없음. HTML, CSS, ES 모듈뿐이다.

---

## 연구 하나 추가하기

1. `content/entries/03-무엇.json` 을 쓴다 — 형식은 **[CONTENT.md](CONTENT.md)**.
2. `content/index.json` 에 한 줄 추가한다.
3. 확인하고 빌드한다.

```bash
python3 scripts/validators/validate_content.py   # 증거 등급·필수 필드 검사
python3 scripts/build_site.py                    # 항목 페이지와 인덱스 생성
python3 scripts/validators/validate_site.py      # 토큰·마크업·접근성 검사
```

HTML은 손대지 않는다. `index.html` 의 인덱스 행과 `entry-*.html` 은 전부 생성물이다.

## 미리보기

```bash
python3 -m http.server 8765
open http://127.0.0.1:8765/index.html
```

`file://` 로는 열지 말 것. ES 모듈이 로드되지 않는다.

---

## 무엇이 어디에 있나

```
DESIGN.md                    디자인 스펙. 색·타입·레이아웃의 근거가 전부 여기 있다
CONTENT.md                   연구 항목 형식
AGENTS.md                    에이전트 작업 규칙

index.html                   손으로 관리. 단 인덱스 행 구간은 생성물
entry-<id>.html              전부 생성물 — 직접 고치지 말 것

assets/css/tokens.css        디자인 시스템. 색·크기·시간은 전부 여기서만 정의한다
assets/css/base.css          리셋, 문서 타이포, 레이아웃 프리미티브
assets/css/components.css    히어로 · 인덱스 · 항목 · 블록 · 칩
assets/js/fid.js             히어로의 FID 파형. 명시된 파라미터로 계산한다
assets/js/site.js            스크롤 리빌

content/index.json           항목 목록
content/entries/*.json       항목 하나당 파일 하나
content/index-rows.html      생성물

scripts/build_site.py        JSON → HTML
scripts/blocks.py            블록 8종의 렌더러
scripts/validators/          게이트
scripts/doctor.sh            작업 전 환경 점검
```

---

## 규칙 두 개

**색·크기·시간은 `tokens.css` 밖에서 선언하지 않는다.** hex 코드나 px 폰트 크기가
다른 파일에 있으면 `validate_site.py` 가 실패시킨다. 필요한 값에 토큰이 없다면
그건 디자인 결정이지 구현 결정이 아니다.

**측정한 것과 가정한 것을 섞지 않는다.** 그림·표·수식·파라미터는 모두 증거 등급을
갖는다 — `SOURCE_FACT` / `CALCULATED` / `INFERRED` / `ILLUSTRATIVE`. 렌더링을
측정처럼 보이게 두는 것은 스타일 선택이 아니라 결함이고, `validate_content.py` 가
잡는다.

히어로의 FID 파형도 같은 규칙을 따른다. 실제 파라미터로 계산한 것이고,
페이지에 "측정 데이터가 아니다"라고 적혀 있다.
