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
아래는 **말할 나레이션**입니다 (화면을 말로 설명하도록 씀). 조작은 화면 흐름에 맞춰 진행.
소제목 〈 〉은 지금 어느 화면인지 표시용.

**〈화면 소개 — 시작〉** *(앱 화면으로 전환하면서)*
> "This is **NeoVUS**, live right now at **neovus dot streamlit dot app** — open to anyone, no login. On the **left** I enter a single variant; the whole interpretation appears here on the **right**."

**〈입력〉**
> "So — on the left, I enter the variant **exactly as it's written on the report** — KCNQ2, c-dot seven-fifteen, G-to-A — and the baby's phenotypes."

**〈상단: 분류·게이지·점수〉**
> "At the top, NeoVUS shows the classification. ClinVar calls this one **uncertain** — a VUS — and that's the clinician's problem. But just below, this **gauge** — a transparent vote over REVEL, AlphaMissense, and CADD — the needle **leans pathogenic**. And these bars show each score against its threshold. **Note — NeoVUS isn't classifying the variant for me; it shows what the evidence says, transparently, and I decide.**"

**〈단백질 그림〉**
> "This is the protein. The blocks are its functional domains, and the **red pin is our variant — residue 239 — sitting right in the S5 transmembrane segment**."

**〈후보 질병·근거 링크〉**
> "Below are the candidate diseases, ranked by how well the phenotypes match — KCNQ2 encephalopathy at a hundred percent. And notice — **every statement has a link**. I click one, and it opens the actual ClinVar record. **Nothing here is a black box — zero unsupported claims.**"

**〈신생아 체크리스트〉**
> "On the right is the neonatal checklist — not just symptoms, but **cited work-up and follow-up**: EEG, brain MRI, gene-specific drug safety."

**〈리포트 다운로드〉**
> "And the whole thing downloads as a **one-page report** for the chart."

**〈침상 표현형 체크 — 하이라이트〉**
> "Finally, the bedside part. I **tick the phenotypes the baby actually has** — and watch: each candidate disease's match **updates live**. No genetics training needed."

### ③ 검증 + 어떻게 만들었나 + 마무리 — 슬라이드 2·3·4 · ~0:50

**〈검증 — 슬라이드 2〉**
> "Is it trustworthy? On ClinVar variants **reclassified across the VUS boundary**, NeoVUS's evidence agreed with the eventual reclassification **84.8% of the time, at 100% precision** for pathogenic calls."

**〈어떻게 만들었나 — 슬라이드 3〉** *(화면이 구성도를 보여줌 — 말은 간단히)*
> "And it was built **entirely with Claude, this week.** **Claude Code** wrote the whole tool, pipeline, and validation on open public data — with one rule: **every claim carries its source**. And **Claude Science** curated what no single database has: the reclassification benchmark, and cited checklists for **eighteen** neonatal genes."

**〈마무리 — 슬라이드 4〉**
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
