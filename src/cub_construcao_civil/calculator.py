"""Motor de cálculo determinístico de área equivalente NBR 12721 e orçamento CUB.

Aritmética inteira em centavos e centésimos de m², frações exatas. Zero float.

LOFRANO TECNOLOGIA.
"""

from dataclasses import dataclass
from fractions import Fraction
from typing import List

from .domain import DivisaoAreaEntrada, ItemNaoInclusoEntrada, ProjetoEmpreendimentoEntrada
from .tabelas_nbr12721 import TipoDivisaoArea, TipoItemNaoIncluso, TipologiaPadrao


def divisao_teto(numerador: int, denominador: int) -> int:
    """Realiza divisão inteira arredondada para cima (ceiling)."""
    if denominador <= 0:
        raise ValueError("Denominador deve ser estritamente positivo.")
    return (numerador + denominador - 1) // denominador


def calcular_area_equivalente(area_real_centesimos: int, coef: Fraction) -> int:
    """Calcula a área equivalente em centésimos de m² com arredondamento teto."""
    return divisao_teto(area_real_centesimos * coef.numerator, coef.denominator)


@dataclass(frozen=True)
class DivisaoAreaCalculada:
    """Resultado do cálculo de área equivalente e apropriação de custo CUB para uma divisão."""

    codigo: str
    descricao: str
    tipo_area: TipoDivisaoArea
    area_real_m2_centesimos: int
    coeficiente_num: int
    coeficiente_den: int
    area_equivalente_m2_centesimos: int
    participacao_area_real_pct_num: int
    participacao_area_real_pct_den: int
    custo_atribuido_centavos: int


@dataclass(frozen=True)
class ItemNaoInclusoCalculado:
    """Item adicional não incluso no CUB com participação percentual no orçamento complementar."""

    codigo: str
    descricao: str
    tipo: TipoItemNaoIncluso
    custo_centavos: int
    participacao_adicional_num: int
    participacao_adicional_den: int


@dataclass(frozen=True)
class OrcamentoGlobalResultado:
    """Orçamento global consolidado com áreas reais, equivalentes e custos CUB."""

    identificacao: str
    localizacao: str
    tipologia: TipologiaPadrao
    mes_ano_referencia: str
    sinduscon_estado: str
    valor_cub_m2_centavos: int
    desoneracao_folha: bool
    area_real_total_centesimos: int
    area_equivalente_total_centesimos: int
    fator_equivalencia_global_num: int
    fator_equivalencia_global_den: int
    custo_base_cub_centavos: int
    custo_itens_adicionais_centavos: int
    custo_global_construcao_centavos: int
    custo_m2_area_real_centavos: int
    custo_m2_area_equivalente_centavos: int
    areas: List[DivisaoAreaCalculada]
    itens_adicionais: List[ItemNaoInclusoCalculado]


def calcular_orcamento_global(projeto: ProjetoEmpreendimentoEntrada) -> OrcamentoGlobalResultado:
    """Calcula o orçamento global da edificação com base na NBR 12721 e CUB/m² informado."""
    # 1. Totalização e equivalência de áreas
    area_real_total = sum(a.area_real_m2_centesimos for a in projeto.areas)
    if area_real_total <= 0:
        raise ValueError("A área real total do empreendimento deve ser positiva.")

    areas_calc: List[DivisaoAreaCalculada] = []
    area_equiv_total = 0

    for a in projeto.areas:
        coef = a.coeficiente_equivalencia
        a_eq = calcular_area_equivalente(a.area_real_m2_centesimos, coef)
        area_equiv_total += a_eq

        part_real_frac = Fraction(a.area_real_m2_centesimos, area_real_total)
        # Custo atribuído da área: área equivalente x CUB unitário / 100
        custo_atribuido = divisao_teto(a_eq * projeto.valor_cub_m2_centavos, 100)

        areas_calc.append(
            DivisaoAreaCalculada(
                codigo=a.codigo,
                descricao=a.descricao,
                tipo_area=a.tipo_area,
                area_real_m2_centesimos=a.area_real_m2_centesimos,
                coeficiente_num=coef.numerator,
                coeficiente_den=coef.denominator,
                area_equivalente_m2_centesimos=a_eq,
                participacao_area_real_pct_num=part_real_frac.numerator,
                participacao_area_real_pct_den=part_real_frac.denominator,
                custo_atribuido_centavos=custo_atribuido,
            )
        )

    # 2. Custo Base CUB da edificação
    # Custo CUB = Área Equivalente Total (centésimos) * CUB_m2 (centavos) / 100
    custo_base_cub = divisao_teto(area_equiv_total * projeto.valor_cub_m2_centavos, 100)

    # 3. Processamento de itens adicionais não inclusos no CUB (Art. 54 Lei 4.591/64)
    custo_adicionais_total = sum(item.custo_centavos for item in projeto.itens_nao_inclusos)
    itens_calc: List[ItemNaoInclusoCalculado] = []

    for item in projeto.itens_nao_inclusos:
        if custo_adicionais_total > 0:
            part_adic_frac = Fraction(item.custo_centavos, custo_adicionais_total)
        else:
            part_adic_frac = Fraction(0, 1)

        itens_calc.append(
            ItemNaoInclusoCalculado(
                codigo=item.codigo,
                descricao=item.descricao,
                tipo=item.tipo,
                custo_centavos=item.custo_centavos,
                participacao_adicional_num=part_adic_frac.numerator,
                participacao_adicional_den=part_adic_frac.denominator,
            )
        )

    # 4. Custo Global de Construção
    custo_global = custo_base_cub + custo_adicionais_total

    # 5. Indicadores unitários médios por m² real e equivalente
    custo_m2_real = divisao_teto(custo_global * 100, area_real_total)
    custo_m2_equiv = divisao_teto(custo_global * 100, area_equiv_total) if area_equiv_total > 0 else 0

    # 6. Fator de Equivalência Global: Área Equivalente / Área Real
    fator_global_frac = Fraction(area_equiv_total, area_real_total)

    return OrcamentoGlobalResultado(
        identificacao=projeto.identificacao,
        localizacao=projeto.localizacao,
        tipologia=projeto.tipologia,
        mes_ano_referencia=projeto.mes_ano_referencia,
        sinduscon_estado=projeto.sinduscon_estado,
        valor_cub_m2_centavos=projeto.valor_cub_m2_centavos,
        desoneracao_folha=projeto.desoneracao_folha,
        area_real_total_centesimos=area_real_total,
        area_equivalente_total_centesimos=area_equiv_total,
        fator_equivalencia_global_num=fator_global_frac.numerator,
        fator_equivalencia_global_den=fator_global_frac.denominator,
        custo_base_cub_centavos=custo_base_cub,
        custo_itens_adicionais_centavos=custo_adicionais_total,
        custo_global_construcao_centavos=custo_global,
        custo_m2_area_real_centavos=custo_m2_real,
        custo_m2_area_equivalente_centavos=custo_m2_equiv,
        areas=areas_calc,
        itens_adicionais=itens_calc,
    )
