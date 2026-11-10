"""Interface de Linha de Comando (CLI) para orçamentação CUB e NBR 12721.

LOFRANO TECNOLOGIA.
"""

import argparse
from pathlib import Path
import sys
from typing import List, Optional

from .calculator import calcular_orcamento_global
from .codecs import (
    carregar_projeto,
    orcamento_para_dict,
    serializar_json_canonico,
)
from .errors import CUBError
from .exports import (
    criar_pacote_zip_deterministico,
    gerar_areas_csv_str,
    gerar_orcamento_global_csv_str,
    gerar_relatorio_markdown,
)
from .svg_report import gerar_painel_svg
from .tabelas_nbr12721 import formatar_area_m2, formatar_centavos_br, formatar_fracao_pct

VERSAO = "1.0.0"


def configurar_stdout_utf8() -> None:
    """Garante saída em UTF-8 nos consoles do Windows e Linux."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


EXEMPLO_PROJETO_JSON = """{
  "identificacao": "Edifício Residencial Jardins do Parque",
  "localizacao": "Bairro Bela Vista · São Paulo / SP",
  "tipologia": "R8-N",
  "mes_ano_referencia": "11/2026",
  "sinduscon_estado": "SINDUSCON-SP",
  "valor_cub_m2_centavos": 245080,
  "desoneracao_folha": false,
  "areas": [
    {
      "codigo": "AP-TIPO",
      "descricao": "Apartamentos-Tipo (32 unidades)",
      "tipo_area": "PRIVATIVA_PRINCIPAL_COBERTA",
      "area_real_m2_centesimos": 272000
    },
    {
      "codigo": "GAR-SS",
      "descricao": "Garagem Coberta no Subsolo",
      "tipo_area": "GARAGEM_COBERTA_SUBSOLO",
      "area_real_m2_centesimos": 98000
    },
    {
      "codigo": "VAR-SAC",
      "descricao": "Varandas e Sacadas Cobertas",
      "tipo_area": "VARANDA_SACADA_COBERTA",
      "area_real_m2_centesimos": 32000
    },
    {
      "codigo": "PIL-COM",
      "descricao": "Pilotis, Hall Social e Festas",
      "tipo_area": "USO_COMUM_COBERTA_PILOTIS",
      "area_real_m2_centesimos": 45000
    },
    {
      "codigo": "TER-DESC",
      "descricao": "Terraços Descobertos e Solarium",
      "tipo_area": "TERRACO_DESCOBERTO",
      "area_real_m2_centesimos": 18000
    },
    {
      "codigo": "LAZ-EXT",
      "descricao": "Piscinas e Quadra Descoberta",
      "tipo_area": "AREAS_LAZER_DESCOBERTAS",
      "area_real_m2_centesimos": 24000
    },
    {
      "codigo": "CXA-MAQ",
      "descricao": "Caixa d'Água, Barrilete e Casa de Máquinas",
      "tipo_area": "RESERVATORIO_BARRILETE_MAQUINAS",
      "area_real_m2_centesimos": 9500
    }
  ],
  "itens_nao_inclusos": [
    {
      "codigo": "FUND-01",
      "descricao": "Fundações Profundas em Estacas Hélice Contínua e Contenção",
      "tipo": "FUNDACOES_ESPECIAIS",
      "custo_centavos": 85000000
    },
    {
      "codigo": "ELEV-02",
      "descricao": "Conjunto de 2 Elevadores Sociais de Alta Velocidade",
      "tipo": "ELEVADORES",
      "custo_centavos": 42000000
    },
    {
      "codigo": "INST-03",
      "descricao": "Instalações de Combate a Incêndio, Pressurização e Gerador",
      "tipo": "INSTALACOES_ESPECIAIS",
      "custo_centavos": 31000000
    },
    {
      "codigo": "URB-04",
      "descricao": "Urbanização Externa, Paisagismo e Pavimentação",
      "tipo": "URBANIZACAO_PAISAGISMO",
      "custo_centavos": 18000000
    },
    {
      "codigo": "PROJ-05",
      "descricao": "Projetos Executivos, Compatibilização BIM e Taxas Cartorárias",
      "tipo": "PROJETOS_TAXAS",
      "custo_centavos": 25000000
    },
    {
      "codigo": "BDI-06",
      "descricao": "BDI da Construtora e Remuneração da Incorporação (15%)",
      "tipo": "BDI_INCORPORACAO",
      "custo_centavos": 195000000
    }
  ]
}
"""


def executar_orcamento(
    caminho_entrada: Path,
    saida_dir: Optional[Path] = None,
    saida_zip: Optional[Path] = None,
) -> int:
    """Executa o cálculo do orçamento global CUB e áreas equivalentes NBR 12721."""
    configurar_stdout_utf8()

    try:
        projeto = carregar_projeto(caminho_entrada)
        print(f"Empreendimento carregado: '{projeto.identificacao}' ({projeto.localizacao})")
        print(f"Tipologia CUB: {projeto.tipologia.value} · {projeto.sinduscon_estado} ({projeto.mes_ano_referencia})")
        print(f"Total de compartimentos de área: {len(projeto.areas)}")

        resultado = calcular_orcamento_global(projeto)

        fator_str = formatar_fracao_pct(resultado.fator_equivalencia_global_num, resultado.fator_equivalencia_global_den)

        print("\n--- RESULTADO DE CUSTO GLOBAL DE CONSTRUÇÃO (NBR 12721) ---")
        print(f"Área Real Total Construída: {formatar_area_m2(resultado.area_real_total_centesimos)}")
        print(f"Área Equivalente em Custo:  {formatar_area_m2(resultado.area_equivalente_total_centesimos)} (Fator Global: {fator_str})")
        print(f"Valor CUB/m² de Referência: {formatar_centavos_br(resultado.valor_cub_m2_centavos)}")
        print(f"Custo Base CUB:             {formatar_centavos_br(resultado.custo_base_cub_centavos)}")
        print(f"Itens Adicionais (Lei 4.591): {formatar_centavos_br(resultado.custo_itens_adicionais_centavos)}")
        print(f"CUSTO GLOBAL ESTIMADO:      {formatar_centavos_br(resultado.custo_global_construcao_centavos)}")
        print(f"Custo Médio / m² Real:      {formatar_centavos_br(resultado.custo_m2_area_real_centavos)} / m²")
        print(f"Custo Médio / m² Equivalente: {formatar_centavos_br(resultado.custo_m2_area_equivalente_centavos)} / m²")

        print("\nDetalhamento por Compartimento (NBR 12721):")
        for a in resultado.areas:
            coef_str = formatar_fracao_pct(a.coeficiente_num, a.coeficiente_den)
            print(
                f"  - [{a.codigo}] {a.descricao:36} | Real: {formatar_area_m2(a.area_real_m2_centesimos):10} | "
                f"Coef: {coef_str:6} | Equiv: {formatar_area_m2(a.area_equivalente_m2_centesimos):10} | Custo: {formatar_centavos_br(a.custo_atribuido_centavos)}"
            )

        # Gerar artefatos em memória
        orc_dict = orcamento_para_dict(resultado)
        orc_json_bytes = serializar_json_canonico(orc_dict).encode("utf-8")
        relatorio_md_bytes = gerar_relatorio_markdown(resultado).encode("utf-8")
        painel_svg_bytes = gerar_painel_svg(resultado).encode("utf-8")
        areas_csv_bytes = gerar_areas_csv_str(resultado).encode("utf-8")
        orcamento_csv_bytes = gerar_orcamento_global_csv_str(resultado).encode("utf-8")

        # Salvar em diretório se solicitado
        if saida_dir:
            saida_dir.mkdir(parents=True, exist_ok=True)
            (saida_dir / "orcamento_global.json").write_bytes(orc_json_bytes)
            (saida_dir / "relatorio.md").write_bytes(relatorio_md_bytes)
            (saida_dir / "painel.svg").write_bytes(painel_svg_bytes)
            (saida_dir / "areas_equivalentes.csv").write_bytes(areas_csv_bytes)
            (saida_dir / "orcamento_consolidado.csv").write_bytes(orcamento_csv_bytes)
            print(f"\nArtefatos gerados na pasta: {saida_dir.resolve()}")

        # Salvar pacote ZIP determinístico se solicitado
        if saida_zip:
            arquivos_zip = [
                ("entrada.json", caminho_entrada.read_bytes()),
                ("orcamento_global.json", orc_json_bytes),
                ("areas_equivalentes.csv", areas_csv_bytes),
                ("orcamento_consolidado.csv", orcamento_csv_bytes),
                ("relatorio.md", relatorio_md_bytes),
                ("painel.svg", painel_svg_bytes),
            ]
            criar_pacote_zip_deterministico(saida_zip, arquivos_zip)
            print(f"Pacote ZIP determinístico gerado: {saida_zip.resolve()}")

        return 0

    except CUBError as e:
        print(f"Erro no cálculo CUB: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Erro inesperado: {e}", file=sys.stderr)
        return 2


def main(argv: Optional[List[str]] = None) -> int:
    """Ponto de entrada principal da CLI."""
    configurar_stdout_utf8()

    parser = argparse.ArgumentParser(
        prog="cub-orcamento",
        description="Cálculo determinístico de Área Equivalente NBR 12721 e Orçamento CUB (LOFRANO TECNOLOGIA).",
    )
    parser.add_argument("-v", "--versao", action="store_true", help="Exibe a versão do programa.")

    subparsers = parser.add_subparsers(dest="comando", help="Comandos disponíveis")

    # Subcomando orcar
    parser_orcar = subparsers.add_parser("orcar", help="Calcula as áreas equivalentes e o orçamento global da edificação.")
    parser_orcar.add_argument("arquivo", type=str, help="Caminho do arquivo JSON do empreendimento.")
    parser_orcar.add_argument("--saida-dir", type=str, default=None, help="Diretório de saída para os relatórios.")
    parser_orcar.add_argument("--zip", type=str, default=None, help="Caminho para gerar o pacote ZIP determinístico.")

    # Subcomando exemplo
    parser_ex = subparsers.add_parser("exemplo", help="Exporta modelo canônico de empreendimento residencial.")
    parser_ex.add_argument("--saida", type=str, default=None, help="Arquivo de destino do exemplo.")

    # Subcomando versao
    subparsers.add_parser("versao", help="Exibe a versão instalada.")

    args = parser.parse_args(argv)

    if args.versao or args.comando == "versao":
        print(f"cub-orcamento {VERSAO}")
        return 0

    if args.comando == "exemplo":
        conteudo = EXEMPLO_PROJETO_JSON
        if args.saida:
            Path(args.saida).write_text(conteudo, encoding="utf-8")
            print(f"Exemplo canônico gravado em: {args.saida}")
        else:
            print(conteudo)
        return 0

    if args.comando == "orcar":
        caminho_in = Path(args.arquivo)
        caminho_dir = Path(args.saida_dir) if args.saida_dir else None
        caminho_zip = Path(args.zip) if args.zip else None
        return executar_orcamento(caminho_in, saida_dir=caminho_dir, saida_zip=caminho_zip)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
