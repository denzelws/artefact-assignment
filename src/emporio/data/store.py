"""Structured store identity for the ``get_store_info`` tool.

Source: manual sections 1.2 (company data) and 2 (hours), plus the cover page.

Known manual quirks (plan section 6), resolved here so the agent never
repeats them:
- The cover lists ``(67) 3341-4444`` while section 7 gives WhatsApp
  ``(67) 3321-4500`` — both are kept, with explicit labels.
- The section 1.2 table prints ``contato@empóriodamusica.com.br``
  (accented, invalid) — the cover page confirms the correct
  ``contato@emporiodamusica.com.br``, used here.
"""

from pydantic import BaseModel, Field


class StoreInfo(BaseModel):
    """Public identity, address, hours and contact channels."""

    name: str = "Empório da Música"
    legal_name: str = "Empório da Música Instrumentos Musicais Ltda."
    cnpj: str = "12.345.678/0001-90"
    address: str = "Rua 14 de Maio, 3200 — Centro, Campo Grande - MS, 79202-333"
    phone_store: str = Field(
        default="(67) 3341-4444", description="Main store line (cover page)."
    )
    phone_whatsapp: str = Field(
        default="(67) 3321-4500", description="Primary remote channel (section 7)."
    )
    email: str = "contato@emporiodamusica.com.br"
    hours_weekdays: str = "Segunda a sexta-feira: 09:00 às 18:00"
    hours_saturday: str = "Sábado: 09:00 às 13:00"
    hours_sunday: str = "Domingo e feriados: fechado"
    founded: int = 2008


def get_store_info() -> StoreInfo:
    """Return the store identity block quoted by the agent."""
    return StoreInfo()
