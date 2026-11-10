"""Tabelas normativas e coeficientes de equivalência da ABNT NBR 12721.

LOFRANO TECNOLOGIA.
"""

from enum import Enum
from fractions import Fraction
from typing import Dict


def formatar_centavos_br(centavos: int) -> str:
    """Formata valor em centavos inteiros para notação monetária brasileira (ex: 125050 -> 'R$ 1.250,50')."""
    negativo = centavos < 0
    centavos_abs = abs(centavos)
    reais = centavos_abs // 100
    resto = centavos_abs % 100
    reais_str = f"{reais:,}".replace(",", ".")
    sinal = "-" if negativo else ""
    return f"{sinal}R$ {reais_str},{resto:02d}"


def formatar_area_m2(area_centesimos: int) -> str:
    """Formata área em centésimos de m² para notação brasileira (ex: 8450 -> '84,50 m²')."""
    reais = area_centesimos // 100
    resto = abs(area_centesimos % 100)
    reais_str = f"{reais:,}".replace(",", ".")
    return f"{reais_str},{resto:02d} m²"


def formatar_fracao_pct(num: int, den: int) -> str:
    """Formata fração em percentual com duas casas decimais inteiras (ex: 3/4 -> '75,00%')."""
    if den == 0:
        return "0,00%"
    cent_pct = (num * 10000) // den
    inteiro = cent_pct // 100
    resto = abs(cent_pct % 100)
    return f"{inteiro},{resto:02d}%"


class TipologiaPadrao(str, Enum):
    """Projetos-padrão normatizados pela ABNT NBR 12721 e informados pelos SINDUSCONs."""

    R1_B = "R1-B"       # Residencial unifamiliar 1 pav - Padrão Baixo
    R1_N = "R1-N"       # Residencial unifamiliar 1 pav - Padrão Normal
    R1_A = "R1-A"       # Residencial unifamiliar 1 pav - Padrão Alto
    PP4_B = "PP4-B"     # Prédio popular 4 pavimentos - Padrão Baixo
    PP4_N = "PP4-N"     # Prédio popular 4 pavimentos - Padrão Normal
    R8_B = "R8-B"       # Residencial multifamiliar 8 pavimentos - Padrão Baixo
    R8_N = "R8-N"       # Residencial multifamiliar 8 pavimentos - Padrão Normal
    R8_A = "R8-A"       # Residencial multifamiliar 8 pavimentos - Padrão Alto
    R16_N = "R16-N"     # Residencial multifamiliar 16 pavimentos - Padrão Normal
    R16_A = "R16-A"     # Residencial multifamiliar 16 pavimentos - Padrão Alto
    PIS = "PIS"         # Projeto de Interesse Social
    CSL8_N = "CSL8-N"   # Comercial Salas e Lojas 8 pavimentos - Normal
    CSL8_A = "CSL8-A"   # Comercial Salas e Lojas 8 pavimentos - Alto
    CSL16_N = "CSL16-N" # Comercial Salas e Lojas 16 pavimentos - Normal
    CSL16_A = "CSL16-A" # Comercial Salas e Lojas 16 pavimentos - Alto
    CAL8_N = "CAL8-N"   # Comercial Andares Livres 8 pavimentos - Normal
    CAL8_A = "CAL8-A"   # Comercial Andares Livres 8 pavimentos - Alto
    GI = "GI"           # Galpão Industrial


class TipoDivisaoArea(str, Enum):
    """Classificação de áreas conforme Tabela 1 e Tabela 2 da ABNT NBR 12721."""

    PRIVATIVA_PRINCIPAL_COBERTA = "PRIVATIVA_PRINCIPAL_COBERTA"
    GARAGEM_COBERTA_SUBSOLO = "GARAGEM_COBERTA_SUBSOLO"
    GARAGEM_DESCOBERTA = "GARAGEM_DESCOBERTA"
    VARANDA_SACADA_COBERTA = "VARANDA_SACADA_COBERTA"
    TERRACO_DESCOBERTO = "TERRACO_DESCOBERTO"
    USO_COMUM_COBERTA_PILOTIS = "USO_COMUM_COBERTA_PILOTIS"
    AREAS_LAZER_DESCOBERTAS = "AREAS_LAZER_DESCOBERTAS"
    RESERVATORIO_BARRILETE_MAQUINAS = "RESERVATORIO_BARRILETE_MAQUINAS"
    DEPOSITO_PRIVATIVO_SUBSOLO = "DEPOSITO_PRIVATIVO_SUBSOLO"


# Coeficientes padrão de equivalência de custo em relação à área padrão (Tabela 1 e 2 NBR 12721)
COEFICIENTES_EQUIVALENCIA_NBR12721: Dict[TipoDivisaoArea, Fraction] = {
    TipoDivisaoArea.PRIVATIVA_PRINCIPAL_COBERTA: Fraction(1, 1),      # 1.00 (padrão)
    TipoDivisaoArea.GARAGEM_COBERTA_SUBSOLO: Fraction(3, 4),          # 0.75
    TipoDivisaoArea.GARAGEM_DESCOBERTA: Fraction(1, 8),               # 0.125
    TipoDivisaoArea.VARANDA_SACADA_COBERTA: Fraction(3, 4),           # 0.75
    TipoDivisaoArea.TERRACO_DESCOBERTO: Fraction(3, 10),              # 0.30
    TipoDivisaoArea.USO_COMUM_COBERTA_PILOTIS: Fraction(1, 2),        # 0.50
    TipoDivisaoArea.AREAS_LAZER_DESCOBERTAS: Fraction(1, 5),          # 0.20
    TipoDivisaoArea.RESERVATORIO_BARRILETE_MAQUINAS: Fraction(3, 4),  # 0.75
    TipoDivisaoArea.DEPOSITO_PRIVATIVO_SUBSOLO: Fraction(1, 2),       # 0.50
}


class TipoItemNaoIncluso(str, Enum):
    """Categorias de serviços e despesas não incluídas no CUB segundo Art. 54 da Lei 4.591/64."""

    FUNDACOES_ESPECIAIS = "FUNDACOES_ESPECIAIS"
    ELEVADORES = "ELEVADORES"
    INSTALACOES_ESPECIAIS = "INSTALACOES_ESPECIAIS"
    URBANIZACAO_PAISAGISMO = "URBANIZACAO_PAISAGISMO"
    PROJETOS_TAXAS = "PROJETOS_TAXAS"
    BDI_INCORPORACAO = "BDI_INCORPORACAO"
    OUTROS = "OUTROS"
