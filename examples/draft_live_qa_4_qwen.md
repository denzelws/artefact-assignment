# Live QA session 4 (DRAFT — raw output, curate in Phase 9)
Model: qwen2.5:7b (first full-qwen session) | Command:
`EMPORIO_OLLAMA_MODEL=qwen2.5:7b .venv/bin/python scripts/live_qa.py` | Oct 31 2026

## 1. Violões até R$ 1000
10 real violões, real prices, every line with correct PIX math (R$429,90 -> R$408,40).
Grade: 10/10 — the reference answer.

## 2. Meu pedido 8 chegou?
Asked the user for the tracking code/order ID instead of using "8" as the order id.
Grade: 5/10 — extraction flakiness (3b sometimes gets this right). Same known class as
incident #5: messenger-side, run-varying, not a road bug. Noted, not chased.

## 3. Tem desconto no pix?
Stated the 5% table-price rule with the no-promo condition, asked which instrument.
Grade: 10/10 — closes incident #6 for 7b+.

## 4. Quero trocar um produto?
Correct 7-day/10-day-refund flow, but framed everything as return/refund and skipped
the 30-day defect distinction.
Grade: 8/10 — right facts, incomplete clock coverage.

## 5. A loja vende oq? (user's MY_QUESTIONS case)
"Vendemos exclusivamente instrumentos musicais" + explicit partner redirect for
accessories. Grade: 10/10 — the few-shot from incident #4 generalizes to qwen.
