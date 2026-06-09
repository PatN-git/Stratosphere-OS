# Evidence Standards for Research Artifacts

These standards ensure all research remains high-integrity, verifiable, and free from hallucinated or speculative claims. They apply to all research domains (Competitive and Problem-Space) and depth modes.

---

## Source Requirements

- **Domain-Specific Source Types:**
  - **Competitive Domain:** Rely on official documentation, official pricing sheets, verified customer reviews (e.g., G2, Capterra), and official press releases.
  - **Problem-Space Domain:** Rely on peer-reviewed academic papers, reputable industry/analyst reports (e.g., Gartner, Forrester), active GitHub repositories (source code, issues, discussion threads), and general literature or documentation of technologies.
- **Explicit Citations (Per-Claim Criticality):** Every published claim regarding competitor capabilities, pricing, user pain points, technological approaches, or trends must be explicitly cited:
  `[Claim] (Source: [URL/Citation], accessed [YYYY-MM-DD])`
  **No uncited assertions are allowed under any circumstances.**
- **Source Independence:** Collapse sources that share a common origin. Only count distinct, primary origins of information:
  - Three different tech blogs all quoting the same single press release count as only **one** source.
  - Multiple news articles referencing the same original benchmark report count as only **one** source.
- **Decision-Driving / Load-Bearing Claims:**
  - **Definition:** A claim that, if wrong, would change the research conclusion or the recommended next step.
  - **Triangulation Rule:** Regardless of Quick vs. Deep depth mode, any decision-driving/load-bearing claim OR `[HIGH]` confidence claim **requires at least two independent, different-type sources** (e.g., official docs + GitHub issue, or academic paper + industry report) after collapsing common origins. Single-sourced load-bearing claims are strictly prohibited.

---

## Confidence Scoring

All feature, market, and technological claims must be annotated with one of the following levels:

- **`[HIGH]` Confidence:** Corroborated by at least **two independent, different-type** sources after collapsing common origins, AND has survived a skeptical refutation pass.
  - **Mandatory Pre-Publish Check:** Before labeling any claim `[HIGH]`, list its two supporting sources AND each source's type (academic | industry | doc | repo | blog | review | press). If the two sources share the same type (or the same origin after collapsing), the claim does NOT qualify as `[HIGH]` — downgrade it to `[MEDIUM]`.
  - *Note:* Quick Search mode cannot publish single-sourced `[HIGH]` confidence claims. In Quick Search mode, only load-bearing claims undergo refutation; therefore a non-load-bearing claim in Quick mode cannot be `[HIGH]` — it tops out at `[MEDIUM]`.
- **`[MEDIUM]` Confidence:** Supported by a single highly credible source (e.g., official marketing page, main developer documentation, or a detailed industry report).
- **`[LOW]` Confidence:** Inferred from context, derived from a single subjective source (e.g., a forum/Reddit post), or extrapolated from old documents.

---

## Handling Unknowns

If information is missing or unverified, do not attempt to guess or infer it. Mark it explicitly:
- Use `[Not publicly available]` if information cannot be found via open searches.
- Use `[Requires product trial]` if accessing the information requires signing up for an enterprise account, active payment, or a custom sales demo.
- Suggest explicit follow-up steps (e.g., "Run a trial account using secondary email to verify feature X").

---

## Strictly Prohibited

- **Fabrication:** Never fabricate competitor features, pricing figures, active integrations, user counts, client lists, or quotes.
- **Over-Generalization:** Do not assume a competitor lacks a feature simply because it is not listed on their homepage. Check documentation or search forums first, or mark as `[LOW]` or `[Unknown]`.

---

## Core Focus

- **Focus on the "Why":** Standard feature checklists are insufficient. Research must focus on **why** users choose a competitor (their motivations, frustrations, workflows, and core value realized) or **why** a technological trend is emerging.
- **Dunford Alignment:** Structure competitive analysis to feed directly into the Dunford Positioning Lens, identifying unique attributes and market category positioning.
