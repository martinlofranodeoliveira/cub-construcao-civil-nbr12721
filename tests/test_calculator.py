"""Testes do motor de cálculo de área equivalente NBR 12721 e orçamento CUB.

LOFRANO TECNOLOGIA.
"""

from fractions import Fraction
import unittest

from cub_construcao_civil.calculator import (
    calcular_area_equivalente,
    calcular_orcamento_global,
    divisao_teto,
)
from cub_construcao_civil.domain import (
    DivisaoAreaEntrada,
    ItemNaoInclusoEntrada,
    ProjetoEmpreendimentoEntrada,
)
from cub_construcao_civil.tabelas_nbr12721 import (
    TipoDivisaoArea,
    TipoItemNaoIncluso,
    TipologiaPadrao,
)


class TestCalculator(unittest.TestCase):

    def test_divisao_teto(self) -> None:
        self.assertEqual(divisao_teto(100, 10), 10)
        self.assertEqual(divisao_teto(101, 10), 11)
        self.assertEqual(divisao_teto(0, 5), 0)
        self.assertEqual(divisao_teto(1, 5), 1)
        with self.assertRaises(ValueError):
            divisao_teto(10, 0)

    def test_calcular_area_equivalente(self) -> None:
        # 100 m² (10.000 centésimos) com coef 1.0 (1/1) -> 10.000
        self.assertEqual(calcular_area_equivalente(10000, Fraction(1, 1)), 10000)
        # 100 m² com coef 0.75 (3/4) -> 7.500
        self.assertEqual(calcular_area_equivalente(10000, Fraction(3, 4)), 7500)
        # 100 m² com coef 0.125 (1/8) -> 1.250
        self.assertEqual(calcular_area_equivalente(10000, Fraction(1, 8)), 1250)
        # 100 m² com coef 0.30 (3/10) -> 3.000
        self.assertEqual(calcular_area_equivalente(10000, Fraction(3, 10)), 3000)

    def test_orcamento_sem_adicionais(self) -> None:
        # Apto: 100 m² (10.000 centésimos), Garagem subsolo: 40 m² (4.000 centésimos, coef 0.75 -> 3.000)
        # Área Real = 140 m² (14.000), Área Equivalente = 130 m² (13.000)
        # CUB/m² = R$ 2.000,00 (200.000 centavos)
        # Custo CUB = 13.000 * 200.000 / 100 = 26.000.000 centavos (R$ 260.000,00)
        a1 = DivisaoAreaEntrada("A1", "Privativa", TipoDivisaoArea.PRIVATIVA_PRINCIPAL_COBERTA, 10000)
        a2 = DivisaoAreaEntrada("A2", "Garagem", TipoDivisaoArea.GARAGEM_COBERTA_SUBSOLO, 4000)
        proj = ProjetoEmpreendimentoEntrada("Obra Simples", "PR", TipologiaPadrao.R1_N, "11/2026", "SINDUSCON-PR", 200000, False, [a1, a2], [])

        res = calcular_orcamento_global(proj)

        self.assertEqual(res.area_real_total_centesimos, 14000)
        self.assertEqual(res.area_equivalente_total_centesimos, 13000)
        self.assertEqual(res.custo_base_cub_centavos, 26000000)
        self.assertEqual(res.custo_itens_adicionais_centavos, 0)
        self.assertEqual(res.custo_global_construcao_centavos, 26000000)

        # Custo / m² real: 26.000.000 * 100 / 14.000 = 185.715 centavos (~ R$ 1.857,15 / m²)
        self.assertEqual(res.custo_m2_area_real_centavos, 185715)
        # Custo / m² equivalente: 26.000.000 * 100 / 13.000 = 200.000 centavos (R$ 2.000,00 / m²)
        self.assertEqual(res.custo_m2_area_equivalente_centavos, 200000)

    def test_orcamento_completo_com_adicionais(self) -> None:
        a1 = DivisaoAreaEntrada("A1", "Privativa", TipoDivisaoArea.PRIVATIVA_PRINCIPAL_COBERTA, 10000)
        item1 = ItemNaoInclusoEntrada("ELEV", "Elevador", TipoItemNaoIncluso.ELEVADORES, 5000000)
        item2 = ItemNaoInclusoEntrada("BDI", "BDI", TipoItemNaoIncluso.BDI_INCORPORACAO, 3000000)

        proj = ProjetoEmpreendimentoEntrada("Obra Completa", "SC", TipologiaPadrao.R8_A, "11/2026", "SINDUSCON-SC", 300000, False, [a1], [item1, item2])
        res = calcular_orcamento_global(proj)

        # Custo CUB = 10.000 * 300.000 / 100 = 30.000.000
        self.assertEqual(res.custo_base_cub_centavos, 30000000)
        self.assertEqual(res.custo_itens_adicionais_centavos, 8000000)
        self.assertEqual(res.custo_global_construcao_centavos, 38000000)

    def test_coeficiente_customizado_no_calculo(self) -> None:
        # Coeficiente customizado de 60% (6/10 = 3/5)
        a1 = DivisaoAreaEntrada("A1", "Varanda Gourmet", TipoDivisaoArea.VARANDA_SACADA_COBERTA, 10000, 3, 5)
        proj = ProjetoEmpreendimentoEntrada("Obra Custom", "MG", TipologiaPadrao.R1_A, "11/2026", "SINDUSCON-MG", 250000, False, [a1], [])
        res = calcular_orcamento_global(proj)

        self.assertEqual(res.areas[0].area_equivalente_m2_centesimos, 6000)
        self.assertEqual(res.areas[0].coeficiente_num, 3)
        self.assertEqual(res.areas[0].coeficiente_den, 5)

    def test_area_equivalente_zero(self) -> None:
        self.assertEqual(calcular_area_equivalente(0, Fraction(1, 1)), 0)
        self.assertEqual(calcular_area_equivalente(0, Fraction(3, 4)), 0)

    def test_coeficiente_acima_de_cem(self) -> None:
        # Área com acabamento nobre ou pé direito duplo (coeficiente 125% -> 5/4)
        self.assertEqual(calcular_area_equivalente(10000, Fraction(5, 4)), 12500)

