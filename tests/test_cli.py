"""Testes da interface de linha de comando (CLI) para NBR 12721 e CUB.

LOFRANO TECNOLOGIA.
"""

import io
from pathlib import Path
import sys
import tempfile
import unittest

from cub_construcao_civil.cli import VERSAO, main


class TestCLI(unittest.TestCase):

    def setUp(self) -> None:
        self.caminho_exemplar = (
            Path(__file__).resolve().parent.parent / "exemplares" / "edificio_residencial_r8n.json"
        )

    def test_cli_versao_flag(self) -> None:
        buf = io.StringIO()
        antigo = sys.stdout
        try:
            sys.stdout = buf
            cod = main(["--versao"])
            self.assertEqual(cod, 0)
            self.assertIn(f"cub-orcamento {VERSAO}", buf.getvalue())
        finally:
            sys.stdout = antigo

    def test_cli_versao_subcomando(self) -> None:
        buf = io.StringIO()
        antigo = sys.stdout
        try:
            sys.stdout = buf
            cod = main(["versao"])
            self.assertEqual(cod, 0)
            self.assertIn(f"cub-orcamento {VERSAO}", buf.getvalue())
        finally:
            sys.stdout = antigo

    def test_cli_ajuda(self) -> None:
        buf = io.StringIO()
        antigo = sys.stdout
        try:
            sys.stdout = buf
            cod = main([])
            self.assertEqual(cod, 0)
            self.assertIn("cub-orcamento", buf.getvalue())
        finally:
            sys.stdout = antigo

    def test_cli_exemplo_stdout(self) -> None:
        buf = io.StringIO()
        antigo = sys.stdout
        try:
            sys.stdout = buf
            cod = main(["exemplo"])
            self.assertEqual(cod, 0)
            self.assertIn("Edifício Residencial Jardins do Parque", buf.getvalue())
        finally:
            sys.stdout = antigo

    def test_cli_exemplo_arquivo(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            arq = Path(tmpdir) / "modelo.json"
            cod = main(["exemplo", "--saida", str(arq)])
            self.assertEqual(cod, 0)
            self.assertTrue(arq.exists())
            self.assertIn("Edifício Residencial Jardins do Parque", arq.read_text(encoding="utf-8"))

    def test_cli_orcar_stdout(self) -> None:
        buf = io.StringIO()
        antigo = sys.stdout
        try:
            sys.stdout = buf
            cod = main(["orcar", str(self.caminho_exemplar)])
            self.assertEqual(cod, 0)
            saida = buf.getvalue()
            self.assertIn("Edifício Residencial Jardins do Parque", saida)
            self.assertIn("RESULTADO DE CUSTO GLOBAL DE CONSTRUÇÃO", saida)
            self.assertIn("Área Real Total Construída:", saida)
            self.assertIn("Custo Base CUB:", saida)
        finally:
            sys.stdout = antigo

    def test_cli_orcar_com_saida_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_saida = Path(tmpdir) / "relatorios_obra"
            cod = main(["orcar", str(self.caminho_exemplar), "--saida-dir", str(dir_saida)])
            self.assertEqual(cod, 0)
            self.assertTrue((dir_saida / "orcamento_global.json").exists())
            self.assertTrue((dir_saida / "relatorio.md").exists())
            self.assertTrue((dir_saida / "painel.svg").exists())
            self.assertTrue((dir_saida / "areas_equivalentes.csv").exists())
            self.assertTrue((dir_saida / "orcamento_consolidado.csv").exists())

    def test_cli_orcar_com_zip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_saida = Path(tmpdir) / "pacote.zip"
            cod = main(["orcar", str(self.caminho_exemplar), "--zip", str(zip_saida)])
            self.assertEqual(cod, 0)
            self.assertTrue(zip_saida.exists())
            self.assertGreater(zip_saida.stat().st_size, 0)

    def test_cli_orcar_arquivo_inexistente(self) -> None:
        buf_err = io.StringIO()
        antigo = sys.stderr
        try:
            sys.stderr = buf_err
            cod = main(["orcar", "/caminho/inexistente.json"])
            self.assertEqual(cod, 2)
            self.assertIn("Erro inesperado", buf_err.getvalue())
        finally:
            sys.stderr = antigo
