# CONTENT.md — 연구 항목 추가하는 법

항목 하나 = `content/entries/` 안의 JSON 파일 하나. HTML도 CSS도 건드리지
않습니다. 목록 파일에 등록할 필요도 없습니다 — `build_entries.py`가 디렉터리를
읽습니다.

> 이 문서는 예전에 `content/index.json`에 한 줄 추가하라고 안내했습니다. 그
> 파일은 더 이상 쓰이지 않고, 그 안에 적힌 두 경로는 존재하지 않습니다. 읽는
> 것은 폐기된 `validate_content.py` 하나뿐입니다.

```bash
$EDITOR content/entries/t09-my-thing.json
node    scripts/render_math.mjs        # 수식을 넣었다면
python3 scripts/build_entries.py       # work/t09-my-thing.html + 카드
python3 scripts/build_index.py
```

파일 이름은 `slug`와 같아야 합니다. 번호 접두사는 `t` = 이론 계산,
`w` = 만든 것.

---

## 스키마

필수 키는 이것이 전부입니다.

```json
{
  "no": "T/09",
  "slug": "t09-my-thing",
  "title": "한국어 제목",
  "subtitle": "ENGLISH KICKER, 대문자",
  "status": "complete",
  "date": "2026-09",
  "repo": "scripts/solve_my_thing.py",
  "summary": "카드와 페이지 머리에 나오는 두세 문장.",
  "question": "이 항목이 답하려는 질문 하나."
}
```

`repo`는 **작업이 있는 곳**입니다. 이 저장소 안이면 스크립트 경로, 다른
저장소면 그 이름(`opm-freecad-cli`, `research-agent`). 비워 두면
`validate_math.py`가 실패합니다 — 산출물 경로가 어디에도 닿지 않게 되기
때문입니다.

## 본문 절

| 키 | 모양 | 절 제목 |
|---|---|---|
| `evidence` | `[{claim, class, source}]` | 근거 |
| `method` | `[{step, name, detail}]` | 어떻게 했나 |
| `numbers` | `[{name, value, unit, class, note}]` | 수치 |
| `geometry` | `{tolerance, renders, equations, parametric_note}` | 그림과 수식 |
| `validation` | `{verdict, checks:[{name, result, how}]}` | 검증 |
| `defect` | `{what, found_by, cause, fix, prevention}` | 발견된 결함 |
| `correction` | 아래 객체 하나 또는 그 목록 | 정정 기록 |
| `unknown` | `["문자열", …]` | 아직 모르는 것 |
| `artifacts` | `[{path, note}]` | 산출물 |
| `en` | `{title, summary, question}` | 영어 카드 |

없는 절은 그냥 빼면 됩니다. 절 번호는 세어서 붙으므로 비워도 어긋나지
않습니다.

## 등급

모든 `class`는 넷 중 하나입니다.

| 등급 | 뜻 | 함께 적어야 하는 것 |
|---|---|---|
| `SOURCE_FACT` | 출처에 그렇게 적혀 있음 | 어느 문서 어디인지 |
| `CALCULATED` | 위 값들에서 유도 | 식과 입력 |
| `INFERRED` | 근거를 밝힌 가정 | 왜 그렇게 골랐는지 |
| `ILLUSTRATIVE` | 그림을 위한 것 | — 물리적 주장 없음 |

모르면 `INFERRED`로 적고 `unknown`에 한 줄 남깁니다. 지어내는 것보다 모른다고
적는 쪽이 언제나 낫습니다.

## 수식

`geometry.equations`에 LaTeX로 씁니다. 조판은 빌드할 때 KaTeX가 하고 결과는
`content/math.json`에 캐시됩니다.

```json
{
  "tex": "\\frac{1}{T_1} = \\frac{R_{\\mathrm{SD}}}{q} + R_{\\mathrm{wall}}",
  "name": "세로 완화",
  "src": "seltzer2008",
  "where": "식 (2.133)",
  "class": "SOURCE_FACT",
  "note": "선택. 한 문단 정도의 설명."
}
```

`src`는 `content/sources.json`에 있는 id여야 합니다. 없는 출처를 쓰려면 거기
먼저 등록하십시오 — `held`가 `disk`면 파일과 sha256까지 적습니다.

`where`는 **출처 안의 어디인지**입니다. 갖고 있는 문헌(`disk`·`zotero`)을
인용하면서 이것을 비우면 게이트가 실패합니다. 문서 전체를 가리키는 것은
인용이 아닙니다.

`held`가 `named`인 출처(지목만 되었고 갖고 있지 않은 것)는 `SOURCE_FACT`를
받칠 수 없습니다. 게이트가 막습니다.

수식을 고쳤으면 `node scripts/render_math.mjs`를 다시 돌려야 합니다. 잊으면
`--check`가 잡습니다.

## 그림

```json
{"src": "assets/diagrams/my-figure.svg",
 "view": "SHORT CAPS LABEL", "alt": "화면을 못 보는 사람에게 설명",
 "note": "이 그림이 왜 여기 있는지"}
```

SVG는 인라인으로 들어가므로 `--t0`~`--t3`을 그대로 물려받고 팔레트 전환을
따라갑니다. `<img>`로 넣으면 격리되어 팔레트를 못 봅니다. 색을 직접 쓰지
마십시오.

라벨이 뷰박스를 벗어나면 페이지에서 잘립니다.
`node scripts/validators/svg_fit.mjs assets/diagrams`가 잡습니다.

## 고친 기록

틀린 것을 지우지 않습니다. 정정을 덧붙입니다. 한 항목이 여러 번 정정될 수
있으므로 목록으로 둘 수 있고, 날짜 역순으로 렌더됩니다.

```json
"correction": {
  "date": "2026-09-13",
  "what": "무엇이 틀렸는지, 옛 값과 새 값을 함께",
  "why": "왜 틀렸는지 — 물리든 코드든",
  "how": "어쩌다 그렇게 됐는지. 변명이 아니라 경위",
  "found_by": "무엇이 그것을 드러냈는지"
}
```

## 넣기 전에

```bash
python3 scripts/build_entries.py --check      # 페이지가 JSON과 맞는가
python3 scripts/validators/validate_math.py   # 인용·산출물 경로
node    scripts/render_math.mjs --check
node    scripts/validators/svg_fit.mjs assets/diagrams
node    scripts/validators/contrast.mjs       # 서버 필요
node    scripts/validators/page_width.mjs     # 서버 필요
```
