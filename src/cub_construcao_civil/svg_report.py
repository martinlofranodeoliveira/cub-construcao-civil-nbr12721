"""Gerador de painel analítico SVG vetorial (1440x900) para áreas equivalentes NBR 12721 e CUB.

LOFRANO TECNOLOGIA.
"""

import html
from typing import List

from .calculator import OrcamentoGlobalResultado
from .tabelas_nbr12721 import formatar_area_m2, formatar_centavos_br, formatar_fracao_pct


def gerar_painel_svg(orcamento: OrcamentoGlobalResultado) -> str:
    """Gera visualização SVG vetorial em 1440x900 do orçamento da obra e áreas equivalentes."""
    w = 1440
    h = 900

    custo_global_str = formatar_centavos_br(orcamento.custo_global_construcao_centavos)
    custo_cub_str = formatar_centavos_br(orcamento.custo_base_cub_centavos)
    custo_adic_str = formatar_centavos_br(orcamento.custo_itens_adicionais_centavos)
    cub_unit_str = formatar_centavos_br(orcamento.valor_cub_m2_centavos)
    area_real_str = formatar_area_m2(orcamento.area_real_total_centesimos)
    area_eq_str = formatar_area_m2(orcamento.area_equivalente_total_centesimos)
    fator_str = formatar_fracao_pct(orcamento.fator_equivalencia_global_num, orcamento.fator_equivalencia_global_den)
    custo_m2_real_str = formatar_centavos_br(orcamento.custo_m2_area_real_centavos)

    # Cores por tipo de área
    cores_tipo = {
        "PRIVATIVA_PRINCIPAL_COBERTA": "#38bdf8",
        "GARAGEM_COBERTA_SUBSOLO": "#818cf8",
        "GARAGEM_DESCOBERTA": "#64748b",
        "VARANDA_SACADA_COBERTA": "#f59e0b",
        "TERRACO_DESCOBERTO": "#fb923c",
        "USO_COMUM_COBERTA_PILOTIS": "#10b981",
        "AREAS_LAZER_DESCOBERTAS": "#34d399",
        "RESERVATORIO_BARRILETE_MAQUINAS": "#cbd5e1",
        "DEPOSITO_PRIVATIVO_SUBSOLO": "#a78bfa",
    }

    # Gráfico de barras horizontais: Área Real vs Área Equivalente por compartimento
    linhas_areas_svg: List[str] = []
    y_start = 250
    row_h = 58
    max_area_p = max((a.area_real_m2_centesimos for a in orcamento.areas), default=100)

    for idx, a in enumerate(orcamento.areas[:8]):
        curr_y = y_start + (idx * row_h)
        cor = cores_tipo.get(a.tipo_area.value, "#38bdf8")

        # Larguras proporcionais para a barra de área real e equivalente
        bar_w_max = 240
        w_real = max(4, min(bar_w_max, (a.area_real_m2_centesimos * bar_w_max) // max_area_p))
        w_equiv = max(4, min(bar_w_max, (a.area_equivalente_m2_centesimos * bar_w_max) // max_area_p))

        coef_str = formatar_fracao_pct(a.coeficiente_num, a.coeficiente_den)

        linhas_areas_svg.append(f"""
          <g transform="translate(60, {curr_y})">
            <rect width="640" height="50" rx="6" fill="#1e293b" fill-opacity="0.5" stroke="#334155" stroke-width="1" />
            <rect width="4" height="50" rx="2" fill="{cor}" />

            <!-- Descrição e Código -->
            <text x="16" y="22" font-family="sans-serif" font-size="12" font-weight="700" fill="#f8fafc">
              {html.escape(a.codigo)} · {html.escape(a.descricao[:28])}
            </text>
            <text x="16" y="38" font-family="sans-serif" font-size="10" fill="#94a3b8">
              {a.tipo_area.value} · Coef: {coef_str}
            </text>

            <!-- Barras Real vs Equivalente -->
            <g transform="translate(300, 10)">
              <!-- Barra Real -->
              <rect x="0" y="2" width="{w_real}" height="10" rx="2" fill="#475569" />
              <text x="{bar_w_max + 10}" y="11" font-family="sans-serif" font-size="10" font-weight="600" fill="#cbd5e1">
                Real: {formatar_area_m2(a.area_real_m2_centesimos)}
              </text>
              <!-- Barra Equivalente -->
              <rect x="0" y="18" width="{w_equiv}" height="10" rx="2" fill="{cor}" />
              <text x="{bar_w_max + 10}" y="27" font-family="sans-serif" font-size="10" font-weight="700" fill="{cor}">
                Equiv: {formatar_area_m2(a.area_equivalente_m2_centesimos)}
              </text>
            </g>
          </g>
        """)

    # Tabela de Itens Adicionais (lado direito)
    linhas_itens_svg: List[str] = []
    iy_start = 450
    i_row_h = 52
    for idx, item in enumerate(orcamento.itens_adicionais[:6]):
        curr_iy = iy_start + (idx * i_row_h)
        part_str = formatar_fracao_pct(item.participacao_adicional_num, item.participacao_adicional_den)
        linhas_itens_svg.append(f"""
          <g transform="translate(740, {curr_iy})">
            <rect width="640" height="44" rx="6" fill="#1e293b" fill-opacity="0.6" stroke="#334155" stroke-width="1" />
            <text x="16" y="22" font-family="sans-serif" font-size="12" font-weight="700" fill="#f8fafc">
              {html.escape(item.codigo)} · {html.escape(item.descricao[:32])}
            </text>
            <text x="16" y="36" font-family="sans-serif" font-size="10" fill="#94a3b8">
              {item.tipo.value}
            </text>

            <text x="450" y="26" font-family="sans-serif" font-size="13" font-weight="800" fill="#f59e0b">
              {formatar_centavos_br(item.custo_centavos)}
            </text>
            <text x="560" y="26" font-family="sans-serif" font-size="11" fill="#64748b">
              ({part_str})
            </text>
          </g>
        """)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
  <defs>
    <linearGradient id="bgGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#090d16" />
      <stop offset="100%" stop-color="#0f172a" />
    </linearGradient>
  </defs>

  <rect width="{w}" height="{h}" fill="url(#bgGrad)" />

  <!-- Cabeçalho -->
  <g transform="translate(60, 40)">
    <text x="0" y="30" font-family="sans-serif" font-size="24" font-weight="800" fill="#f8fafc">
      {html.escape(orcamento.identificacao)}
    </text>
    <text x="0" y="54" font-family="sans-serif" font-size="13" font-weight="500" fill="#94a3b8">
      Custo Global de Construção (NBR 12721) · {html.escape(orcamento.localizacao)} · Tipologia: {orcamento.tipologia.value} · {orcamento.sinduscon_estado} ({orcamento.mes_ano_referencia})
    </text>
  </g>

  <!-- 4 Cards Superiores Executivos -->
  <g transform="translate(60, 115)">
    <!-- Card 1: Custo Global -->
    <g transform="translate(0, 0)">
      <rect width="310" height="95" rx="8" fill="#1e293b" stroke="#334155" stroke-width="1" />
      <rect width="310" height="4" rx="2" fill="#10b981" />
      <text x="16" y="24" font-family="sans-serif" font-size="11" font-weight="700" fill="#94a3b8">CUSTO GLOBAL ESTIMADO</text>
      <text x="16" y="56" font-family="sans-serif" font-size="22" font-weight="800" fill="#10b981">{custo_global_str}</text>
      <text x="16" y="78" font-family="sans-serif" font-size="11" fill="#cbd5e1">CUB + Serviços Adicionais</text>
    </g>

    <!-- Card 2: Custo Base CUB -->
    <g transform="translate(330, 0)">
      <rect width="310" height="95" rx="8" fill="#1e293b" stroke="#334155" stroke-width="1" />
      <rect width="310" height="4" rx="2" fill="#38bdf8" />
      <text x="16" y="24" font-family="sans-serif" font-size="11" font-weight="700" fill="#94a3b8">CUSTO BASE CUB ({orcamento.tipologia.value})</text>
      <text x="16" y="56" font-family="sans-serif" font-size="22" font-weight="800" fill="#38bdf8">{custo_cub_str}</text>
      <text x="16" y="78" font-family="sans-serif" font-size="11" fill="#cbd5e1">Valor CUB/m²: {cub_unit_str}</text>
    </g>

    <!-- Card 3: Áreas Reais e Equivalentes -->
    <g transform="translate(660, 0)">
      <rect width="310" height="95" rx="8" fill="#1e293b" stroke="#334155" stroke-width="1" />
      <rect width="310" height="4" rx="2" fill="#a855f7" />
      <text x="16" y="24" font-family="sans-serif" font-size="11" font-weight="700" fill="#94a3b8">ÁREA EQUIVALENTE (NBR 12721)</text>
      <text x="16" y="56" font-family="sans-serif" font-size="22" font-weight="800" fill="#a855f7">{area_eq_str}</text>
      <text x="16" y="78" font-family="sans-serif" font-size="11" fill="#cbd5e1">Área Real: {area_real_str} ({fator_str})</text>
    </g>

    <!-- Card 4: Custo Médio por m² Real -->
    <g transform="translate(990, 0)">
      <rect width="330" height="95" rx="8" fill="#1e293b" stroke="#334155" stroke-width="1" />
      <rect width="330" height="4" rx="2" fill="#f59e0b" />
      <text x="16" y="24" font-family="sans-serif" font-size="11" font-weight="700" fill="#94a3b8">CUSTO MÉDIO / M² REAL</text>
      <text x="16" y="56" font-family="sans-serif" font-size="22" font-weight="800" fill="#f59e0b">{custo_m2_real_str} / m²</text>
      <text x="16" y="78" font-family="sans-serif" font-size="11" fill="#cbd5e1">Adicionais: {custo_adic_str}</text>
    </g>
  </g>

  <!-- Título Esquerdo: Quadro de Áreas NBR 12721 -->
  <g transform="translate(60, 230)">
    <text x="0" y="10" font-family="sans-serif" font-size="13" font-weight="800" fill="#f8fafc">
      Quadro II NBR 12721 · Comparativo de Áreas Reais vs. Equivalentes em Custo
    </text>
  </g>

  <!-- Linhas de Áreas (Esquerda) -->
  {"".join(linhas_areas_svg)}

  <!-- Painel Direito: Serviços Adicionais Não Inclusos (Lei 4.591/64) -->
  <g transform="translate(740, 230)">
    <!-- Card Resumo CUB vs Adicionais -->
    <rect width="640" height="175" rx="8" fill="#1e293b" stroke="#334155" stroke-width="1" />
    <text x="20" y="28" font-family="sans-serif" font-size="13" font-weight="800" fill="#f8fafc">
      Composição do Custo Global de Construção
    </text>
    <text x="20" y="48" font-family="sans-serif" font-size="11" fill="#94a3b8">
      Discriminação entre o padrão normatizado CUB e os serviços complementares de infraestrutura.
    </text>

    <!-- Barra de Composição CUB vs Adicionais -->
    <g transform="translate(20, 70)">
      <rect width="600" height="24" rx="4" fill="#0f172a" />
      <rect width="{(orcamento.custo_base_cub_centavos * 600) // orcamento.custo_global_construcao_centavos}" height="24" rx="4" fill="#38bdf8" />
      <rect x="{(orcamento.custo_base_cub_centavos * 600) // orcamento.custo_global_construcao_centavos}" y="0" width="{(orcamento.custo_itens_adicionais_centavos * 600) // orcamento.custo_global_construcao_centavos}" height="24" rx="4" fill="#f59e0b" />
    </g>

    <g transform="translate(20, 120)">
      <circle cx="6" cy="6" r="6" fill="#38bdf8" />
      <text x="20" y="10" font-family="sans-serif" font-size="11" font-weight="600" fill="#cbd5e1">
        CUB Básico: {custo_cub_str} ({formatar_fracao_pct(orcamento.custo_base_cub_centavos, orcamento.custo_global_construcao_centavos)})
      </text>

      <circle cx="320" cy="6" r="6" fill="#f59e0b" />
      <text x="334" y="10" font-family="sans-serif" font-size="11" font-weight="600" fill="#cbd5e1">
        Adicionais (Lei 4.591): {custo_adic_str} ({formatar_fracao_pct(orcamento.custo_itens_adicionais_centavos, orcamento.custo_global_construcao_centavos)})
      </text>
    </g>

    <text x="20" y="152" font-family="sans-serif" font-size="11" fill="#64748b">
      Fundações profundas, elevadores, BDI, urbanização e projetos complementares.
    </text>
  </g>

  <!-- Título dos Serviços Adicionais -->
  <g transform="translate(740, 430)">
    <text x="0" y="10" font-family="sans-serif" font-size="13" font-weight="800" fill="#f8fafc">
      Itens Não Inclusos no CUB (Art. 54 da Lei 4.591/64)
    </text>
  </g>

  <!-- Linhas dos Itens Adicionais -->
  {"".join(linhas_itens_svg)}

  <!-- Rodapé -->
  <g transform="translate(60, 860)">
    <text x="0" y="15" font-family="sans-serif" font-size="11" fill="#64748b">
      Conformidade ABNT NBR 12721:2006 · Lei Federal nº 4.591/1964 · Aritmética Exata (Zero Float) · LOFRANO TECNOLOGIA
    </text>
  </g>
</svg>
"""
    return svg
