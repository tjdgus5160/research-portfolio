# CONTENT.md — 연구 항목 추가하는 법

이 사이트에 연구를 추가한다는 것은 **JSON 파일 하나를 쓰는 일**이다.
디자인을 건드릴 일도, HTML을 손댈 일도 없다.

```
content/entries/01-rb-cell-optics.json      ← 하나가 연구 항목 하나
```

파일을 만들고 `content/index.json` 목록에 한 줄 추가하면 끝이다.

---

## 항목 파일

```json
{
  "id": "01-rb-cell-optics",
  "number": "01",
  "title": "Rb 증기셀 광학계",
  "subtitle": "794.98 nm 펌프와 780.24 nm 프로브를 한 섬유로",
  "year": "2026",
  "status": "진행 중",
  "tags": ["optics", "vapor cell"],

  "meta": {
    "기간": "2025.03 – 2026.02",
    "역할": "설계 · 해석 · 검증",
    "방법": "파라메트릭 CAD · 편광 해석",
    "장비": "FreeCAD, LM Studio, 자체 검증 파이프라인"
  },

  "summary": "한 문단. 인덱스와 항목 머리에 같이 쓰인다.",

  "blocks": [ ... ]
}
```

`meta`의 키는 자유롭게 정해도 된다. 왼쪽 레일에 적힌 순서대로 나온다.

---

## 블록

`blocks`는 순서 있는 배열이다. 타입은 아래 여덟 개뿐이고, 새로 만들 일은 없다.

### `prose` — 한국어 본문

```json
{ "type": "prose", "text": "문단. 줄바꿈 두 번으로 문단을 나눈다.\n\n두 번째 문단." }
```

### `figure` — 그림

```json
{
  "type": "figure",
  "src": "assets/img/cell-optics.png",
  "alt": "증기셀 광학 경로",
  "width": 1600, "height": 1000,
  "caption": "빔 경로. 프리즘 두 개로 90°씩 꺾어 셀을 횡단한다.",
  "evidence": "ILLUSTRATIVE"
}
```

`width`와 `height`는 **반드시** 넣는다. 없으면 이미지가 로드될 때 글이 밀린다.

### `data` — 측정·계산 표

```json
{
  "type": "data",
  "caption": "셀 치수",
  "evidence": "SOURCE_FACT",
  "source": "Smith 2021, Table 1, p.3",
  "columns": ["파라미터", "값", "단위"],
  "rows": [["cell_length", "7.5", "mm"], ["cell_width", "7.5", "mm"]]
}
```

### `equation` — 유도

```json
{
  "type": "equation",
  "expr": "V = L·W·T − π(D/2)²·T",
  "inputs": { "L": "30.0 mm", "W": "20.0 mm", "T": "10.0 mm", "D": "8.0 mm" },
  "yields": "5497.345175 mm³",
  "evidence": "CALCULATED"
}
```

### `spec` — 파라미터 목록

```json
{
  "type": "spec",
  "items": [
    { "k": "coil_separation", "v": "10.5", "unit": "mm", "evidence": "CALCULATED" },
    { "k": "housing_wall",    "v": "2.0",  "unit": "mm", "evidence": "INFERRED" }
  ]
}
```

### `code`

```json
{ "type": "code", "lang": "bash", "text": "uv run cadctl build configs/opm_sensor.yaml" }
```

### `note` — 단서·가정·미해결

```json
{ "type": "note", "kind": "가정", "text": "원문에 없어 가공성을 기준으로 정했다." }
```

### `refs` — 인용

```json
{
  "type": "refs",
  "items": [
    { "text": "Smith et al., Rev. Sci. Instrum. 92, 015004 (2021)", "doi": "10.1063/5.0031503" }
  ]
}
```

---

## 증거 등급 — 이게 이 사이트의 요점이다

`figure`, `data`, `equation`, `spec`의 항목은 **반드시** `evidence`를 갖는다.

| 등급 | 뜻 | 같이 적을 것 |
|---|---|---|
| `SOURCE_FACT` | 인용된 원문에 있는 값 | `source` |
| `CALCULATED` | 위 값들에서 유도한 값 | `inputs`, `yields` |
| `INFERRED` | 근거 있는 가정 | `reasoning` |
| `ILLUSTRATIVE` | 그림이 읽히라고 있는 것. 물리적 주장 없음 | — |

렌더링을 측정처럼 보이게 두는 것은 스타일 선택이 아니라 결함이다.
값이 없으면 `INFERRED`나 `ILLUSTRATIVE`이지, 지어내서 `SOURCE_FACT`로 올리는 일은 없다.
모르면 모른다고 적는 편이 언제나 낫다.

**인용은 지어내지 않는다.** DOI, arXiv ID, 실제로 받은 URL 중 하나로 반드시 닿아야 한다.

---

## 목록에 등록

`content/index.json`:

```json
{
  "entries": [
    { "id": "01-rb-cell-optics", "file": "content/entries/01-rb-cell-optics.json" },
    { "id": "02-balanced-polarimeter", "file": "content/entries/02-balanced-polarimeter.json" }
  ]
}
```

위에서부터 인덱스에 나온다.

---

## 확인

```bash
python3 scripts/validators/validate_content.py
```

증거 등급이 빠졌거나, 등급이 요구하는 필드가 없거나, 그림에 크기가 없거나,
블록 타입이 목록에 없으면 여기서 잡힌다. 통과해야 올린다.
