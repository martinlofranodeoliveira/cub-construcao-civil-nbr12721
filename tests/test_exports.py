"""Testes de exportação (CSV, Markdown, SVG e ZIP determinístico) para NBR 12721 e CUB.

LOFRANO TECNOLOGIA.
"""

from pathlib import Path
import tempfile
import unittest
import zipfile

from cub_construcao_civil.calculator import calcular_orcamento_global
from cub_construcao_civil.domain import (
    DivisaoAreaEntrada,
    ItemNaoInclusoEntrada,
    ProjetoEmpreendimentoEntrada,
)
from cub_construcao_civil.errors import ERR_ARQUIVO_EXISTENTE, CUBError
from cub_construcao_civil.exports import (
    criar_pacote_zip_deterministico,
    gerar_areas_csv_str,
    gerar_orcamento_global_csv_str,
    gerar_relatorio_markdown,
    sanitizar_csv,
)
from cub_construcao_civil.svg_report import gerar_painel_svg
from cub_construcao_civil.tabelas_nbr12721 import (
    TipoDivisaoArea,
    TipoItemNaoIncluso,
    TipologiaPadrao,
)


class TestExports(unittest.TestCase):

    def setUp(self) -> None:
        a1 = DivisaoAreaEntrada("=A1", "+Apartamento Tipo", TipoDivisaoArea.PRIVATIVA_PRINCIPAL_COBERTA, 10000)
        a2 = DivisaoAreaEntrada("-G1", "@Garagem Subsolo", TipoDivisaoArea.GARAGEM_COBERTA_SUBSOLO, 4000)
        item1 = ItemNaoInclusoEntrada("=F1", "+Fundação Especial", TipoItemNaoIncluso.FUNDACOES_ESPECIAIS, 5000000)
        self.projeto = ProjetoEmpreendimentoEntrada(
            "Residencial Teste",
            "Campinas / SP",
            TipologiaPadrao.R8_N,
            "11/2026",
            "SINDUSCON-SP",
            250000,
            False,
            [a1, a2],
            [item1],
        )
        self.orcamento = calcular_orcamento_global(self.projeto)

    def test_sanitizar_csv_formula_injection(self) -> None:
        self.assertEqual(sanitizar_csv("=1+1"), "'=1+1")
        self.assertEqual(sanitizar_csv("+1234"), "'+1234")
        self.assertEqual(sanitizar_csv("-5678"), "'-5678")
        self.assertEqual(sanitizar_csv("@cmd"), "'@cmd")
        self.assertEqual(sanitizar_csv("\ttab"), "'\ttab")
        self.assertEqual(sanitizar_csv("\rret"), "'\rret")
        self.assertEqual(sanitizar_csv("Apartamento 101"), "Apartamento 101")

    def test_gerar_areas_csv_str(self) -> None:
        csv_str = gerar_areas_csv_str(self.orcamento)
        linhas = csv_str.strip().splitlines()
        self.assertEqual(len(linhas), 3)  # Cabeçalho + 2 áreas
        cabecalho = linhas[0].split(";")
        self.assertIn("codigo", cabecalho)
        self.assertIn("area_equivalente_m2", cabecalho)

        # Checar sanitização no primeiro compartimento
        linha1 = linhas[1].split(";")
        self.assertEqual(linha1[0], "'=A1")
        self.assertEqual(linha1[1], "'+Apartamento Tipo")

    def test_gerar_orcamento_global_csv_str(self) -> None:
        csv_str = gerar_orcamento_global_csv_str(self.orcamento)
        linhas = csv_str.strip().splitlines()
        self.assertEqual(len(linhas), 3)  # Cabeçalho + CUB_BASICO + Item 1
        self.assertIn("CUB_BASICO", linhas[1])
        self.assertIn("ITENS_ADICIONAIS_LEI_4591", linhas[2])

    def test_gerar_relatorio_markdown(self) -> None:
        md = gerar_relatorio_markdown(self.orcamento)
        self.assertIn("# Relatório de Custo Global de Construção (CUB/NBR 12721) — Residencial Teste", md)
        self.assertIn("Área Real Total Construída", md)
        self.assertIn("Área Equivalente em Custo (NBR 12721)", md)
        self.assertIn("Serviços Adicionais (Lei 4.591/64)", md)
        self.assertIn("Zero Float", md)

    def test_gerar_painel_svg(self) -> None:
        svg = gerar_painel_svg(self.orcamento)
        self.assertTrue(svg.startswith("<svg"))
        self.assertTrue(svg.endswith("</svg>\n"))
        self.assertIn('viewBox="0 0 1440 900"', svg)
        self.assertIn("Residencial Teste", svg)
        self.assertIn("CUSTO GLOBAL ESTIMADO", svg)
        self.assertIn("LOFRANO TECNOLOGIA", svg)

    def test_criar_pacote_zip_deterministico(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            zip1 = Path(tmpdir) / "teste1.zip"
            zip2 = Path(tmpdir) / "teste2.zip"

            arquivos = [
                ("relatorio.md", b"# Relatorio\nConteudo fixo.\n"),
                ("dados.csv", b"col1;col2\n1;2\n"),
            ]

            criar_pacote_zip_deterministico(zip1, arquivos)
            criar_pacote_zip_deterministico(zip2, arquivos)

            self.assertEqual(zip1.read_bytes(), zip2.read_bytes())

            with zipfile.ZipFile(zip1, "r") as zf:
                self.assertEqual(zf.namelist(), ["dados.csv", "relatorio.md"])

    def test_criar_pacote_zip_nao_sobrescreve(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_arq = Path(tmpdir) / "ja_existe.zip"
            zip_arq.write_bytes(b"conteudo")

            with self.assertRaises(CUBError) as ctx:
                criar_pacote_zip_deterministico(zip_arq, [("a.txt", b"a")])
            self.assertEqual(ctx.exception.codigo, ERR_ARQUIVO_EXISTENTE)
