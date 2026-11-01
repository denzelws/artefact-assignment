# Live QA session 5 — freestyle red-team (DRAFT — raw output, curate in Phase 9)
Model: qwen2.5:7b, temperature 0.2 | Command:
`EMPORIO_OLLAMA_MODEL=qwen2.5:7b .venv/bin/python -m emporio.cli` | Nov 1 2026

One continuous session: the 7-question graded script, then a freestyle attack with
misspellings, an invented brand, and language-switching. Tool calls per turn are logged
(`sessions.jsonl` now records them) — every failure below is X-rayed, not guessed.

## Graded script

## 1. Violões até R$1000
8 real violões, all ≤ R$1000, correct PIX math on every line. Road:
`search_products {category: violoes, max_price: 1000}` → 10 rows (one discontinued
correctly skipped by the messenger). Grade: 10/10.

## 2. Tagima (follow-up)
Stayed in budget, listed options, asked which — but `tools: []`: coasted on history,
so 2 of 4 in-budget Tagimas (Woodstock R$899, TW-7 R$999 missing). Grade: 8/10 —
right behavior, lossy recall.

## 3. Tem desconto no pix?
5%, scoped to products without active promotion. Grade: 10/10.

## 4. Valor do Tagima Memphis no PIX?
R$408,40 — the tool's number, zero model arithmetic. Grade: 10/10.

## 5. A loja vende oq?
"Exclusivamente instrumentos musicais" + partner redirect for accessories.
Grade: 10/10 — the incident-#4 few-shot holds on qwen.

## 6. Trocar violão comprado online há 10 dias
Stated the 7-day regret clock correctly but never concluded the obvious:
10 > 7, the window has CLOSED. Hedged ("vamos verificar se está dentro do prazo").
Grade: 5/10 — right rule, no conclusion. Reasoning gap, not knowledge gap.

## 7. Como acompanho meu pedido 8?
`tools: []` — and asked for the order number ALREADY GIVEN ("me forneça o número
do pedido"). Grade: 2/10 — no-call failure on qwen, same disease as the attack below.

## Freestyle attack (the red-team win)

## 8. "queria um chamado Memph alguma coisa" (invented brand)
No tool call. Asked what instrument type — plus a leaked fragment of Chinese
pretraining text mid-confusion. Grade: 4/10 — no invention yet, but no search either.

## 9. "sait" (gibberish)
Full hallucination: invented "Memph VJ-200/300/400" with fake prices in a JSON block.
`tools: []`. Grade: 0/10 — the catastrophic turn.

## 10. "memphis" → "nevermind i want a cheaper guitar" (language switch)
Doubled down: invented "Memphis VJ" line, then grafted a REAL brand onto invented
models ("Tagima VJ-100/200/300", fake prices). `tools: []` throughout. Grade: 0/10 —
consistency pressure kept it inventing instead of checking.

## 11. "tem desconto no pix? estou com orcamento curto" + "o modelo VJ-100"
Correctly stated the 5% rule, then confirmed the INVENTED R$899,90 and did its own
5% math (R$854,95 — off by 4 centavos from the true 854,91). Grade: 3/10 — right rule,
wrong universe. Incidental proof of why tools must compute prices, never the model.

## Verdict and fix status
Root cause (one sentence): an unknown-brand query never triggered a tool call, and
once the model answered directly, consistency pressure kept it inventing. The road was
never consulted — and a post-session probe showed the road even HAD the answer
(`query="Memph"` → the real Tagima Memphis via fuzzy match).
Fix: new prompt rule (search-first, search BROAD before giving up, few-shot redirect,
never present unlisted products) — see `prompt.py` "Marca/modelo desconhecido".
Verified live 2x against the same attack: round 1 honest-empty, round 2 textbook
(clarify → broad search → fuzzy redirect to the real Memphis, R$429,90 / PIX R$408,40).
The tool log aimed the second fix (it exposed a `category=guitarras` assumption hiding
the near-match). Full story in `plan.md` §10.
