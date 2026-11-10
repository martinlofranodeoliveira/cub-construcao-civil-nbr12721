"""cub_construcao_civil — Cálculo determinístico de Área Equivalente NBR 12721 e Orçamento CUB.

LOFRANO TECNOLOGIA.
"""

from .calculator import (
    DivisaoAreaCalculada,
    ItemNaoInclusoCalculado,
    OrcamentoGlobalResultado,
    calcular_area_equivalente,
    calcular_orcamento_global,
    divisao_teto,
)
from .codecs import carregar_projeto, decodificar_json_canonico, orcamento_para_dict, serializar_json_canonico
from .domain import DivisaoAreaEntrada, ItemNaoInclusoEntrada, ProjetoEmpreendimentoEntrada
from .errors import CUBError, ErroCodec, ErroValidacao
from .tabelas_nbr12721 import (
    COEFICIENTES_EQUIVALENCIA_NBR12721,
    TipoDivisaoArea,
    TipoItemNaoIncluso,
    TipologiaPadrao,
    formatar_area_m2,
    formatar_centavos_br,
    formatar_fracao_pct,
)

__version__ = "1.0.0"
__author__ = "Martin Lofrano"

__all__ = [
    "__version__",
    "COEFICIENTES_EQUIVALENCIA_NBR12721",
    "CUBError",
    "DivisaoAreaCalculada",
    "DivisaoAreaEntrada",
    "ErroCodec",
    "ErroValidacao",
    "ItemNaoInclusoCalculado",
    "ItemNaoInclusoEntrada",
    "OrcamentoGlobalResultado",
    "ProjetoEmpreendimentoEntrada",
    "TipoDivisaoArea",
    "TipoItemNaoIncluso",
    "TipologiaPadrao",
    "calcular_area_equivalente",
    "calcular_orcamento_global",
    "carregar_projeto",
    "decodificar_json_canonico",
    "divisao_teto",
    "formatar_area_m2",
    "formatar_centavos_br",
    "formatar_fracao_pct",
    "orcamento_para_dict",
    "serializar_json_canonico",
]
