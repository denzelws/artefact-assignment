"""Store policy sections transcribed from the shop manual.

Source: ``data/políticas_da_loja.pdf`` (v2.1, June 2025), read once during
development with an throwaway PDF extractor. The texts below are faithful,
condensed Portuguese transcriptions — the agent quotes them, never the PDF.

``search_policies`` ranks sections by keyword overlap (accent-insensitive,
so ``devolucao`` matches ``devolução``) and falls back to the section
index when nothing matches, per the plan.
"""

from pydantic import BaseModel, Field

from .text import query_tokens, word_set


class PolicySection(BaseModel):
    """One titled manual section the agent can quote."""

    id: str = Field(description="Stable slug, e.g. 'trocas_devolucoes'.")
    title: str = Field(description="Manual heading, e.g. 'Trocas e Devoluções'.")
    keywords: list[str] = Field(
        default_factory=list, description="Portuguese lookup terms for ranking."
    )
    text: str = Field(description="Condensed transcription of the manual section.")


POLICY_SECTIONS: list[PolicySection] = [
    PolicySection(
        id="sobre_loja",
        title="Sobre a Empório da Música",
        keywords=["loja", "historia", "missao", "sobre", "catalogo", "instrumentos", "acessorios"],
        text=(
            "Loja especializada em instrumentos musicais, fundada em 2008 em Campo Grande/MS, "
            "referência regional para músicos iniciantes, intermediários e profissionais. "
            "Missão: democratizar o acesso a instrumentos de qualidade no Centro-Oeste. "
            "Trabalha EXCLUSIVAMENTE com instrumentos musicais — não vende acessórios "
            "(cordas, palhetas, cabos, cases, pedais, amplificadores)."
        ),
    ),
    PolicySection(
        id="horarios",
        title="Horário de Funcionamento",
        keywords=["horario", "aberto", "fecha", "funcionamento", "sabado", "domingo", "feriado",
                  "abrir", "abre", "fechar", "atende"],
        text=(
            "Segunda a sexta-feira: 09:00 às 18:00. Sábado: 09:00 às 13:00. "
            "Domingo e feriados: fechado. O WhatsApp segue o mesmo horário, com respostas "
            "automáticas fora do expediente. Em datas especiais (Black Friday, Aniversário, Natal) "
            "o horário pode ser estendido, avisado nas redes sociais e no WhatsApp."
        ),
    ),
    PolicySection(
        id="pagamentos",
        title="Formas de Pagamento",
        keywords=["pagamento", "pix", "cartao", "credito", "debito", "boleto", "parcela", "desconto",
                  "pagar", "parcelar", "juros", "vista"],
        text=(
            "PIX: à vista com 5% de desconto sobre o preço de tabela. Cartão de débito: à vista, "
            "todas as bandeiras. Cartão de crédito: até 12x sem juros, parcela mínima de R$ 100,00. "
            "Boleto: à vista, compensação em até 3 dias úteis. Parcelamento: até 3x sem mínimo "
            "(exceto abaixo de R$ 50,00); 4x–6x parcela mínima de R$ 80,00; 7x–12x parcela mínima "
            "de R$ 100,00. Combinação de formas (ex.: PIX + cartão) permitida acima de R$ 2.000,00."
        ),
    ),
    PolicySection(
        id="trocas_devolucoes",
        title="Trocas e Devoluções",
        keywords=["troca", "devolucao", "arrependimento", "defeito", "reembolso", "prazo", "defeituoso",
                  "trocar", "devolver", "reembolsar"],
        text=(
            "Arrependimento (compras online): devolução em até 7 dias corridos após o recebimento, "
            "sem justificativa, produto na embalagem original sem sinais de uso; reembolso na mesma "
            "forma de pagamento em até 10 dias úteis; frete de devolução por conta da loja. "
            "Defeito de fabricação: troca em até 30 dias corridos; após 30 dias, acionar o fabricante "
            "(a loja pode intermediar). Mau uso, quedas, umidade ou modificações não são cobertos. "
            "Troca por preferência (cor/modelo): até 7 dias, produto intacto, diferença cobrada ou "
            "reembolsada. NÃO elegíveis: personalizados/sob encomenda, liquidação com 'venda final', "
            "boquilhas de sopro (higiene)."
        ),
    ),
    PolicySection(
        id="frete_entregas",
        title="Frete e Entregas",
        keywords=["frete", "entrega", "prazo", "rastreamento", "rastreio", "correios", "jadlog", "pac", "sedex", "envio",
                  "enviar", "entregar", "rastrear", "gratis", "taxa"],
        text=(
            "Campo Grande e região: frete GRÁTIS acima de R$ 500,00; abaixo disso taxa fixa de "
            "R$ 35,00; prazo 1 a 3 dias úteis, entrega por motoboy próprio (cliente é contactado "
            "por telefone). Outras cidades: Correios (PAC 5–12 dias úteis, SEDEX 2–5 dias úteis) e "
            "Jadlog (3–8 dias úteis), todos com rastreamento e seguro incluídos; frete calculado por "
            "CEP/peso/dimensões; grande porte pode exigir cotação individual. Rastreamento: código "
            "padrão BR + 9 alfanuméricos + BR (ex.: BR4K7M2X9P1BR), enviado por e-mail e WhatsApp ao "
            "despachar. Em caso de avaria, recusar o recebimento e contactar a loja imediatamente."
        ),
    ),
    PolicySection(
        id="promocoes",
        title="Promoções e Descontos",
        keywords=["promocao", "desconto", "cupom", "black", "friday", "oferta", "queima", "aniversario"],
        text=(
            "Campanhas: Aniversário da Loja (agosto, 10%–25%), Black Friday (novembro, 15%–30%), "
            "Volta às Aulas (fevereiro), Queima de Estoque e Semana do Músico (22 de novembro). "
            "Regras: promoções NÃO são cumulativas — o desconto de PIX (5%) não se aplica sobre "
            "preços promocionais. Sujeitas a estoque, sem rain check (reserva de preço). Preços "
            "promocionais sempre apresentados com preço original e percentual de desconto."
        ),
    ),
    PolicySection(
        id="atendimento_whatsapp",
        title="Atendimento via WhatsApp",
        keywords=["whatsapp", "atendimento", "contato", "reclamacao", "tom", "resposta", "fluxo"],
        text=(
            "WhatsApp (67) 3321-4500 é o principal canal remoto, com humanos ou assistente virtual. "
            "Tom: informal mas profissional, como um amigo que entende de música. Resposta em até "
            "5 minutos no expediente; fora dele, informar horário de retorno. NUNCA informar preço, "
            "estoque ou prazo sem consultar o sistema. Escopo: só instrumentos; acessórios "
            "(cordas, cabos, palhetas, pedais, amplificadores, cases) são redirecionados. "
            "Fluxo: saudação (pelo nome, se conhecido) → entendimento → consulta ao sistema → "
            "resposta com preços/condições → fechamento cordial. Fora de estoque: sugerir "
            "alternativas. Descontinuado: oferecer equivalentes. Promoção expirada: informar com "
            "transparência o preço atual. Reclamação: empatia, registrar, encaminhar — retorno em "
            "24 horas úteis."
        ),
    ),
    PolicySection(
        id="garantia",
        title="Garantia",
        keywords=["garantia", "defeito", "fabricante", "cobertura", "assistência", "prazo",
                  "garantir", "conserto"],
        text=(
            "Garantia legal: 90 dias contra defeitos de fabricação, da data de recebimento (CDC). "
            "Garantia do fabricante: 6 meses a 2 anos conforme certificado que acompanha o produto. "
            "NÃO cobre: desgaste natural (trastes, cordas, feltros), mau uso/queda/clima extremo, "
            "modificações ou reparos por terceiros não autorizados, danos estéticos sem perda funcional."
        ),
    ),
    PolicySection(
        id="privacidade",
        title="Privacidade e Proteção de Dados",
        keywords=["privacidade", "lgpd", "dados", "pessoais", "exclusao", "consentimento",
                  "apagar", "excluir"],
        text=(
            "Conformidade com a LGPD (Lei nº 13.709/2018). Dados (nome, telefone, e-mail, endereço) "
            "usados só para: processar e entregar pedidos, comunicar status/rastreamento, enviar "
            "promoções (só com consentimento explícito) e obrigações legais/fiscais. Dados NÃO são "
            "compartilhados com terceiros para marketing. Cliente pode pedir exclusão a qualquer "
            "momento via WhatsApp ou e-mail."
        ),
    ),
    PolicySection(
        id="disposicoes_finais",
        title="Disposições Finais",
        keywords=["manual", "versao", "gerencia", "duvida", "atualizacao"],
        text=(
            "Manual interno v2.1 (junho/2025), referência da equipe e do assistente virtual, sujeito "
            "a atualizações. Em dúvida sobre qualquer política, consultar a gerência antes de "
            "responder ao cliente. Objetivo: transparência, precisão e a melhor experiência possível."
        ),
    ),
]


def list_sections() -> list[dict[str, str]]:
    """Return the section index (id + title), used as the search fallback."""
    return [{"id": section.id, "title": section.title} for section in POLICY_SECTIONS]


def search_policies(query: str, limit: int = 3) -> list[PolicySection]:
    """Rank sections by keyword/text overlap; fall back to all sections.

    Whole-word, accent-insensitive matching: stopwords, single letters and pure
    numbers never become tokens. Scoring: a query token in the title counts 3,
    in keywords 2, in text 1. Empty queries or zero scores return the full section
    list so the caller (tool/agent) can present the index instead of
    nothing.
    """
    tokens = query_tokens(query)
    if not tokens:
        return list(POLICY_SECTIONS)

    scored: list[tuple[int, PolicySection]] = []
    for section in POLICY_SECTIONS:
        title = word_set(section.title)
        keywords = word_set(" ".join(section.keywords))
        text = word_set(section.text)
        score = sum(
            (3 if token in title else 0) + (2 if token in keywords else 0) + (1 if token in text else 0)
            for token in tokens
        )
        if score > 0:
            scored.append((score, section))
    if not scored:
        return list(POLICY_SECTIONS)
    scored.sort(key=lambda item: item[0], reverse=True)
    return [section for _, section in scored[:limit]]


def get_section(section_id: str) -> PolicySection | None:
    """Fetch one section by id, or None for unknown ids."""
    matches = [section for section in POLICY_SECTIONS if section.id == section_id]
    return matches[0] if matches else None
