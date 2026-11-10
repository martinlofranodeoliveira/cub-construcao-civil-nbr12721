"""Testes das tabelas normativas e enums da ABNT NBR 12721.

LOFRANO TECNOLOGIA.
"""

from fractions import Fraction
import unittest

from cub_construcao_civil.tabelas_nbr12721 import (
    COEFICIENTES_EQUIVALENCIA_NBR12721,
    TipoDivisaoArea,
    TipoItemNaoIncluso,
    TipologiaPadrao,
)


class TestTabelasNBR12721(unittest.TestCase):

    def test_todas_divisoes_possuem_coeficiente(self) -> None:
        for tipo in TipoDivisaoArea:
            self.assertIn(tipo, COEFICIENTES_EQUIVALENCIA_NBR12721)
            coef = COEFICIENTES_EQUIVALENCIA_NBR12721[tipo]
            self.assertIsInstance(coef, Fraction)
            self.assertGreater(coef, 0)
            self.assertLessEqual(coef, 1)

    def test_coeficientes_especificos_norma(self) -> None:
        self.assertEqual(COEFICIENTES_EQUIVALENCIA_NBR12721[TipoDivisaoArea.PRIVATIVA_PRINCIPAL_COBERTA], Fraction(1, 1))
        self.assertEqual(COEFICIENTES_EQUIVALENCIA_NBR12721[TipoDivisaoArea.GARAGEM_COBERTA_SUBSOLO], Fraction(3, 4))
        self.assertEqual(COEFICIENTES_EQUIVALENCIA_NBR12721[TipoDivisaoArea.GARAGEM_DESCOBERTA], Fraction(1, 8))
        self.assertEqual(COEFICIENTES_EQUIVALENCIA_NBR12721[TipoDivisaoArea.TERRACO_DESCOBERTO], Fraction(3, 10))
        self.assertEqual(COEFICIENTES_EQUIVALENCIA_NBR12721[TipoDivisaoArea.USO_COMUM_COBERTA_PILOTIS], Fraction(1, 2))
        self.assertEqual(COEFICIENTES_EQUIVALENCIA_NBR12721[TipoDivisaoArea.AREAS_LAZER_DESCOBERTAS], Fraction(1, 5))

    def test_tipologias_principais_presentes(self) -> None:
        self.assertEqual(TipologiaPadrao.R1_N.value, "R1-N")
        self.assertEqual(TipologiaPadrao.R8_N.value, "R8-N")
        self.assertEqual(TipologiaPadrao.R16_N.value, "R16-N")
        self.assertEqual(TipologiaPadrao.CSL8_N.value, "CSL8-N")
        self.assertEqual(TipologiaPadrao.GI.value, "GI")

    def test_tipos_itens_adicionais_lei_4591(self) -> None:
        self.assertIn(TipoItemNaoIncluso.FUNDACOES_ESPECIAIS, list(TipoItemNaoIncluso))
        self.assertIn(TipoItemNaoIncluso.ELEVADORES, list(TipoItemNaoIncluso))
        self.assertIn(TipoItemNaoIncluso.INSTALACOES_ESPECIAIS, list(TipoItemNaoIncluso))
        self.assertIn(TipoItemNaoIncluso.URBANIZACAO_PAISAGISMO, list(TipoItemNaoIncluso))
        self.assertIn(TipoItemNaoIncluso.BDI_INCORPORACAO, list(TipoItemNaoIncluso))
