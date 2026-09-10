**다음 변경 제안 — 연구 결과를 실제로 확인할 수 있는 포트폴리오**

2026-09-10 KST · 검토 기준: `4255b8f`와 현재 작업 트리. 구현은 하지 않았다. 아래 작업량과 증감 예산은 예상치이고, 현재 파일 크기·검사 결과·원본 대조 결과는 이번 검토에서 직접 얻었다.

가장 큰 문제는 연구 자료가 없다는 것이 아니다. 자료는 이 기계에 있고, 페이지는 그 자료의 일부를 잘못 옮겼으며, 방문자는 원본을 열 수 없다. 최근의 디자인보다 이 문제를 먼저 고쳐야 한다.

**검토 범위와 측정 한계**

`index.html`, `en/index.html`, `work/*.html`, `gallery.html`, 세 stylesheet, 두 JavaScript 파일, 네 generator, 다섯 validator, 두 locale JSON, 현재 entry JSON 세 개, 이전 content contract, 최근 `git log --oneline -40`, `.github/workflows/gates.yml`을 확인했다. Gallery의 126개 record에서 provenance 필드도 집계했다. Entry가 가리키는 두 외부 로컬 저장소까지 따라가 파일 존재·크기·hash·관련 값을 대조했다.

실제 브라우저 성능 측정은 완료하지 못했다. Live URL은 web 도구에서 열리지 않았고, `curl`은 `Could not resolve host`로 실패했다. Orca browser는 `runtime_open_timeout`, 설치된 Chromium은 macOS sandbox의 `Permission denied (1100)`로 시작하지 못했다. 따라서 다음 값은 **미측정**이다: 배포판과 작업 트리의 일치 여부, 실제 HTTP 요청 수와 압축 전송량, 초기/scroll 후 gallery thumbnail 다운로드 수, browser JavaScript 실행 시간, LCP·CLS·INP, 실행 중 CSS coverage. 이 값을 파일 크기나 코드의 frame cap으로 대신하지 않는다. 아래 브라우저 결함은 명시한 경우 source 분석에 따른 판정이며, 화면 재현 결과로 주장하지 않는다.

**직접 확인한 기준선**

| 대상 | 로컬 파일 크기, bytes | 직접 연결한 로컬 resource 수¹ | 그 resource를 모두 합친 bytes¹ |
| --- | ---: | ---: | ---: |
| `index.html` | 11,152 | 14 | 88,811 |
| `en/index.html` | 11,103 | 14 | 88,762 |
| `work/w01-rb-cell-optics.html` | 9,871 | 6 | 71,141 |
| `work/w02-balanced-polarimeter.html` | 8,739 | 6 | 70,009 |
| `work/w03-supervised-pipeline.html` | 10,988 | 9 | 91,746 |
| `gallery.html` | 179,201 | 127 | 5,391,304 |

¹ HTML 자신과 그 HTML의 `href`/`src`가 직접 참조하는 CSS·JS·image·favicon의 고유 파일 목록이다. **실제 request count가 아니다.** Font stylesheet·font subset·CSS background·실제 cache/lazy 동작은 제외했다. Gallery의 마지막 값은 126장을 전부 읽었을 때의 파일 payload 합계다.

| 공통 resource | 원본 bytes | 로컬 gzip level 9, bytes² |
| --- | ---: | ---: |
| `styles.css` | 25,732 | 6,462 |
| `entry.css` | 5,839 | 1,709 |
| `decor.css` | 7,933 | 2,273 |
| `script.js` | 21,058 | 6,955 |
| `minigame.js` | 5,626 | 2,313 |

² 동일 입력을 `gzip.compress(..., mtime=0)`으로 압축했다. GitHub Pages의 wire bytes를 측정한 수치가 아니다.

- Gallery JPEG는 정확히 **126개, 5,212,103 bytes**다. 전부 width 720이며 height는 270–1,276이다. HTML에 `loading="lazy"`는 126개, `width`/`height`는 0개다. 방문자가 실제 몇 장을 내려받는지는 아직 모른다.
- 두 index와 세 entry에도 image 요소 19개가 있고, 크기가 지정된 것은 **0개**다. 두 index의 image 16개는 모두 lazy 속성도 없다. 이 결함만으로 CLS가 얼마라고 말할 수는 없다.
- CSS의 comment와 `@import`를 제외한 balanced-brace inventory는 일반 rule block 265개와 keyframe block 20개를 찾았다. 같은 grouping context에서 selector와 declaration이 모두 같은 중복 block은 **0개**였다. `.screen`, `.no`, `.svc img`, `.manifesto`, `[data-r]`는 각각 두 번 선언되지만 대부분 속성을 덧붙인 것이다. 반복 selector를 전부 dead CSS로 세면 잘못된 리뷰다.
- 확실한 정리 후보는 사용처 없는 `.meter`/`.meter::before` 두 rule, 사용되지 않는 `--cut`, 그리고 anchor 지정 없이 남은 detector sprite branch다. 나머지 unused 비율은 browser coverage 전에는 주장하지 않는다.
- `validate_copy.py`: **38 checks PASS**. `validate_contrast.py`: **119 checks PASS**. 두 page generator의 `--check`: **변경 0**. 두 JS 파일: `node --check` 통과.
- `validate_content.py`: **3 checks 중 2 FAIL**, 옛 entry 경로 두 개가 없다. `validate_site.py`: **34 checks 중 14 FAIL**. 후자는 옛 `assets/css` 위치만 검사하고 untracked study page까지 섞으므로, 14개를 그대로 현재 사이트의 결함 수로 인용해서는 안 된다.
- `.github/workflows/gates.yml`은 **untracked**다. `git ls-tree -r HEAD .github` 결과가 비어 있다. 이 workflow가 현재 push를 막고 있다고 말할 근거가 없다. GitHub의 별도 branch rule이나 배포 설정은 확인하지 못했다.
- 파일을 바꾸지 않는 in-memory negative test에서 contrast checker는 `--t0`를 `--t3`와 같은 색으로 바꿔도 **119 checks PASS**였다. Kicker의 글자색을 배경색과 같게 바꾸면 검사가 두 개 줄어 **117 checks PASS**였다. Gallery builder의 `PAGE`를 존재하지 않는 경로로 바꿔도 `--check`는 **exit 0**이었다.

**우선순위**

| 순위 | 제안 | 결정 |
| ---: | --- | --- |
| 1 | 원본과 충돌하는 연구 수치 정정 | 첫 번째 |
| 2 | 현재 schema에 맞는 evidence gate | 두 번째 |
| 3 | 열어볼 수 있는 evidence packet | 세 번째 |
| 4 | 배포를 실제로 보호하는 gates | 진행 |
| 5 | 키보드와 navigation의 기본 동작 복구 | 진행 |
| 6 | Gallery를 실제로 필터링하고 나누기 | 진행 |
| 7 | Gallery provenance를 재현 가능한 자료로 | 진행 |
| 8 | Sound·motion을 사용자가 선택하게 | 진행 |
| 9 | 연구 문서의 의미 구조와 image 크기 | 진행 |
| 10 | English에서 연구 본문까지 이어지는 경로 | 진행 |
| 11 | 측정 후 runtime와 dead branch 정리 | 진행, 먼저 browser 기준선 확보 |
| 12 | Palette와 token의 단일 권위 복구 | design lead와 규칙 정합부터 |
| 13 | PASS·진척도·LIVE의 의미 명시 | 진행 |
| 14 | 또 한 번의 전면 visual rebuild | 거부 |
| 15 | RESONANCE를 실제 측정처럼 확장 | 거부, 현재 mode도 삭제 권고 |

**1 — 원본과 충돌하는 연구 수치 정정**

- **Why now:** [W/01](content/entries/w01-rb-cell-optics.json)은 standoff `1.7 mm`를 SOURCE_FACT로 싣는다. 원본 `~/Projects/opm-freecad-cli/configs/opm_sensor.yaml`의 header도 그렇게 쓰지만, 실제 `vapor_cell.position.x=5.75`, `size.x=7.5`이므로 glass 전면은 X=`2.0 mm`다. 같은 hash를 참조하는 `output/opm_sensor/build-report.json`의 `reference_cell.bbox.x_min`도 **2.0**이다. 차이는 **0.3 mm**다. Header의 다른 설명에는 **3.65 mm**까지 남아 있다. 여기서 새 실험값을 추정할 필요는 없다. 서로 다른 설명을 하나의 값처럼 출판한 것이 문제다.
- **What it changes:** W/01 JSON과 그것으로 생성되는 두 index·entry를 정정하고 correction record를 남긴다. 같은 대조에서 발견한 세 문제도 함께 처리한다: 본문의 beam 경로 `Y=±9`와 config의 `beam_offset_y=8.6`; D1을 pump·probe 겸용이라고 쓴 entry와 config `waveplate.targets`의 D1 circular/D2 linear intent; `93508a03…8cf79a`를 ‘해석된 설정 hash’라고 부른 문구. 이것은 raw config hash이며 resolved hash는 `47c10562…02a8`이다. W/03의 일반 `0.01 mm` tolerance도 원 보고서의 **volume tolerance 0.01 mm³**와 분리해 표기한다. 예상 1–2일, source owner의 의미 검토 포함.
- **What it costs:** 짧은 correction 기록만큼 HTML이 늘어난다. Front glass·cell centre·atomic volume의 기준을 구별해야 하며, CAD의 `2.0 mm`를 실제 장치의 측정 결과로 승격하면 안 된다. Source 저장소 자체의 낡은 주석 정정은 별도 작업 범위다.
- **How to know:** 고정된 source hash와 field 경로로 값을 읽고, 명시한 식으로 standoff를 계산해 card·본문·두 locale의 값과 비교한다. 다른 reference plane이면 반드시 이름과 근거를 기록한다. 현재 `1.7` 대 `2.0`, raw 대 resolved hash, mm 대 mm³ 사례를 각각 실패 fixture로 남긴다. 문자열 `1.7`이 존재하는지만 보는 검사는 정정을 오히려 막는다.

**2 — 현재 schema에 맞는 evidence gate**

- **Why now:** [CONTENT.md](CONTENT.md)는 `blocks` schema와 `content/index.json` 등록을 지시하지만, [build_entries.py](scripts/build_entries.py)의 `load()`는 최상위 JSON을 glob해서 `question/evidence/numbers/geometry/validation`을 읽는다. 옛 index에는 없는 두 파일이 남았고 현재 세 entry는 검사 대상조차 아니다. 현재 numbers **19개 중 CALCULATED 8개**에는 structured equation/inputs가 없으며, W/03 한 행만 note에 식과 입력을 직접 쓴다. Render 세 개와 validation row 13개에도 자체 evidence class가 없다. `badge('NOT_EVIDENCE')`는 오류 없이 badge를 만든다.
- **What it changes:** `validate_content.py`, `build_entries.py`, 현재 JSON 세 개, `CONTENT.md`, `content/index.json`, validator 안내를 하나의 schema에 맞춘다. 사용하지 않는 옛 index는 제거한다. Class enum, source ID와 locator, calculation equation/inputs 또는 명시적 geometry algorithm·input artifact, inference reasoning, render class를 필수화한다. Unknown field와 missing class는 실패시킨다. 과거 draft는 provenance 미검증 표시를 유지한다. 예상 2–3일.
- **What it costs:** Browser JS 증가는 없다. 대신 근거를 채우는 authoring 비용이 생긴다. 기존 CAD 계산값을 억지로 단순 수식에 끼워 맞추면 안 된다. 처음에는 현재 entry가 fail하는 것이 정상이며, 통과시키려고 전부 ILLUSTRATIVE로 바꾸는 것도 금지한다.
- **How to know:** 정상 entry가 통과하고, source 삭제·알 수 없는 class·단위 없는 calculation·class 없는 figure/data·중복 slug가 각각 실패한다. 새 entry 하나를 추가하면 두 index와 detail이 생성되고 같은 validator의 검사 수에 포함되어야 한다. Generator가 markup을 만들기 전에 validation을 실행한다.

**3 — 열어볼 수 있는 evidence packet**

- **Why now:** [build_entries.py](scripts/build_entries.py)의 artifact renderer는 `<code>` 경로만 출력한다. 세 entry의 artifact reference **13개는 고유 파일 10개**를 가리키며, 전부 이 기계에서 확인했다. 총 **1,125,839 bytes**다. OPM config **53,164 bytes**, build report **56,228 bytes**, STEP **819,078 bytes**와 W/03의 실제 FCStd·STEP·validation report·HTML report가 있다. W/03 FCStd의 전체 hash는 entry에 적힌 `185ca724…1139aa`와 일치한다. 자료 부족 때문에 링크를 못 단 상황이 아니다.
- **What it changes:** 두 source repo의 검토된 snapshot을 `assets/evidence/` 등의 versioned packet으로 출판하고 entry에 URL, 전체 SHA-256, source revision, 생성일, dirty 여부, 파일 형식·크기를 기록한다. `build_entries.py`는 실제 download/source link를 만든다. 큰 CAD는 클릭했을 때만 받는다. W/01·W/02의 `renders: []`도 그대로 드러내고, 그림을 넣을 때는 이 snapshot에서 검증한 view만 사용한다. 예상 1–2일, 공개본 내용 검토 별도.
- **What it costs:** 위 원본 그대로라면 저장·배포량 약 **1.13 MB** 추가, 첫 화면 자동 다운로드는 **0 bytes**가 목표다. Snapshot 업데이트와 URL 보존을 관리해야 한다. `git_dirty: true`인 build를 commit 하나만으로 완전 재현 가능하다고 표현할 수 없다. 기존 경로에 있다는 사실만으로 공개본을 자동 교체하지 않는다.
- **How to know:** 모든 공개 artifact link가 저장소에 실제 존재하고 bytes·hash가 manifest와 일치한다. Entry의 검증 행에서 원 보고서의 해당 field까지 도달할 수 있어야 한다. Browser network check에서는 클릭 전 STEP/FCStd request가 없어야 한다. 과거 packet URL은 새 entry revision 뒤에도 같은 bytes를 제공해야 한다.

**4 — 배포를 실제로 보호하는 gates**

- **Why now:** [gates.yml](.github/workflows/gates.yml)이 아직 untracked이고, 내용에도 현재 evidence 검사·gallery drift·browser interaction 검사가 없다. Link check는 `#fragment`를 버리고 CSS URL과 JSON artifact를 읽지 않는다. Contrast checker는 palette를 별도로 hardcode하며, foreground가 추정 background와 같으면 ‘decorative’로 간주해 건너뛴다. 이번 두 negative test는 최근 `4255b8f`의 “다시는 조용히 돌아오지 않는다”는 보장이 성립하지 않음을 보여준다.
- **What it changes:** Workflow를 추적하고 PR required check와 Pages publish dependency를 실제 repository 설정에 연결한다. 그 설정은 현재 확인되지 않았으므로 먼저 확인한다. 개선한 content·link·contrast·gallery check와 소수의 browser regression을 등록한다. `validate_structure.py`는 README에 이미 superseded로 명시됐으므로 옛 base 파일과 함께 retire하고 history로 보존한다. Pillow 및 browser 검사 환경의 version을 고정한다. 예상 2–3일, 이후 기능별 test는 해당 제안에 포함.
- **What it costs:** Page weight 변화는 없다. CI 실행 시간·dependency 업데이트 비용이 생긴다. 모든 commit에 heavyweight CAD 재생성을 넣을 필요는 없다. HTML generator의 일치는 사실성의 증명이 아니며, browser contrast check도 이미지·compositing의 모든 문제를 증명하지는 않는다.
- **How to know:** Broken fragment, invisible text, missing evidence, drifted generated page를 각각 넣은 PR이 실패하고 publish로 진행하지 않아야 한다. Untracked 로컬 파일이 없어도 clean checkout에서 같은 결과가 나야 한다. Gate가 실패를 잡는 시험도 gate에 넣는다. “검사를 실행했다”와 “배포가 검사에 종속된다”를 별도로 확인한다.

**5 — 키보드와 navigation의 기본 동작 복구**

- **Why now:** [script.js](script.js)의 menu Escape handler와 pad의 `Escape: 'b'`가 같은 keydown을 처리한다. `6958001`은 game Escape만 고쳤고 menu Escape는 여전히 history 이동까지 호출할 수 있다. Arrow key는 실제 button/link에 focus가 있어도 pad가 가로챈다. START는 desktop에서 `display:none`인 menu를 토글한다. 또한 `screenWipe.out()`에는 clear timer가 없는데 주석과 `226c2cc`는 navigation 실패에도 overlay가 제거된다고 주장한다. Source에서 확인한 동작이며 browser 재현은 미완료다.
- **What it changes:** `script.js`, index generator, locale labels와 필요한 control CSS를 수정한다. 기본 keyboard 탐색을 보존하고 pad shortcut은 focus가 pad에 있거나 사용자가 명시적으로 활성화한 범위로 한정한다. Escape는 현재 열린 UI만 닫고 focus를 돌려준다. Bare Escape/Backspace의 history binding과 실패 시 화면을 가리는 transition을 삭제하거나 명시적인 정리 경로로 교체한다. 예상 1–2일.
- **What it costs:** 코드량은 감소 가능하다. 익숙한 pad shortcut 일부는 조작 방식이 바뀐다. Device 모양을 유지하면서 실제 control의 label과 결과를 일치시키는 비용이 있다. 새 framework는 필요 없다.
- **How to know:** Desktop/mobile에서 menu 열기→Escape를 해도 URL·history index가 바뀌지 않고 focus가 opener로 돌아온다. Link·button의 Enter/Space와 arrow key가 기대 동작을 유지한다. START가 실제 보이는 menu를 연다. Navigation을 차단한 테스트에서도 overlay가 남지 않는다. Game Escape regression도 삭제 전까지 유지한다.

**6 — Gallery를 실제로 필터링하고 나누기**

- **Why now:** [build_gallery.py](scripts/build_gallery.py)는 filter에서 `c.hidden`만 바꾸고 author CSS는 `figure{display:flex}`를 강제한다. Author display가 hidden의 기본 표시 규칙을 덮는 구조다. 따라서 attribute만 검사해서 filter PASS를 선언할 수 없다. [gallery.html](gallery.html)에는 doctype·lang·charset·viewport가 없고 portfolio로 돌아가는 anchor가 **0개**다. 126장의 lazy 속성만으로 모바일 load가 적다고 보장할 수도 없다.
- **What it changes:** Generator에서 실제로 숨겨지는 card, 결과 count/status, 일관된 document shell과 돌아가기 link를 출력한다. Archive는 보존하되 한 page에 **12개**씩 내는 static pagination을 제안한다. 이는 새 목표값이다. Filter별 page와 전체 archive 경로를 제공하면 JS 없이도 쓸 수 있고 initial image 후보 수를 제한할 수 있다. 예상 1–2일.
- **What it costs:** Generator와 작은 HTML page 수가 늘어난다. 이미지 저장량은 그대로다. 첫 page에서 모든 항목을 browser Find로 찾는 기능은 줄어들므로 전체 metadata index는 별도로 유지해야 한다. 무한 scroll은 상태·history·접근성 비용 때문에 채택하지 않는다.
- **How to know:** Filter 후 attribute뿐 아니라 rendered box·accessibility tree·visible count를 확인한다. 모든 archive 항목이 중복·누락 없이 page link로 도달 가능해야 한다. 새 12개 page의 cold load에서 thumbnail request가 **12개 이하**인지 확인하고, filter/navigation 중 이전 page의 숨은 thumbnail을 추가로 받지 않는지 기록한다. 현재 126장 중 initial 다운로드 수는 이 검토에서 미측정이다.

**7 — Gallery provenance를 재현 가능한 자료로**

- **Why now:** “10 on the site”는 실제 page 참조가 아니라 `assets/*.png`와 ComfyUI output의 hash 비교 결과다. 현재 index는 `assets/gb/`를 쓰므로 그 10개 legacy asset은 현재 여섯 public page의 image slot에 쓰이지 않는다. Archive에는 model `unknown` **22개**, prompt 없는 record **52개**, size가 node reference 문자열로 출력된 record **23개**가 있다. `describe()`는 가장 긴 CLIP text를 positive prompt라고 **추측**한다. `--check`는 thumbnail 신설/삭제만 보며 HTML 부재조차 통과한다.
- **What it changes:** Local ComfyUI 수집과 public manifest→HTML 렌더를 분리한다. `assets/gallery/manifest.json`에 notes뿐 아니라 source hash·generator 종류·graph provenance·추출 실패 이유를 저장한다. Prompt polarity는 graph connection을 따라 판정하고 모르면 unknown으로 남긴다. Installed는 배포 대상 page/CSS의 실제 참조 graph에서 계산한다. `--check`는 committed manifest에서 만든 HTML과 비교하고 source 교체에 따른 stale thumbnail도 잡는다. 예상 2–3일.
- **What it costs:** Manifest 크기와 schema 유지 비용이 증가한다. Browser가 manifest를 자동 fetch할 필요는 없다. 현재 absolute `~/ComfyUI/output` 의존성을 CI에서 제거해야 한다. 원 PNG가 없는 항목의 provenance를 소급해서 만들어낼 수는 없다.
- **How to know:** Gallery HTML 삭제·caption 수정·manifest note 수정·동일 filename의 source 교체가 모두 drift로 검출된다. Unknown은 허용하되 근거 없는 model/positive prompt 추정은 금지한다. Node link가 size 문자열로 출력되지 않아야 한다. 같은 input snapshot을 두 번 렌더하면 timestamp 때문에 달라지지 않고 byte-identical해야 한다. Historical asset과 current slot을 방문자가 구별할 수 있어야 한다.

**8 — Sound·motion을 사용자가 선택하게**

- **Why now:** [script.js](script.js)의 저장값이 없을 때 sound는 기본 on이다. 첫 pointerdown/key/touch가 chime을 활성화하지만 최초 button은 `aria-pressed=false`로 보인다. Entry 세 page에도 같은 audio unlock이 설치되는데 `.snd` control은 없다. Reduced motion은 시작 시 한 번 읽으며, 실행 중 변경은 추적하지 않는다. Boot의 CSS 길이는 약 **2.57 s**, 이어지는 uncover는 **0.30 s**, out navigation에는 **0.32 s** 고정 지연이 있다. 이는 설정값에서 계산한 지연이지 실측 paint time이 아니다.
- **What it changes:** `script.js`, 두 generator, locale JSON에 명시적 sound opt-in과 motion 선택을 둔다. 첫 일반 click/Tab으로 소리를 켜지 않는다. Entry에도 audio가 존재한다면 끄는 수단이 있어야 한다. OS motion 변경을 실시간 반영하고 decorative canvas·ticker·sprite를 함께 중단한다. 필수 content를 보려는 사람에게 boot 지연을 부과하지 않는다. 예상 1–2일.
- **What it costs:** Preference 처리와 control label이 조금 늘어난다. 기본 load에서 audio context를 만들지 않으므로 초기 작업은 줄일 수 있다. 저장소가 막혀도 조작 가능해야 한다. 실측 없이 CPU·battery 절감률을 약속하지 않는다.
- **How to know:** Fresh storage에서 Tab·link click을 해도 AudioContext가 생성되지 않고 sound는 silent여야 한다. Explicit sound action만 켠다. 어느 page에서든 off 상태가 정확히 표시되고 유지된다. 실행 중 reduced-motion으로 바꾸면 decorative animation/RAF가 멈추고 내용이 즉시 읽혀야 한다. 저장소 예외 상황도 검사한다.

**9 — 연구 문서의 의미 구조와 image 크기**

- **Why now:** 두 index와 세 entry 모두 첫 하위 heading이 `h3`이며 section 이름은 `<p class="kicker">`다. Badge의 풀이는 `abbr title`에만 있다. 앞서 집계한 public page의 image **145개 전부** width/height가 없다. [styles.css](styles.css)는 JS 없이도 service image를 `clip-path:inset(0 0 100% 0)`로 숨기며 hero 위에는 `.screen::after`가 남는다. “JS 없이 즉시 page가 보인다”는 boot 설명이 artwork까지 보장하지는 않는다.
- **What it changes:** `build_index.py`, `build_entries.py`, `build_gallery.py`에서 section heading 순서를 바로잡고 evidence legend를 실제 text로 제공한다. Image dimensions는 asset에서 읽어 출력하고 loading 정책을 명시한다. Site rule의 lazy 요구를 바꾸려면 hero 예외의 근거를 design lead가 먼저 결정한다. Reveal은 JS 성공 후에만 숨김 상태를 활성화한다. Table은 기존 local overflow를 유지하면서 label과 keyboard 접근을 검증한다. 예상 1–2일.
- **What it costs:** Dimensions·legend만큼 소량의 HTML이 증가한다. 정상 motion 화면은 유지 가능하지만 잘못된 heading을 CSS로 다시 같은 크기로 꾸미는 작업이 필요하다. Image 크기 누락을 고쳤다는 이유만으로 CLS PASS를 선언하면 안 된다.
- **How to know:** 모든 image의 declared aspect ratio가 실제 asset과 맞는다. Heading navigation으로 각 연구 section에 도달하고, keyboard/touch로 class 의미를 읽을 수 있어야 한다. JS와 image 일부를 차단해도 본문·navigation·fallback artwork가 남는다. 390 CSS px와 200% zoom에서 page body가 옆으로 넘치지 않고 table만 내부 scroll해야 한다. CLS는 browser에서 별도로 기록한다.

**10 — English에서 연구 본문까지 이어지는 경로**

- **Why now:** `bf19a4c`의 English edition은 home과 card만 번역한다. 세 entry의 `en.question`은 이미 JSON에 있지만 public HTML 어디에도 출력되지 않는다. English OPEN 세 개는 모두 `lang="ko"` page로 연결되고 detail의 STAGE SELECT는 Korean index로 돌아간다. Link는 존재하지만 읽기 경로가 끊긴다. 최근 metadata 수정 `ab23ffd`도 index에만 적용돼 entry 세 개에는 canonical·OG 정보가 없다.
- **What it changes:** `build_entries.py`, locale content와 entry schema에 detail locale·translation 상태를 넣는다. 우선 이미 있는 English question을 사용하고 미번역 범위를 link에서 알린다. 이후 검토된 English 본문을 생성하되 수치·class·source reference는 공유한다. Detail에 locale을 유지하는 previous/next/back과 canonical·sharing metadata를 출력한다. 예상 plumbing 1–2일, 기술 번역 검토 2–3일.
- **What it costs:** Static HTML이 추가되며 home의 자동 page weight는 늘지 않는다. 기술 문장을 두 언어로 유지하는 비용이 크다. Korean fallback을 조용히 English라고 표시하는 방식은 금지한다. 번역 자동화만으로 physics 검토를 대체하지 않는다.
- **How to know:** English home→OPEN→next→back에서 locale이 유지된다. Translation이 없으면 클릭 전에 알 수 있어야 한다. 두 locale의 숫자·단위·evidence/source ID가 일치한다. 각 detail URL의 canonical이 자신을 가리키고, 실제 있는 번역에만 reciprocal alternate를 낸다. 공유 metadata 검사는 site root와 `/en/`, `/work/`의 상대경로를 모두 검사한다.

**11 — 측정 후 runtime와 dead branch 정리**

- **Why now:** Home은 index용 rule이 **496 bytes**뿐인 `entry.css` 전체 **5,839 bytes**를 가져온다. Entry도 shared JS **21,058 bytes**와 `decor.css` **7,933 bytes**를 읽는다. 다만 entry에서 rain/game loop가 실행된다는 뜻은 아니다. Selector guard가 있으므로 파일 크기와 runtime을 구별해야 한다. [decor.css](decor.css)의 detector overlay는 `--decor-detect-still` anchor 선언이 없어 fallback frame이 0이지만, `6f53aa9`는 detector animation까지 동작한다고 기록한다. 이 branch는 완성시키기보다 삭제할 가치가 높다.
- **What it changes:** 먼저 browser 측정 harness를 gates에 추가한다. 그 결과를 보고 index card rule을 공통 sheet로 옮겨 home의 entry stylesheet 요청을 제거하고, 사용처 없는 `.meter` 두 rule·`--cut`·미완성 detector overlay를 지운다. Shared JS는 실제 사용 기능 단위로 줄이되 fragment 파일을 무작정 늘리지는 않는다. Google Fonts `@import`의 request chain과 실제 subset bytes도 함께 측정한다. 예상 측정 1일, 작은 정리 1일.
- **What it costs:** Home에서 줄일 수 있는 CSS는 우선 대략 **5.3 kB raw와 stylesheet request 1개** 수준이다. Gzip 절감량은 재측정해야 한다. 전체 39,504 bytes CSS를 성급히 쪼개면 cache·request 복잡성이 더 커질 수 있다. Font나 shared selector는 한 viewport의 coverage만으로 삭제하지 않는다.
- **How to know:** 같은 Chromium version·기계·네트워크 조건에서 cache disabled로 desktop 1440×900/mobile 390×844를 각각 3회 측정한다. Cold 5초, 전체 scroll, menu/palette/keyboard, 다시 10초 idle을 구분해 request URL·encoded bytes·ScriptDuration·long task·CSS/JS coverage를 남긴다. Gallery는 initial/scroll/filter별 unique thumbnail 수를 기록한다. Reduced motion도 별도 실행한다. 삭제 이후 주요 동작이 같고 payload/request가 실제 감소해야 한다. Budget은 이 기준선을 얻은 다음 정하며, 현재 JS ms나 unused %를 만들어 쓰지 않는다.

**12 — Palette와 token의 단일 권위 복구**

- **Why now:** [AGENTS.md](AGENTS.md)는 `DESIGN.md`, `assets/css/tokens.css`, `assets/js/fid.js`를 design authority로 지정하지만 현재 세 파일이 없다. Raw font-size declaration은 `styles.css` **37개**, `entry.css` **27개**다. Palette는 styles, asset generator, contrast validator, game fallback에 각각 적혀 있다. `P`는 root attribute만 바꾸며 still `<img>` source는 mono에 남고 sprite만 DMG로 바뀐다. Source의 hover 조합으로 계산하면 `.svc li .no::after`는 dark ground에서 **약 1.71:1**인데 현재 contrast gate는 이를 light ground로 가정한다.
- **What it changes:** 먼저 design lead가 authoritative file 위치와 적용 규칙을 정합시킨다. 현재 규칙을 builder가 임의로 무시하거나 고쳐 쓰지 않는다. 그 결정 후 CSS·pixel generator·validator가 같은 palette/token definition을 읽도록 하고, still/sprite의 palette 전환도 하나의 mapping을 사용한다. `--focus`를 포함한 실제 focus contract를 복구한다. 예상 규칙 정리 반나절, 이관·검증 2–3일.
- **What it costs:** Design ownership 조정과 generator input 하나가 필요하다. Palette 색 자체를 바꾸는 제안은 아니다. 선언 이관 중 cascade·breakpoint가 바뀔 위험이 있으므로 시각 회귀 검사가 필요하다. Token 위반을 없애려고 기존 gate를 단순히 꺼서는 안 된다.
- **How to know:** 실제 shipped palette 변경이 validator 입력에도 반영되고 같은 색 foreground/background negative fixture는 반드시 실패한다. Root palette, PNG palette, still/sprite 대응이 모두 일치한다. Hover·focus·reduced-motion의 실제 computed color pair를 검사한다. 보호된 design 파일을 owner 결정 없이 수정하거나 우회한 변경은 받지 않는다.

**13 — PASS·진척도·LIVE의 의미 명시**

- **Why now:** [build_entries.py](scripts/build_entries.py)의 progress meter는 `round((number_count + check_count) / 2)`를 10칸에 채운다. W/01은 6칸, W/02는 4칸, W/03은 6칸이지만 세 JSON의 status는 모두 `complete`다. Item 하나를 덧붙이면 연구 진척 없이 meter가 오른다. Header STATUS도 연구 상태 대신 validation verdict를 사용한다. 두 hero의 `● LIVE`에는 연결된 measurement feed나 상태 판정이 없다.
- **What it changes:** 임의 progress bar와 근거 없는 LIVE label을 삭제한다. Generator와 locale JSON에서 연구 stage, 검증 scope, build date, unresolved issue를 분리해 표시한다. W/01·W/02는 geometry validation이며 optical performance는 미측정이라는 제한을 PASS 옆에 둔다. W/03은 infrastructure smoke test임을 첫 화면에 둔다. Number/check count는 유용하다면 순수 count로만 남긴다. 예상 반나절–1일.
- **What it costs:** Page weight와 CSS는 소폭 감소한다. 게임형 “completion” 연출을 잃지만 device interface의 layout을 바꿀 이유는 없다. 새로운 stage enum을 유지해야 하며 실제 확인되지 않은 ‘실험 완료’ 상태를 추가해서는 안 된다.
- **How to know:** Number나 explanatory check 한 행을 추가해도 stage가 변하지 않는다. 모든 PASS에는 무엇을 검증했는지와 근거 report가 연결된다. 미측정 성능과 unresolved 항목을 아래까지 scroll하지 않아도 알 수 있어야 한다. Live source가 없는 page에 LIVE가 생성되면 gate를 실패시킨다.

**14 — 또 한 번의 전면 visual rebuild: 거부**

- **Why now:** History에는 Speedy 방향, Webisoft 채택, 이미지 전면 재생성, original 8-bit rewrite, boot·sound·pad·sprite 추가가 연속해서 있다. 작업 트리에는 untracked `v2.*`, `v3.*`, `awwwards-study.*`도 있다. 이미 여러 디자인에 시간을 썼는데 현재 content validator는 실제 entry를 읽지 못하고 public artifact link는 없다. 다음 redesign을 정당화할 사용성 측정도 없다.
- **What it changes:** 채택한다면 모든 generator·CSS·JS·asset을 다시 건드리는 수일–수주 작업이다. **하지 않는다.** 기존 study를 public route로 올리는 것도 제안하지 않는다. Delete 여부는 review 대상인 untracked 사용자 작업을 함부로 지우지 말고 별도 보관 정책으로 정한다.
- **What it costs:** Weight 증가량은 구현 전 알 수 없다. 확실한 비용은 responsive·keyboard·locale·evidence presentation을 전부 다시 검증해야 한다는 점과 original handheld identity가 흔들리는 위험이다.
- **How to know:** 색·screenshot 선호가 아니라 연구자가 source와 검증 한계를 찾는 과제의 실패가 현재 layout 때문에 발생한다는 증거가 있어야 재검토할 수 있다. 지금은 그런 증거가 없으므로 이 제안의 acceptance decision은 REJECT다. 우선순위 1–13을 visual rewrite의 부수 작업으로 미루지 않는다.

**15 — RESONANCE를 실제 측정처럼 확장: 거부, 현재 mode도 삭제 권고**

- **Why now:** [minigame.js](minigame.js)는 `Math.random()`으로 target/noise를 만들고 `field/9`를 trace frequency로 쓴다. 단위·calibration·source·equation contract는 없고 화면에도 ILLUSTRATIVE가 없다. Dialog에는 focus 진입/복귀·trap·background inert·canvas text alternative·touch tuning button이 없다. Reduced-motion 검사도 없다. 현재 mode를 연구 demonstration이나 sensitivity display로 키우는 것은 “A RENDER IS NOT A SIMULATION”과 충돌한다.
- **What it changes:** Simulation처럼 보이는 추가 graph·score·측정 수치를 만들지 않는다. 현재 hidden mode도 삭제하는 편을 권한다: `minigame.js`, index generator의 두 script reference, `styles.css`의 `.game*` rule과 workflow의 해당 parse 대상 정리. 예상 반나절. 파일 삭제는 구현 시에만 하며 이번 review에서는 하지 않았다.
- **What it costs:** 현재 script를 제거하면 두 home에서 각각 **5,626 bytes raw / 로컬 gzip 2,313 bytes와 script request 1개**를 덜 요구한다. CSS도 조금 준다. Easter egg를 잃는 것이 비용이다. 실제 물리 simulation은 검증할 model·입력·단위·불확실성까지 별도 연구 작업이 필요하므로 간단한 frontend 추가로 견적 내지 않는다.
- **How to know:** 삭제 후 hidden key sequence가 modal이나 새 animation을 만들지 않고 keyboard navigation regression이 통과해야 한다. 원래 code는 git history로 남는다. 향후 설명용 모델을 제안하려면 ILLUSTRATIVE/CALCULATED 구분, 방정식·입력·source·실험과의 차이, accessible static explanation을 먼저 검토해야 한다. 그 조건 없는 확장은 REJECT다.

**먼저 할 세 가지**

**1 → 2 → 3** 순서로 진행한다. 틀린 숫자를 먼저 정정하고, 다음 entry에서 같은 실수를 막는 현재 schema gate를 만들고, 이미 존재하는 원본을 방문자가 열 수 있게 한다. 세 작업이 끝나면 이 사이트의 “RECORDED TO BE CHECKED”를 연구자가 직접 시험할 수 있다. 이후 4번으로 그 결과가 실제 배포 조건이 되게 한다.

거부하는 두 가지는 **14번의 전면 visual rebuild**와 **15번의 측정처럼 보이는 game 확장**이다. 둘 다 지금 확인된 근거 접근·정합·사용성 결함을 해결하지 않으며, 검증할 표면만 늘린다.

**원본 대조의 재확인 지점**

- `~/Projects/opm-freecad-cli/configs/opm_sensor.yaml`: lines 29–40의 옛 standoff 설명, lines 121–132의 다른 설명과 실제 size/position, lines 179–206의 wavelength·beam offset·waveplate intent.
- 같은 repo의 `output/opm_sensor/build-report.json`: `config_sha256`, `resolved_config_sha256`, `git_dirty`, `parts[name=reference_cell].bbox.x_min`, 각 part의 `checks`. 실제 집계는 part 25개·check 175개이며 warnings/errors/interferences는 모두 0이다. 이 CAD 검사 결과 자체를 가짜라고 판정한 것이 아니다.
- `~/orca/projects/research-agent/validation/final/smoketest.json`: `scope`, `supervisor_independent_checks.remeasured_off_saved_model`, `tolerance_mm3`. 연결된 FCStd와 report도 존재한다.
- Negative test는 `Path.read_text` 또는 generator의 `PAGE` binding을 memory에서만 바꾸어 수행했다. Repo 파일을 변형한 후 되돌리는 방식은 사용하지 않았다. Generator 실행도 page/artifact를 쓰는 일반 mode 대신 `--check`로 제한했다. 전체 asset generator의 파일 재생성 검사는 이번에는 실행하지 않았다.
