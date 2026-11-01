"""Policy search robustness: accents, typos, and graceful fallback."""

import pytest

from emporio.data import (
    POLICY_SECTIONS,
    get_section,
    get_store_info,
    list_sections,
    search_policies,
)


def test_ten_sections() -> None:
    assert len(POLICY_SECTIONS) == 10


@pytest.mark.parametrize(
    ("query", "expected_top1"),
    [
        ("devolucao", "trocas_devolucoes"),  # no accent
        ("DEVOLUÇÃO!!!", "trocas_devolucoes"),  # shouting + punctuation
        ("prazo para trocar produto com defeito", "trocas_devolucoes"),
        ("garantia", "garantia"),
        ("quantos dias de garantia tenho", "garantia"),
        ("frete gratis p campo grande", "frete_entregas"),
        ("que horas abre sabado?", "horarios"),
        ("boleto", "pagamentos"),
        ("12x sem juros", "pagamentos"),
        ("lgpd quero apagar meus dados", "privacidade"),
        ("reclamacao", "atendimento_whatsapp"),  # no tilde
    ],
)
def test_mangled_queries_rank_first(query: str, expected_top1: str) -> None:
    assert search_policies(query)[0].id == expected_top1


@pytest.mark.parametrize("query", ["PIX", "rastreio do meu pedido"])
def test_ambiguous_queries_contain_expected(query: str) -> None:
    ids = [section.id for section in search_policies(query)]
    assert ("pagamentos" in ids) or ("frete_entregas" in ids)


@pytest.mark.parametrize("query", ["qero divolber um produt com deffeito", "?!? ...", ""])
def test_garbage_falls_back_to_index(query: str) -> None:
    assert len(search_policies(query)) == 10


def test_section_index_and_lookup() -> None:
    index = list_sections()
    assert len(index) == 10
    assert {"id", "title"} <= set(index[0].keys())
    assert get_section("horarios") is not None
    assert get_section("nope") is None


def test_store_info_applies_manual_corrections() -> None:
    info = get_store_info()
    assert info.phone_whatsapp == "(67) 3321-4500"
    assert info.phone_store == "(67) 3341-4444"
    assert info.email == "contato@emporiodamusica.com.br"  # unaccented, valid
    assert "14 de Maio" in info.address
