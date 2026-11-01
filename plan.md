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
