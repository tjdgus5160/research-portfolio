# SHP® — 연구 포트폴리오

**https://tjdgus5160.github.io/research-portfolio/**

⁸⁷Rb 광펌핑 자력계에 관한 계산과 설계를 모아둔 정적 사이트입니다. 서버도,
빌드 도구 체인도, API 키도 필요 없습니다. `index.html`을 브라우저로 열면 그대로
동작합니다.

이 README는 예전에 이 저장소가 무엇이었는지를 설명하고 있었습니다(webisoft.com
디자인 재현). 그 단계는 끝났고, 현재 인터페이스는 4색 8비트 핸드헬드로 새로
만든 것입니다. `scripts/validators/validate_copy.py`가 그때의 문구가 하나도
남아 있지 않다는 것을 매 실행마다 검사합니다.

---

## 구조

```
index.html  en/index.html      한국어·영어 첫 화면 (생성물)
work/*.html                    연구 항목 페이지 (생성물)
gallery*.html                  생성한 이미지 모음 (생성물)

content/entries/*.json         ← 손으로 쓰는 것은 사실상 이것뿐
content/site.{ko,en}.json      첫 화면 문구
content/sources.json           수식이 인용하는 출처 등록부
content/math.json              LaTeX → MathML 조판 캐시 (생성물)

scripts/*.py                   계산과 페이지 생성
scripts/validators/            게이트
analysis/*.json                계산 결과 (생성물)
assets/diagrams/*.svg          그림 (생성물)
input/papers/                  사람이 넣은 원본 PDF
```

`content/entries/`의 JSON 하나가 연구 항목 하나입니다. 스키마와 쓰는 법은
[CONTENT.md](CONTENT.md)에 있습니다.

## 스타일

색은 `styles.css`의 `:root`에 있는 `--t0`(가장 어두움)부터 `--t3`(화면 바탕)
까지 네 개뿐입니다. `:root[data-pal="dmg"]`가 초록 게임보이 팔레트입니다. 픽셀
단위는 `--px` 하나로, 720px 아래에서 4px에서 3px로 줄어듭니다. 모든 타이밍은
`steps()`입니다 — 부드럽게 움직이는 것이 하나도 없는 것이 의도입니다.

## 다시 만들기

```bash
python3 scripts/solve_relaxation.py        # 계산 → analysis/*.json + 그림
node    scripts/render_math.mjs            # 수식 → content/math.json
python3 scripts/build_entries.py           # → work/*.html + 두 첫 화면의 카드
python3 scripts/build_index.py             # → index.html, en/index.html
```

계산 스크립트는 전부 `--check`를 받습니다. 디스크와 다른 결과가 나오면 0이 아닌
값으로 끝납니다.

## 게이트

```bash
python3 -m http.server 8788 &              # 브라우저를 쓰는 게이트에 필요

python3 scripts/validators/validate_copy.py    # 문구가 제자리에 있는가
python3 scripts/validators/validate_math.py    # 수식·인용·산출물 경로
node    scripts/render_math.mjs --check        # 조판 캐시가 최신인가
node    scripts/validators/contrast.mjs        # 실제로 렌더된 글자의 대비
node    scripts/validators/page_width.mjs      # 가로 스크롤이 생기지 않는가
node    scripts/validators/svg_fit.mjs assets/diagrams   # 그림 라벨이 프레임 안인가
python3 scripts/wigner.py                      # 3-j·6-j·d 항등식 자가검사
```

어떤 게이트가 왜 있고 어떤 것이 폐기되었는지는
[scripts/validators/README.md](scripts/validators/README.md)에 있습니다.
**폐기된 것은 실행하지 마십시오** — 통과할 수 없는 검사는 검사를 무시하는
습관을 가르칩니다.

## 이 사이트가 지키려는 것

모든 수치가 네 등급 중 하나를 답니다: `SOURCE_FACT`(출처에 적혀 있음),
`CALCULATED`(위 값들에서 유도), `INFERRED`(근거를 밝힌 가정),
`ILLUSTRATIVE`(그림을 위한 것, 물리적 주장 없음). 모르는 것은 모른다고 적습니다
— 각 항목의 "아직 모르는 것" 절이 그것입니다.

틀린 것은 지우지 않고 정정 기록으로 남깁니다. 무엇이 틀렸고, 왜 틀렸고, 어쩌다
그렇게 됐고, 누가 찾았는지까지 적습니다.

## 만든 것

인터페이스, 픽셀 아트, 그림 전부 이 저장소의 코드가 생성합니다. 외부 디자인이나
이미지를 가져다 쓰지 않았습니다. 생성 이미지의 프롬프트와 설정은
`assets/prompts.md`에 기록되어 있습니다.
