"""Testes do codec canônico determinístico para projetos NBR 12721 e orçamentos CUB.

LOFRANO TECNOLOGIA.
"""

from fractions import Fraction
import json
from pathlib import Path
import tempfile
import unittest

from cub_construcao_civil.calculator import calcular_orcamento_global
from cub_construcao_civil.codecs import (
    carregar_projeto,
    decodificar_json_canonico,
    orcamento_para_dict,
    serializar_json_canonico,
)
from cub_construcao_civil.domain import DivisaoAreaEntrada, ProjetoEmpreendimentoEntrada
from cub_construcao_civil.errors import (
    ERR_BOM_PROIBIDO,
    ERR_CHAVE_DUPLICADA,
    ERR_FLOAT_PROIBIDO,
    ERR_JSON_INVALIDO,
    ERR_PROFUNDIDADE_EXCEDIDA,
    ERR_TIPO_AREA_INVALIDO,
    ERR_TIPOLOGIA_INVALIDA,
    ErroCodec,
)
from cub_construcao_civil.tabelas_nbr12721 import TipoDivisaoArea, TipologiaPadrao


class TestCodecs(unittest.TestCase):

    def test_rejeitar_bom_bytes(self) -> None:
        payload = b"\xef\xbb\xbf{\"identificacao\": \"Ed\"}"
        with self.assertRaises(ErroCodec) as ctx:
            decodificar_json_canonico(payload)
        self.assertEqual(ctx.exception.codigo, ERR_BOM_PROIBIDO)

    def test_rejeitar_bom_str(self) -> None:
        payload = "\ufeff{\"identificacao\": \"Ed\"}"
        with self.assertRaises(ErroCodec) as ctx:
            decodificar_json_canonico(payload)
        self.assertEqual(ctx.exception.codigo, ERR_BOM_PROIBIDO)

    def test_rejeitar_chave_duplicada(self) -> None:
        payload = '{"p": 1, "p": 2}'
        with self.assertRaises(ErroCodec) as ctx:
            decodificar_json_canonico(payload)
        self.assertEqual(ctx.exception.codigo, ERR_CHAVE_DUPLICADA)

    def test_rejeitar_float_na_leitura(self) -> None:
        payload = '{"valor_cub": 2450.50}'
        with self.assertRaises(ErroCodec) as ctx:
            decodificar_json_canonico(payload)
        self.assertEqual(ctx.exception.codigo, ERR_FLOAT_PROIBIDO)

    def test_rejeitar_float_na_serializacao(self) -> None:
        dados = {"area": 84.5}
        with self.assertRaises(ErroCodec) as ctx:
            serializar_json_canonico(dados)
        self.assertEqual(ctx.exception.codigo, ERR_FLOAT_PROIBIDO)

    def test_rejeitar_profundidade_excessiva(self) -> None:
        obj: dict = {}
        curr = obj
        for _ in range(35):
            curr["filho"] = {}
            curr = curr["filho"]
        texto = json.dumps(obj)
        with self.assertRaises(ErroCodec) as ctx:
            decodificar_json_canonico(texto)
        self.assertEqual(ctx.exception.codigo, ERR_PROFUNDIDADE_EXCEDIDA)

    def test_serializacao_deterministica(self) -> None:
        dados = {
            "z": 10,
            "a": 20,
            "frac": Fraction(3, 4),
            "areas": [
                {"codigo": "A2", "m2": 50},
                {"codigo": "A1", "m2": 100},
            ],
        }
        res = serializar_json_canonico(dados)
        self.assertTrue(res.endswith("\n"))
        linhas = [ln for ln in res.splitlines() if ln.strip()]
        self.assertTrue(linhas[1].strip().startswith('"a":'))
        self.assertTrue(linhas[-2].strip().startswith('"z":'))

    def test_carregar_projeto_valido(self) -> None:
        caminho_exemplar = (
            Path(__file__).resolve().parent.parent / "exemplares" / "edificio_residencial_r8n.json"
        )
        proj = carregar_projeto(caminho_exemplar)
        self.assertEqual(proj.identificacao, "Edifício Residencial Jardins do Parque")
        self.assertEqual(proj.tipologia, TipologiaPadrao.R8_N)
        self.assertEqual(len(proj.areas), 7)
        self.assertEqual(len(proj.itens_nao_inclusos), 6)

    def test_carregar_projeto_arquivo_inexistente(self) -> None:
        with self.assertRaises(FileNotFoundError):
            carregar_projeto(Path("/caminho/fantasma/obra.json"))

    def test_carregar_projeto_raiz_nao_objeto(self) -> None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as tmp:
            tmp.write("[1, 2, 3]")
            caminho = Path(tmp.name)
        try:
            with self.assertRaises(ErroCodec) as ctx:
                carregar_projeto(caminho)
            self.assertEqual(ctx.exception.codigo, ERR_JSON_INVALIDO)
        finally:
            caminho.unlink(missing_ok=True)

    def test_carregar_projeto_campos_obrigatorios_ausentes(self) -> None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as tmp:
            tmp.write('{"localizacao": "SP", "areas": []}')
            caminho = Path(tmp.name)
        try:
            with self.assertRaises(ErroCodec) as ctx:
                carregar_projeto(caminho)
            self.assertEqual(ctx.exception.codigo, ERR_JSON_INVALIDO)
        finally:
            caminho.unlink(missing_ok=True)

    def test_carregar_projeto_tipologia_invalida(self) -> None:
        conteudo = """{
            "identificacao": "Obra Invalida",
            "localizacao": "SP",
            "tipologia": "TIPOLOGIA_NAO_EXISTE",
            "mes_ano_referencia": "11/2026",
            "sinduscon_estado": "SINDUSCON-SP",
            "valor_cub_m2_centavos": 200000,
            "desoneracao_folha": false,
            "areas": []
        }"""
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as tmp:
            tmp.write(conteudo)
            caminho = Path(tmp.name)
        try:
            with self.assertRaises(ErroCodec) as ctx:
                carregar_projeto(caminho)
            self.assertEqual(ctx.exception.codigo, ERR_TIPOLOGIA_INVALIDA)
        finally:
            caminho.unlink(missing_ok=True)

    def test_carregar_projeto_tipo_area_invalido(self) -> None:
        conteudo = """{
            "identificacao": "Obra Invalida",
            "localizacao": "SP",
            "tipologia": "R1-N",
            "mes_ano_referencia": "11/2026",
            "sinduscon_estado": "SINDUSCON-SP",
            "valor_cub_m2_centavos": 200000,
            "desoneracao_folha": false,
            "areas": [
                {
                    "codigo": "A1",
                    "descricao": "Area",
                    "tipo_area": "TIPO_DESCONHECIDO",
                    "area_real_m2_centesimos": 1000
                }
            ]
        }"""
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as tmp:
            tmp.write(conteudo)
            caminho = Path(tmp.name)
        try:
            with self.assertRaises(ErroCodec) as ctx:
                carregar_projeto(caminho)
            self.assertEqual(ctx.exception.codigo, ERR_TIPO_AREA_INVALIDO)
        finally:
            caminho.unlink(missing_ok=True)

    def test_orcamento_para_dict_completo(self) -> None:
        a = DivisaoAreaEntrada("A1", "Apto", TipoDivisaoArea.PRIVATIVA_PRINCIPAL_COBERTA, 10000)
        proj = ProjetoEmpreendimentoEntrada("Edificio", "SP", TipologiaPadrao.R1_N, "11/2026", "SINDUSCON-SP", 250000, False, [a], [])
        orc = calcular_orcamento_global(proj)
        d = orcamento_para_dict(orc)

        self.assertEqual(d["identificacao"], "Edificio")
        self.assertIn("totais_areas", d)
        self.assertIn("totais_custos", d)
        self.assertEqual(len(d["areas"]), 1)
        self.assertEqual(d["areas"][0]["codigo"], "A1")
