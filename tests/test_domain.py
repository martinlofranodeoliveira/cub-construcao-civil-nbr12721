"""Testes de modelo de domínio e validação para NBR 12721 e CUB.

LOFRANO TECNOLOGIA.
"""

from fractions import Fraction
import unittest

from cub_construcao_civil.domain import (
    DivisaoAreaEntrada,
    ItemNaoInclusoEntrada,
    ProjetoEmpreendimentoEntrada,
)
from cub_construcao_civil.errors import ERR_VALIDACAO, ErroValidacao
from cub_construcao_civil.tabelas_nbr12721 import (
    TipoDivisaoArea,
    TipoItemNaoIncluso,
    TipologiaPadrao,
    formatar_area_m2,
    formatar_centavos_br,
    formatar_fracao_pct,
)


class TestDominio(unittest.TestCase):

    def test_formatar_centavos_br(self) -> None:
        self.assertEqual(formatar_centavos_br(0), "R$ 0,00")
        self.assertEqual(formatar_centavos_br(250), "R$ 2,50")
        self.assertEqual(formatar_centavos_br(245080), "R$ 2.450,80")
        self.assertEqual(formatar_centavos_br(1000000000), "R$ 10.000.000,00")
        self.assertEqual(formatar_centavos_br(-50000), "-R$ 500,00")

    def test_formatar_area_m2(self) -> None:
        self.assertEqual(formatar_area_m2(0), "0,00 m²")
        self.assertEqual(formatar_area_m2(8450), "84,50 m²")
        self.assertEqual(formatar_area_m2(120000), "1.200,00 m²")

    def test_formatar_fracao_pct(self) -> None:
        self.assertEqual(formatar_fracao_pct(0, 100), "0,00%")
        self.assertEqual(formatar_fracao_pct(3, 4), "75,00%")
        self.assertEqual(formatar_fracao_pct(1, 8), "12,50%")
        self.assertEqual(formatar_fracao_pct(1, 1), "100,00%")
        self.assertEqual(formatar_fracao_pct(5, 0), "0,00%")

    def test_divisao_area_valida(self) -> None:
        d = DivisaoAreaEntrada("AP-01", "Apartamento", TipoDivisaoArea.PRIVATIVA_PRINCIPAL_COBERTA, 8500)
        self.assertEqual(d.codigo, "AP-01")
        self.assertEqual(d.area_real_m2_centesimos, 8500)
        self.assertEqual(d.coeficiente_equivalencia, Fraction(1, 1))

    def test_divisao_area_customizada(self) -> None:
        d = DivisaoAreaEntrada("DIV-01", "Área Específica", TipoDivisaoArea.USO_COMUM_COBERTA_PILOTIS, 10000, 6, 10)
        self.assertEqual(d.coeficiente_equivalencia, Fraction(3, 5))

    def test_divisao_area_codigo_vazio(self) -> None:
        with self.assertRaises(ErroValidacao) as ctx:
            DivisaoAreaEntrada("", "Apartamento", TipoDivisaoArea.PRIVATIVA_PRINCIPAL_COBERTA, 8500)
        self.assertEqual(ctx.exception.codigo, ERR_VALIDACAO)

    def test_divisao_area_descricao_vazia(self) -> None:
        with self.assertRaises(ErroValidacao) as ctx:
            DivisaoAreaEntrada("AP", "   ", TipoDivisaoArea.PRIVATIVA_PRINCIPAL_COBERTA, 8500)
        self.assertEqual(ctx.exception.codigo, ERR_VALIDACAO)

    def test_divisao_area_negativa(self) -> None:
        with self.assertRaises(ErroValidacao) as ctx:
            DivisaoAreaEntrada("AP", "Apartamento", TipoDivisaoArea.PRIVATIVA_PRINCIPAL_COBERTA, 0)
        self.assertEqual(ctx.exception.codigo, ERR_VALIDACAO)

        with self.assertRaises(ErroValidacao) as ctx:
            DivisaoAreaEntrada("AP", "Apartamento", TipoDivisaoArea.PRIVATIVA_PRINCIPAL_COBERTA, -500)
        self.assertEqual(ctx.exception.codigo, ERR_VALIDACAO)

    def test_divisao_area_coeficiente_incompleto(self) -> None:
        with self.assertRaises(ErroValidacao) as ctx:
            DivisaoAreaEntrada("AP", "Apartamento", TipoDivisaoArea.PRIVATIVA_PRINCIPAL_COBERTA, 8500, 5, None)
        self.assertEqual(ctx.exception.codigo, ERR_VALIDACAO)

        with self.assertRaises(ErroValidacao) as ctx:
            DivisaoAreaEntrada("AP", "Apartamento", TipoDivisaoArea.PRIVATIVA_PRINCIPAL_COBERTA, 8500, None, 10)
        self.assertEqual(ctx.exception.codigo, ERR_VALIDACAO)

    def test_item_adicional_valido(self) -> None:
        item = ItemNaoInclusoEntrada("ELEV", "Elevador", TipoItemNaoIncluso.ELEVADORES, 15000000)
        self.assertEqual(item.codigo, "ELEV")
        self.assertEqual(item.custo_centavos, 15000000)

    def test_item_adicional_custo_negativo(self) -> None:
        with self.assertRaises(ErroValidacao) as ctx:
            ItemNaoInclusoEntrada("ELEV", "Elevador", TipoItemNaoIncluso.ELEVADORES, -100)
        self.assertEqual(ctx.exception.codigo, ERR_VALIDACAO)

    def test_projeto_valido(self) -> None:
        a = DivisaoAreaEntrada("A1", "Apto", TipoDivisaoArea.PRIVATIVA_PRINCIPAL_COBERTA, 10000)
        p = ProjetoEmpreendimentoEntrada("Proj", "SP", TipologiaPadrao.R8_N, "11/2026", "SINDUSCON-SP", 250000, False, [a], [])
        self.assertEqual(p.identificacao, "Proj")
        self.assertEqual(len(p.areas), 1)

    def test_projeto_sem_areas(self) -> None:
        with self.assertRaises(ErroValidacao) as ctx:
            ProjetoEmpreendimentoEntrada("Proj", "SP", TipologiaPadrao.R8_N, "11/2026", "SINDUSCON-SP", 250000, False, [], [])
        self.assertEqual(ctx.exception.codigo, ERR_VALIDACAO)

    def test_projeto_cub_negativo(self) -> None:
        a = DivisaoAreaEntrada("A1", "Apto", TipoDivisaoArea.PRIVATIVA_PRINCIPAL_COBERTA, 10000)
        with self.assertRaises(ErroValidacao) as ctx:
            ProjetoEmpreendimentoEntrada("Proj", "SP", TipologiaPadrao.R8_N, "11/2026", "SINDUSCON-SP", 0, False, [a], [])
        self.assertEqual(ctx.exception.codigo, ERR_VALIDACAO)

    def test_projeto_areas_duplicadas(self) -> None:
        a1 = DivisaoAreaEntrada("A1", "Apto 1", TipoDivisaoArea.PRIVATIVA_PRINCIPAL_COBERTA, 10000)
        a2 = DivisaoAreaEntrada("A1", "Apto 2", TipoDivisaoArea.PRIVATIVA_PRINCIPAL_COBERTA, 12000)
        with self.assertRaises(ErroValidacao) as ctx:
            ProjetoEmpreendimentoEntrada("Proj", "SP", TipologiaPadrao.R8_N, "11/2026", "SINDUSCON-SP", 250000, False, [a1, a2], [])
        self.assertEqual(ctx.exception.codigo, ERR_VALIDACAO)
