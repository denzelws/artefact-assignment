# Live QA session 3 (DRAFT — raw output, curate in Phase 9)
User's own MY_QUESTIONS case. Model: llama3.2:3b, then qwen2.5:7b for comparison.

## "Ola, a loja de vcs vendem oq?"
3b (before fix):
> [...] Além disso, também vendemos acessórios relacionados à música, como cordas,
> palhetas, cabos, casos, pedais, amplificadores, boquilhas, entre outros.
Grade: 2/10 — confident inversion of manual section 1 (instruments ONLY).
Answered from pretraining, no tool consulted. Incident #4.

qwen2.5:7b (same question, no fix yet):
> [...] violões, baixos, violinos, teclados, guitarras e diversos acessórios para músicos.
Grade: 4/10 — also wrong on accessories. Proves rules alone don't beat prior.

3b (after few-shot example in ESCOPO):
> Nossa loja especializada em instrumentos musicais oferece uma ampla variedade de
> violões, guitarras, pandeiros, tamborins, e outros instrumentos musicais.
Grade: 9/10 — accessories gone, scope correct. Lesson: examples beat instructions.
