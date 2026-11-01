# Live QA session 1 (DRAFT — raw output, curate in Phase 9)
Model: llama3.2:3b | Command: `.venv/bin/python scripts/live_qa.py` | Date: Oct 31 2026

## 1. Olá! Quais violões até R$ 1000 vocês têm?
> Peço desculpas, mas não consegui encontrar violões até R$ 1000 na nossa loja. Posso sugerir
> algumas opções de violões mais acessíveis que ainda sejam de boa qualidade? [...]
Grade: FAIL (recall) — `category="violão"` (singular) matched 0 rows. Root cause of incident #3,
fixed by stemming the category comparison.

## 2. Meu pedido 8 chegou?
> Olá Ana Carolina! [...] Seu pedido de número 8 já foi enviado! [...] rastreamento BRJL5544332BR.
> [...] entrega é de 28 de fevereiro de 2026. [...]
Grade: PASS — real name, real code, real ETA. ("viiol" typo variant seen in earlier runs.)

## 3. Tem desconto no pix?
> Desculpe, Ana Carolina! Infelizmente, não encontramos nenhuma promoção disponível para o seu
> pedido. No entanto, [...] Kalani KAL-700T [...] 10% [...] Ohana CK-20 [...] 20% [...]
Grade: FAIL (reasoning) — never stated the 5% PIX rule despite it being in the prompt.
3b-model capacity, second data point. No code fix.

## 4. Quero trocar um produto, como funciona?
> [...] 7 dias corridos [...] 30 dias corridos [defeito] [...] preferência [...] 7 dias [...]
Grade: PASS — correct clocks and exclusions.
