"""Exportadores e geradores de relatórios analíticos, CSVs seguros e pacotes determinísticos para CUB.

LOFRANO TECNOLOGIA.
"""

from fractions import Fraction
import os
from pathlib import Path
from typing import Any, List, Union
import zipfile

from .calculator import OrcamentoGlobalResultado
from .errors import ERR_ARQUIVO_EXISTENTE, CUBError
from .tabelas_nbr12721 import formatar_area_m2, formatar_centavos_br, formatar_fracao_pct

CARACTERES_INJECAO = ("=", "+", "-", "@", "\t", "\r")


def sanitizar_csv(valor: Any) -> str:
    """Neutraliza tentativa de injeção de fórmulas em planilhas (DDE/CSV injection)."""
    s = str(valor)
    if s and s[0] in CARACTERES_INJECAO:
        return f"'{s}"
    return s


def gerar_areas_csv_str(orcamento: OrcamentoGlobalResultado) -> str:
    """Gera texto CSV sanitizado com o detalhamento das áreas reais e equivalentes da NBR 12721."""
    linhas: List[str] = [
        "codigo;descricao;tipo_area;area_real_m2_centesimos;area_real_m2;coeficiente_frac;coeficiente_pct;area_equivalente_m2_centesimos;area_equivalente_m2;part_area_real_pct;custo_atribuido_centavos;custo_atribuido_br"
    ]

    for a in orcamento.areas:
        colunas = [
            sanitizar_csv(a.codigo),
            sanitizar_csv(a.descricao),
            a.tipo_area.value,
            str(a.area_real_m2_centesimos),
            formatar_area_m2(a.area_real_m2_centesimos),
            f"{a.coeficiente_num}/{a.coeficiente_den}",
            formatar_fracao_pct(a.coeficiente_num, a.coeficiente_den),
            str(a.area_equivalente_m2_centesimos),
            formatar_area_m2(a.area_equivalente_m2_centesimos),
            formatar_fracao_pct(a.participacao_area_real_pct_num, a.participacao_area_real_pct_den),
            str(a.custo_atribuido_centavos),
            formatar_centavos_br(a.custo_atribuido_centavos),
        ]
        linhas.append(";".join(colunas))

    return "\n".join(linhas) + "\n"


def gerar_orcamento_global_csv_str(orcamento: OrcamentoGlobalResultado) -> str:
    """Gera texto CSV com o orçamento consolidado: CUB básico e itens adicionais não inclusos."""
    linhas: List[str] = [
        "categoria;codigo;descricao;tipo;custo_centavos;custo_br;participacao_pct"
    ]

    # Linha do CUB Básico
    linhas.append(";".join([
        "CUB_BASICO",
        "CUB-BASE",
        sanitizar_csv(f"Custo Base CUB ({orcamento.tipologia.value} · {orcamento.sinduscon_estado})"),
        "CONSTRUCAO_PADRAO",
        str(orcamento.custo_base_cub_centavos),
        formatar_centavos_br(orcamento.custo_base_cub_centavos),
        formatar_fracao_pct(orcamento.custo_base_cub_centavos, orcamento.custo_global_construcao_centavos),
    ]))

    # Linhas dos itens adicionais não inclusos no CUB
    for item in orcamento.itens_adicionais:
        linhas.append(";".join([
            "ITENS_ADICIONAIS_LEI_4591",
            sanitizar_csv(item.codigo),
            sanitizar_csv(item.descricao),
            item.tipo.value,
            str(item.custo_centavos),
            formatar_centavos_br(item.custo_centavos),
            formatar_fracao_pct(item.custo_centavos, orcamento.custo_global_construcao_centavos),
        ]))

    return "\n".join(linhas) + "\n"


def gerar_relatorio_markdown(orcamento: OrcamentoGlobalResultado) -> str:
    """Gera relatório executivo de área equivalente NBR 12721 e orçamento CUB."""
    fator_global_str = formatar_fracao_pct(
        orcamento.fator_equivalencia_global_num,
        orcamento.fator_equivalencia_global_den,
    )

    linhas = [
        f"# Relatório de Custo Global de Construção (CUB/NBR 12721) — {orcamento.identificacao}",
        f"**Localização da Obra:** {orcamento.localizacao}",
        f"**Tipologia Padrão:** {orcamento.tipologia.value} · **Entidade:** {orcamento.sinduscon_estado}",
        f"**Mês/Ano de Referência:** {orcamento.mes_ano_referencia} · **Desoneração da Folha:** {'Sim' if orcamento.desoneracao_folha else 'Não'}",
        f"**Valor do CUB/m²:** {formatar_centavos_br(orcamento.valor_cub_m2_centavos)}",
        "",
        "---",
        "",
        "## 1. Resumo Executivo de Custos e Áreas",
        "",
        "| Indicador de Projeto | Grandeza Física / Monetária | Notação por m² |",
        "|---|---|---|",
        f"| **Área Real Total Construída** | **{formatar_area_m2(orcamento.area_real_total_centesimos)}** | 100,00% da área bruta |",
        f"| **Área Equivalente em Custo (NBR 12721)** | **{formatar_area_m2(orcamento.area_equivalente_total_centesimos)}** | Fator de Equivalência Global: **{fator_global_str}** |",
        f"| **Custo Base CUB** | **{formatar_centavos_br(orcamento.custo_base_cub_centavos)}** | {formatar_centavos_br(orcamento.valor_cub_m2_centavos)} / m² equiv. |",
        f"| **Serviços Adicionais (Lei 4.591/64)** | **{formatar_centavos_br(orcamento.custo_itens_adicionais_centavos)}** | Fundações, elevadores, BDI, taxas |",
        f"| **CUSTO GLOBAL ESTIMADO DA OBRA** | **{formatar_centavos_br(orcamento.custo_global_construcao_centavos)}** | **{formatar_centavos_br(orcamento.custo_m2_area_real_centavos)} / m² real** |",
        f"| **Custo Global por m² Equivalente** | — | **{formatar_centavos_br(orcamento.custo_m2_area_equivalente_centavos)} / m² equiv.** |",
        "",
        "---",
        "",
        "## 2. Quadro Geral de Áreas Reais e Equivalentes (Quadro II NBR 12721)",
        "",
        "| Código | Descrição do Compartimento | Tipo de Área | Área Real | Coeficiente | Área Equivalente | Custo CUB Estimado |",
        "|---|---|---|---|---|---|---|",
    ]

    for a in orcamento.areas:
        coef_str = formatar_fracao_pct(a.coeficiente_num, a.coeficiente_den)
        linhas.append(
            f"| `{a.codigo}` | {a.descricao} | `{a.tipo_area.value}` | "
            f"{formatar_area_m2(a.area_real_m2_centesimos)} | {coef_str} | "
            f"**{formatar_area_m2(a.area_equivalente_m2_centesimos)}** | {formatar_centavos_br(a.custo_atribuido_centavos)} |"
        )

    linhas.extend([
        "",
        "---",
        "",
        "## 3. Discriminação dos Serviços Não Inclusos no CUB (Art. 54 Lei 4.591/64)",
        "",
        "| Código | Descrição do Serviço / Despesa | Categoria | Custo Orçado | Participação |",
        "|---|---|---|---|---|",
    ])

    for item in orcamento.itens_adicionais:
        part_str = formatar_fracao_pct(item.participacao_adicional_num, item.participacao_adicional_den)
        linhas.append(
            f"| `{item.codigo}` | {item.descricao} | `{item.tipo.value}` | "
            f"**{formatar_centavos_br(item.custo_centavos)}** | {part_str} |"
        )

    linhas.extend([
        "",
        "---",
        "",
        "## 4. Notas Metodológicas e Fundamentos",
        "",
        "1. **ABNT NBR 12721:2006**: Coeficientes de equivalência normativos para determinação do custo de construção em incorporações imobiliárias.",
        "2. **Art. 54 da Lei Federal 4.591/1964**: O CUB não inclui fundações especiais, elevadores, ar condicionado central, ligações definitivas de água/esgoto/energia, projetos, impostos, taxas e remuneração da incorporadora.",
        "3. **Zero Float**: Todos os cálculos são processados estritamente em inteiros (centavos e centésimos de metro quadrado) e frações exatas (`Fraction`).",
        "",
        "*LOFRANO TECNOLOGIA — Engenharia de Software e Projetos de Alta Confiabilidade.*",
    ])

    return "\n".join(linhas) + "\n"


def criar_pacote_zip_deterministico(
    caminho_zip: Union[str, Path],
    arquivos: List[tuple[str, bytes]],
) -> None:
    """Cria arquivo ZIP determinístico e bit-a-bit reprodutível com proteção contra sobrescrita."""
    caminho_p = Path(caminho_zip)
    if caminho_p.exists():
        raise CUBError(f"Arquivo de destino já existe: {caminho_p}", ERR_ARQUIVO_EXISTENTE)

    fd = os.open(str(caminho_p), os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o644)
    with os.fdopen(fd, "wb") as f_out:
        with zipfile.ZipFile(f_out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            data_fixa = (2026, 11, 10, 0, 0, 0)
            for nome_arco, dados_bytes in sorted(arquivos, key=lambda x: x[0]):
                zinfo = zipfile.ZipInfo(filename=nome_arco, date_time=data_fixa)
                zinfo.compress_type = zipfile.ZIP_DEFLATED
                zinfo.external_attr = 0o644 << 16
                zf.writestr(zinfo, dados_bytes)
