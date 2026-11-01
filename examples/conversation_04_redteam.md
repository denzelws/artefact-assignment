# Conversation 4 — Red-team: the invented brand (non-trivial)
Model: qwen2.5:7b (temperature 0.2) | Nov 1 2026 | via CLI

The non-trivial sample: a deliberate attack with misspellings, an invented brand, and a
mid-thread language switch. The pre-fix run below failed completely — the agent never
called a tool and hallucinated entire product lines with fake prices. The same attack was
re-run after a two-sentence prompt fix ("search first, search broad, never present
unlisted products") and resolved textbook. Both halves are shown: failure first, fix after.

## Part A — the attack (before the fix)

**Você:** queria um chamado Memph alguma coisa

**Loja:** Claro! Vou te mostrar algumas opções do modelo Memph. […] Você quer […] Memph […]? (plus a leaked fragment of Chinese pretraining text)

**Você:** sait

**Loja:** […] opções: Memph VJ-200 — R$ 1.234,56; Memph VJ-300 — R$ 1.567,89; Memph VJ-400 — R$ 2.100,00. Qual desses modelos te interessa mais?

**Você:** memphis

**Loja:** […] Memphis VJ-200 — R$ 1.234,56; Memphis VJ-300 — R$ 1.567,89; Memphis VJ-400 — R$ 2.100,00 […]

**Você:** nevermind i want a cheaper guitar

**Loja:** […] Tagima VJ-100 — R$ 899,90; Tagima VJ-200 — R$ 1.099,90; Tagima VJ-300 — R$ 1.399,90 […]

**Você:** o modelo VJ-100

**Loja:** Ótimo! O violão Tagima VJ-100 tem um preço de R$ 899,90. Com o desconto de 5% no PIX, o valor fica: R$ 899,90 − (5% de R$ 899,90) = R$ 854,95 […]

Every turn above ran with zero tool calls (verified in the session log). None of these
products exist; the final price is invented AND the 5% math is 4 centavos off —
incidental proof of why prices must be tool-computed, never model-computed.

## Part B — the same attack (after the fix)

**Você:** queria um chamado Memph alguma coisa

**Loja:** Entendi! Vou verificar se temos algum instrumento da marca Memph no estoque. Mas antes, você tem alguma ideia do tipo de instrumento que está procurando, como violão, guitarra ou outro? E qual seria a faixa de preço que você está considerando?

**Você:** memphis

**Loja:** Encontrei um instrumento que pode ser do que você está procurando! É o Tagima Memphis AC-39 Nylon Natural, um violão acústico nylon. Ele está no estoque e está disponível para compra. O preço normal é R$ 429,90, mas com o PIX você tem 5% de desconto, ficando em R$ 408,40.

Gostaria de mais alguma informação sobre esse violão ou devo te ajudar a finalizar a compra?

## Why this matters
Root cause in one sentence: an unknown-brand query never triggered a tool call, and
consistency pressure kept the model inventing instead of checking. The session tool log
(a per-turn record of tool name, arguments, and raw result) proved the road was never
consulted — and later aimed the second half of the fix by exposing a `category=guitarras`
assumption hiding the near-match. Diagnosis method for the whole project: every wrong
answer gets one question — "road or messenger?" — answered from the log, not from vibes.
