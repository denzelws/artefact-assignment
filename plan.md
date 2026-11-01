# Emporio da Musica — Agent Plan (Reference)

## 1. Requirement summary
- Text-message agent for Emporio da Musica (Campo Grande/MS), assisting the store team.
- Portuguese persona; English code, README, commits, and submission artifacts.
- Python only. CLI interface. Ollama (`llama3.1:8b`) default; OpenAI-compatible provider opt-in.
- Deliverables: public GitHub repo with incremental history, English README, 3–5 sample
  conversations (one non-trivial), submission PDF via Google Forms + email reply.
- Deadline: Tuesday Nov 3, 2026, 23:59 BRT. Repo frozen before submission.
- Git: user runs every `git` command; no automatic commits; no AI co-author trailers.

## 2. Data inventory (`data/`, provided files — do not rename)
- `desafio_tecnico_ai_eng - products.csv`: product_id, price_brl, name, category_id,
  description, stock_quantity, status (active/discontinued/coming_soon), specs (JSON), created_at.
- `desafio_tecnico_ai_eng - categories.csv`: 9 categories (violoes = 5, ukuleles = 9).
- `desafio_tecnico_ai_eng - orders.csv`: 20 orders
  (delivered/shipped/confirmed/pending/cancelled). Tracking + ETA only on shipped/delivered.
- `desafio_tecnico_ai_eng - order_items.csv`: order <-> product links (orders 15 and 20 have 2 items).
- `desafio_tecnico_ai_eng - customers.csv`: 50 customers.
- `desafio_tecnico_ai_eng - promotions.csv`: 25 promos, 4 active (ids 12, 14, 19, 24).
- `políticas_da_loja.pdf`: 8-page manual, pasted into chat. Key sections: store data (1.2),
  hours (2), payments (3), returns (4), shipping (5), promos (6), WhatsApp service (7),
  warranty (8), privacy/LGPD (9).

## 3. Architecture
- Single Python package, one process, no extra services. Model calls typed tools; never raw SQL.
- `src/emporio/`: `cli.py`, `config.py`, `agent/` (loop, PT system prompt), `llm/` (ChatModel
  protocol + Ollama/OpenAI clients), `tools/` (one module per tool, pydantic args),
  `data/` (CSV -> SQLite loader, policy sections).
- SQLite loaded from CSVs at startup. Policy manual stored as ~10 titled sections.
- CLI REPL with JSONL session log (source for `examples/` transcripts).
- Tests: pytest; repositories, tools, agent loop with fake model. No live keys in tests.

## 4. Tools
- `search_products` (text/category/max_price/in-stock), `get_product`,
  `get_order_status` (tracking/ETA only when present), `get_promotions` (active only),
  `search_policies` (keyword rank over sections, falls back to section index),
  `get_store_info` (address, hours, phones, email).
- Edge cases: zero stock (prod 96), discontinued (113), coming_soon (130), cancelled orders,
  inactive promos, PIX discount never stacked on promo prices.

## 5. Persona (manual section 7)
- Informal but professional, "friend who understands music"; greet by name when known.
- Flow: greet -> understand -> consult system -> answer with prices/terms -> close.
- Never state price/stock/deadline without a tool call. Instruments only; accessories
  (strings, picks, cables, pedals, amps, cases) get a polite redirect.
- Out-of-stock -> suggest alternatives; expired promo -> transparent current price;
  complaints -> empathy + escalate, 24-business-hour callback.

## 6. Known data assumptions (to document in README)
- Phones: header `(67) 3341-4444` vs WhatsApp `(67) 3321-4500` in section 7 — agent quotes both
  with labels. Email table contains accented `contato@empóriodamusica.com.br` (invalid) —
  agent uses `contato@emporiodamusica.com.br`.
- Tracking format `BR` + 9 alphanumerics + `BR` matches CSV codes.

## 7. Editor standard (`.vscode/settings.json`)
- Dracula, JetBrains Mono + ligatures, size 12, ruler 120, Ruff format-on-save +
  organize imports, `src` layout, exclusions: `.venv`, `__pycache__`, `.pytest_cache`,
  `.ruff_cache`, `dist`. (Prettier/ESLint/`@/*` do not apply to this Python repo.)

## 8. Build phases (one atomic commit each, run by the user)
1. `feat(config): env settings + provider switch`
2. `feat(llm): ChatModel protocol + Ollama/OpenAI clients`
3. `feat(data): CSVs -> SQLite`
4. `feat(data): policy sections + store info`
5. `feat(tools): store tools`
6. `feat(agent): PT persona loop`
7. `feat(cli): REPL + JSONL log`
8. `test`: pytest suite
9. `docs`: README + 4 samples (violoes <= R$1000; Takamine GD20 price; regret/return case;
   out-of-scope redirect) + submission PDF + freeze

## 9. Submission
- English PDF named `<Full Name> - AI Engineer – Full-Stack para Aplicações com IA Generativa.pdf`
  with summary, decisions, limitations, repo link, run instructions.
- Submit via Google Form; reply to Tatielle's email with the same link + PDF.

## 10. UX edge-case audit (added after Phase 4, Oct 31 2026)
- How we got here: after building the data layer, we re-read the manual against the
  implementation and asked "what can a real customer type that breaks the happy path?".
  A 15-query torture test (`DEVOLUÇÃO!!!`, `frete gratis p campo grande`,
  `qero divolber um produt com deffeito`) proved the policy search holds for realistic
  messiness (accents/case/punctuation/stopwords) and degrades to the section index on
  garbage. Total garbage never resolves — that is by design: the LLM layer (Phase 6)
  maps messy text to clean tool arguments before search ever sees it. The cases below
  are the ones normalization alone cannot solve; each names where it lands.
- Order-status UX (tool semantics, Phase 5):
  - No tracking yet (pending/confirmed have NULL code/ETA) — tool returns an explicit
    "not shipped" state with what happens next, so the model never invents a code.
  - Cancelled order — empathy + replacement offer, not just the status word; response
    includes all items (orders 15/20 have 2) and the customer name (JOIN to customers
    enables "Olá, Lucas…" instead of a cold dump).
- Product UX (structural, Phase 5 tools + Phase 6 prompt):
  - Out-of-stock MUST suggest same-category in-stock alternatives (manual 7.3). Tool
    results carry `status` + `stock_quantity` so the agent can branch.
  - Three distinct "unavailable" messages: out-of-stock (temporarily indisponível +
    alternatives), discontinued (fora do catálogo + successors), coming_soon (ainda não
    lançado — never "sem estoque").
  - Accessories (strings, picks, cables, pedals, amps, cases) are a redirect path,
    distinguishable from "instrumento esgotado" — the prompt carries the literal list.
- Money UX (model arithmetic + rules, Phase 6 prompt; one tool flag, Phase 5):
  - Installment minima enforced before offering: 12x needs R$100/parcela, so a R$500
    item cannot go 12x. Prompt carries the 3x/6x/12x table.
  - Promotion results flag `pix_eligible` — the 5% PIX never applies on promo prices,
    and a boolean keeps the model from computing the most expensive mistake.
  - Freight: metro rule quoted exactly (grátis > R$500, else R$35); out-of-area gets
    method + range only, never a fabricated number.
- Clock confusion (Phase 6 prompt): 7 (online regret) vs 30 (defect) vs 90 (legal
  warranty) days — the model must qualify the situation (online? defect? how long ago?)
  before quoting a number; search ranking already verified for these sections.
- Escalation (prompt scripts, no tools by design): complaints -> empathy + 24h callback
  promise; LGPD deletion requests -> acknowledge + route. Neither is tool-solvable, so
  the prompt must prevent the model from improvising a resolution.
- Process note: pytest suite started early (Phase 4.5, `tests/` for llm/data/policies,
  29 tests) instead of waiting for Phase 8 — scratch `/tmp` smoke scripts graduate into
  `tests/test_*.py` from now on; Phase 8 extends the suite (tools, agent loop).
- Incident #1 (kept for README): first live turn hallucinated. Asked "quais violões até
  R$ 1000", the model correctly called `search_products` but got `[]` and invented
  Yamaha/Taylor/Fender listings. Diagnosis via history X-ray (`/tmp/diag_agent.py`):
  the model echoed `query: "violões"` (plural) while descriptions say "violão"
  (singular) — substring match failed on every row. Fix: 10-line PT `stem()`
  (`violoes->violao`, `trocas->troca`, short words untouched) applied to product
  search and policy ranking, with regression tests pinning the exact model call.
  Re-run quoted 8 real violões at real prices. Lesson recorded: empty tool results
  push small models to invent, so recall robustness IS hallucination prevention.
- Incident #2 (same session): the model's natural query `query="violões até R$ 1000"`
  still returned `[]` AFTER the stem fix. Cause: every token was required, and residue
  tokens (`até`, `R$`->`r`, `1000`) appear in no description — prices belong to
  `max_price`, not to text. Fix: shared `data/text.py`
  (`normalize`/`stem`/`STOPWORDS`/`query_tokens`/`word_set`) used by both product search
  and policy ranking; `query_tokens` drops stopwords, single letters and pure numbers.
  Regression test pins the exact model query. Same session added a prompt rule from live
  observation ("viiol" typo on llama3.2:3b): copy names/prices/codes verbatim, never
  rewrite. Verification: qwen2.5:7b answered with 5 real violões, real prices and correct
  PIX math (R$429,90 -> R$408,40); residual prose wobble on 3b is capacity, not code.
- Incident #3 (user re-run caught it): `category="violão"` (singular, the natural word)
  returned 0 rows while `"violões"` returned 14 — category matching never got the stem.
  Same fix shape as #1/#2 (stem both sides of the name comparison). Pattern recorded:
  the model varies wording run to run, so EVERY text comparison in the tools must be
  number/accent/case-proof, not just the query field.
- Incident #4 (user's own MY_QUESTIONS case): "a loja vende oq?" -> 3b answered the store
  ALSO sells accessories (cordas, palhetas, cabos...) — a confident inversion of manual
  §1, answered from pretraining without calling any tool. Qwen-7b also failed ("diversos
  acessórios"), so NOT 3b-only: rules alone don't beat prior when no tool is consulted.
  Fix: few-shot example inside ESCOPO (model customer "vocês vendem cordas?" + redirect
  to imitate) instead of another rule. Verified on 3b: accessories gone. Lesson: for
  scope/safety behavior, examples beat instructions. Prime Phase 9 non-trivial sample.
- Incident #5 (same re-run): "pedido 8" said not-found while the X-ray proves the road
  is perfect (`get_order_status {order_id: 8}` -> found/shipped/all facts). Pure 3b
  messenger flakiness: identical question, some runs call the tool, some ask for
  clarification instead. Not fixable in code; the loop is correct and bigger models are
  consistent. Distinguish from recall bugs: flakiness varies run to run, recall fails
  deterministically.
- Full-fabrication event (live CLI, 3b): "violões até R$1000" returned generic invented
  products ("Violão Acústico R$249,90" — nothing in the catalog) plus an invented R$500
  cap. X-ray minutes later on the identical question: correct tool call, 14 real results,
  grounded answer. Verdict: incident-#5 class (no-call flakiness), not a new recall bug —
  no code changed. Open hypothesis (unproven): prompt growth (~30→60 lines across tonight's
  fixes) competes with tool schemas for 3b attention; candidate Phase 8/9 work is a prompt
  condense pass keeping all rules. Graded runs stay on 7b+.
- Typo probe (live CLI, deliberate "desconto no pi?"): understanding 10/10 — "pi" resolved
  to PIX, correctly scoped to the Woodstock thread. But the answer repeated incident #6
  (no 5% stated) and added a scope regression: offered "acessórios" as alternatives, a
  context the incident-#4 few-shot doesn't cover. Fix: ESCOPO now bans offering
  accessories as alternatives/suggestions too, not just listing them as products.
- Incident #6 (PIX, closed): 3b is 0-for-4 with four DISTINCT wrong variants (denial,
  promo-listing dodge, and finally the inverted rule "PIX apenas para produtos COM
  desconto" — backwards and dangerous). A PIX few-shot (same treatment that fixed #4)
  did not help. Qwen states the rule correctly every time. Verdict: conditional rules
  (X unless Y) exceed 3b reliability — unsolvable by prompt on small models, solvable
  by capacity. The architecture already contains the answer: `pix_eligible`/`pix_price`
  are computed in tools, so per-product PIX numbers are always correct; only the
  general-rule statement needs model capacity.
  Re-probe Nov 1 at temperature=0.2: 1/3 correct, 2/3 denial variant — notable: the tool
  (`get_promotions`) was called 3/3, only the prose conclusion flips. Temperature fixed
  tool-call consistency, not conditional reasoning. Verdict STANDS: graded runs on 7b.
- Incident #7 (live CLI): user said just "Tagima" (2 matches: Memphis, Dallas Tuner) and
  the model detailed one silently instead of listing both + asking. Road delivered both;
  messenger chose without asking. Fix: prompt rule in the flow (vague query -> shortlist
  with prices -> ask before detailing). User's preferred UX confirmed: both + select.
- Incident #8 (live CLI): follow-up "Tagima" after "violões até R$1000" listed ALL Tagimas
  (up to R$1349), dropping the established budget. Tools are stateless by design; carrying
  conversation filters is the messenger's job. Fix: prompt rule (refinements inherit prior
  filters unless changed). VERIFIED live Oct 31: follow-up "Tagima" returned 4/4 in-budget
  Tagimas (R$429–R$999, no R$1199/R$1349) + asked which — both halves of follow-up behavior
  now hold (#7 ask-when-vague, #8 remember-when-refining).
- Human QA verdicts (user-run `scripts/live_qa.py`): troca consistently correct
  (WhatsApp, 7/30/90 clocks); pedido 8 correct whenever the tool is called; violões
  10/10 real post-fixes (minus one listed-discontinued, fixed by prompt). Bottom line
  for the README: no invented products, prices or tracking codes in any grounded turn —
  tool grounding holds, prose wobble is model size.
- Model benchmarking (early numbers for the README performance section, Oct 31 2026,
  user's machine): qwen2.5:7b cold load takes minutes (5.1 GB resident, 100% CPU while
  inferring, 4K context, 4-min Ollama keep-alive — warm runs within the window are fast);
  per-turn latency several times llama3.2:3b. Quality ranking from live QA: qwen holds
  PIX rule + scope + grounding; 3b needs prompt scaffolding and still drops conditionals.
  Plan default llama3.1:8b not yet measured locally. Demo tip: pre-warm with
  `ollama run <model>` before presenting.
- Decision (trade-off, kept for README): single model per deployment, NO per-question
  routing. Considered a cascade (3b default, escalate conditional-rule questions to 7b)
  and rejected: two resident models cost more RAM/VRAM than one 7b; the router becomes a
  new failure point to debug 3 days before the deadline; and the evidence shows 7b
  handles every category while 3b fumbles across them. Flexibility lives in one env var
  (`EMPORIO_OLLAMA_MODEL`), and per-product PIX numbers are model-proof anyway (computed
  in tools). Revisit only with latency/cost telemetry demanding it.
- Guiding principle (earned from incidents #1–#6): the agent is a messenger, not the
  truth. Truth lives in SQLite rows + 10 policy sections; tools are the only road
  between truth and messenger; the model supplies tone and flow. Every wrong answer is
  diagnosed with one question — "road or messenger?" — via the history X-ray: empty or
  wrong tool results mean road repair (with regression tests); correct results with bad
  prose mean messenger training (few-shot examples beat rules); run-varying failures
  with a proven road mean model capacity (bigger model). This layering is the
  README spine and the reason small-model prose wobble never corrupts facts.
- Temperature fix (Oct 31, closes the incident-#5 class on the common case): run-varying
  no-call flakiness on llama3.2:3b ("quais violões vocês têm?" answered directly, no tool,
  ~1 in 3 runs) was sampling noise, not prompt wording — default temperature=1.0 lets a
  weak "always call a tool" intent flip run to run on 3b. Fix: new `temperature` setting
  (`LLM_TEMPERATURE`, default 0.2; Ollama `options.temperature`, OpenAI `temperature=`),
  tests on both clients + factory passthrough. Verification: same question on 3b → tool
  called 3/3 (was ~2/3). Suite: 54 passed. Lesson (README-worthy): set determinism knobs
  BEFORE judging a small model — sampling noise < model size.
- CLI observability gap (Nov 1, from live QA): `sessions.jsonl` logged only user/assistant
  text, so a Tagima turn ("sorry, none found" + 2-of-6 list) couldn't be X-rayed — the
  road's actual output was unknown. Fix: `Agent.last_tool_calls` (reset per turn) now
  flows into each JSONL record under `"tools"` (suite: 56). Lesson: log the road, not
  just the conversation — undiagnosable turns are a logging bug, not a model mystery.
  First X-ray (Nov 1): reproduced "violões → Tagima" on 3b via piped CLI; log shows
  `search_products {category: violoes, query: Tagima}` → 6 results, all 6 listed. Road
  innocent twice over — the user's earlier 2-of-6 + "sorry, none found" was run-varying
  messenger wobble (incident-#5 family: apology text generated before reading results),
  not a recall bug. No code changed.
- Red-team win (Nov 1, user's freestyle): "Memph" (invented brand) → qwen never called a tool
  and hallucinated entire product lines (Memph/Memphis VJ-200/300/400, Tagima VJ-100...), with
  invented prices AND model arithmetic — plus a Chinese pretraining leak mid-confusion. Same
  disease as #7: no tool call on ill-formed queries. Fix: prompt rule (search-first, broad
  before giving up, few-shot redirect, never present unlisted products). Verified 2x live:
  run 1 honest-empty (no invention) but category-narrow miss exposed by the tool log
  (`category=guitarras` → []); strengthened rule ("busque amplo"); run 2 textbook:
  clarify → broad search → fuzzy redirect to the real Tagima Memphis (R$429,90 / PIX R$408,40).
  Lesson: the tool log doesn't just diagnose — it aims the next fix.
- Phase 8 DONE (Nov 1): coverage 78% → 100% (554 stmts, 0 missed), suite 56 → 85, all
  hermetic (mocked `urlopen`, no network). New: `test_config.py` (defaults/env/cache),
  loader empty-table, `price_block` both branches, full Ollama+OpenAI client tests
  (payloads, headers, tool-call parsing, every error branch), CLI `build_agent` +
  scripted REPL (turn logging, EOF/blank/LLMError paths). Coverage tooling lives outside
  the venv (`pytest-cov` can't install into the sandboxed venv): user re-runs with a
  normal `pip install pytest-cov` + `python -m pytest tests/ --cov=emporio --cov-report=term-missing`.
  Postscript (user's strict run caught it): suite now warning-clean under `-W error` too.
  That hunt found a REAL product bug — `load_database` never closed its connection
  (`sqlite3` context managers commit but don't close), leaking one fd per load; fixed
  with `contextlib.closing` + explicit `commit` (closing alone silently rolls back —
  verified by 14 red tests before the commit line went in). Lesson: treat warnings as
  errors and the suite debugs your product code.
