# NeoVUS 데모 영상 — 제작 가이드 + 대본

목표: **3분 이내**(하드캡, ~2:30 권장). **3구간**으로 반디캠 녹화 → Clipchamp로 이어붙이기 →
YouTube(Unlisted) 업로드 → CV 플랫폼에 링크 제출.

---

## 0. 녹화 전 체크리스트

- [ ] 앱 **공개 상태 확인**: 시크릿(incognito) 창에서 https://neovus.streamlit.app 이 로그인 없이 열리는지 확인.
- [ ] 브라우저 정리: 북마크바·확장 숨기기, 다른 탭 닫기, 알림 끄기(방해금지).
- [ ] 두 가지 준비:
  - **탭 A** — 앱 (neovus.streamlit.app)
  - **슬라이드** — `C:\Users\Public\neovus_slides.html` 열고 **F11**(전체화면), 방향키 ← → 로 이동
- [ ] 앱 글자를 영상에서 읽히게 확대 (`Ctrl` + `+`).
- [ ] 앱 흐름을 리허설 1회.

## 1. 반디캠 설정

- 모드: **화면 녹화(Screen Recording)** → **전체화면**(브라우저 F11 상태).
- **형식:** 1920×1080, 30fps, MP4(H.264).
- **소리:** 마이크 ON(나레이션), 시스템 소리는 선택.
- **웹캠(선택):** 구석에 작은 얼굴 오버레이 — 인트로에 신뢰감↑.

## 2. 3구간으로 나눠 녹화

각 구간을 따로 녹화하고, 틀린 구간만 다시 찍으세요. 찍기 쉬운 순서: **② → ① → ③**.
(*아래 인용문(">")만 영어로 읽는 나레이션입니다.*)

### ① 인트로 — 슬라이드 1(제목) · ~0:15
화면: 제목 슬라이드 (웹캠 얼굴 선택)
> "I'm a neonatologist. When a newborn's genomic report comes back with a **variant of uncertain significance**, there's no bedside tool to interpret it. So I built **NeoVUS** with Claude."

### ② 프로그램 사용 — 앱 탭 · ~1:35
화면: neovus.streamlit.app (라이브)

**〈입력〉** *[gene `KCNQ2`, variant `c.715G>A`, HPO `HP:0001250, HP:0010851` 입력 → Interpret 클릭]*
> "I enter the variant **exactly as it's written on the report** — KCNQ2, c.715G>A — plus the baby's phenotypes."

**〈판정·단백질〉** *[상단 배지(주황 Uncertain)·게이지 → 단백질 그림으로 스크롤, 커서로 S5 짚기]*
> "This one is a **VUS** — ClinVar reports it as **uncertain**. That's exactly the clinician's problem. But NeoVUS's own **evidence gauge**, a transparent vote over REVEL, AlphaMissense, and CADD, **leans pathogenic**. The protein view shows where it lands: **residue 239, in the S5 transmembrane segment**."

**〈침상 표현형 체크〉** *[표현형 2~3개 체크 → 질병별 매치 바 변하는 것 보여주기]*
> "Candidate diseases are ranked by phenotype match. And here's the bedside part — I **tick the phenotypes the baby actually has**, and each disease's match updates live. No genetics training needed."

**〈근거·다운로드〉** *[출처 링크 하나 클릭(새 탭 잠깐) → 돌아와 다운로드 버튼]*
> "The checklist gives cited **work-up and follow-up** — EEG, MRI, gene-specific drug safety. And the whole point: **every claim links to its source. Zero unsupported claims — not a black box.** One click downloads the report for the chart."

### ③ 검증 + 마무리 — 슬라이드 2·3 · ~0:40
화면: 검증 슬라이드 → 마무리 슬라이드
> "Is it trustworthy? On ClinVar variants **reclassified across the VUS boundary**, NeoVUS's evidence agreed with the eventual reclassification **84.8% of the time, at 100% precision** for pathogenic calls. The benchmark and checklists were curated with **Claude Science**; the tool, pipeline, and validation were built with **Claude Code**."
>
> "NeoVUS is **open-source**, runs on **open public data**, and is **live right now** — the neonatal VUS tool I wished I had at the bedside. Thank you."

*~2:00로 더 줄이려면 ②의 〈판정·단백질〉과 〈근거·다운로드〉에서 한 문장씩 빼면 됩니다.*

## 3. 구간 이어붙이기(편집)

- **Clipchamp**(Windows 11 기본 내장, 무료): 클립 ①②③을 타임라인에 순서대로 끌어놓기 → 하드컷으로 충분 → **Export** 1080p MP4.
- 대안: **Bandicut**(반디캠 같은 회사)로 MP4 join.
- 세 구간 **마이크 볼륨·해상도(1080p) 동일**하게 유지.

## 4. 업로드 + 제출

1. 완성 MP4를 **YouTube → 공개범위: 미등록(Unlisted)** 로 업로드 (링크로만 열람, 검색 노출 X).
2. YouTube 링크 복사.
3. **https://cerebralvalley.ai/e/built-with-claude-life-sciences/hackathon/submit** 에서 제출:
   - **Demo video:** YouTube 링크
   - **Repo:** https://github.com/moonicu/neovus
   - **Summary:** `docs/SUBMISSION.md` 의 190단어 요약
   - 마감: **7/13 9:00 PM ET = 7/14 오전 10:00 KST**
