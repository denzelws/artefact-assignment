# Live QA session 2 (DRAFT — raw output, curate in Phase 9)
Model: llama3.2:3b | Command: `.venv/bin/python scripts/live_qa.py` | Date: Oct 31 2026
Run after the category-stem fix (incident #3).

## 1. Olá! Quais violões até R$ 1000 vocês têm?
> [...] Tagima Memphis AC-39 Nylon Natural: R$ 429,90 [...] Rozini RC-104: R$ 459,90 [...]
> Shelby SN-100: R$ 549,00 [...] 10 real violões, real prices [...]
> Shelby SN-7C 7 Cordas: R$ 749,00 (atualmente descontinuado, mas tem um preço similar).
Grade: 8/10 — all real, but listed a discontinued item as buyable. Prompt hardened
("never list discontinued/coming_soon as purchasable").

## 2. Meu pedido 8 chegou?
> Olá, Ana Carolina Ferreira! Seu pedido nº 8 foi despachado [...] rastreamento é
> BRJL5544332BR [...] entrega [...] 28 de fevereiro de 2026 [...]
Grade: 10/10 — flawless.

## 3. Tem desconto no pix?
> Infelizmente, não há descontos atuais para o Pix. [...]
Grade: 3/10 — factually wrong twice in a row on 3b. Model capacity, no code fix.

## 4. Quero trocar um produto, como funciona?
> [...] 7 dias [...] WhatsApp (67) 3321-4500 [...] passos [...] "para a troca de acessórios,
> você precisará entregar o mesmo, pois eles não são trocados ou devolvidos."
Grade: 7/10 — clocks and channel right; invented accessories-exchange clause
(accessories are redirect-only). Minor 3b prose hallucination.
