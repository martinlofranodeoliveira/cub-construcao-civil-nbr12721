"""Modelos de domínio imutáveis e tipados para orçamentação CUB e NBR 12721.

Todas as grandezas monetárias expressas em centavos inteiros (int),
todas as áreas em centésimos de m² (int) e coeficientes em frações racionais exatas.
Zero float.

LOFRANO TECNOLOGIA.
"""

from dataclasses import dataclass
from fractions import Fraction
from typing import List, Optional

from .errors import ERR_VALIDACAO, ErroValidacao
from .tabelas_nbr12721 import (
    COEFICIENTES_EQUIVALENCIA_NBR12721,
    TipoDivisaoArea,
    TipoItemNaoIncluso,
    TipologiaPadrao,
)


@dataclass(frozen=True)
class DivisaoAreaEntrada:
    """Compartimento ou setor de área da edificação para cálculo de equivalência."""

    codigo: str
    descricao: str
    tipo_area: TipoDivisaoArea
    area_real_m2_centesimos: int
    coeficiente_customizado_num: Optional[int] = None
    coeficiente_customizado_den: Optional[int] = None

    def __post_init__(self) -> None:
        if not self.codigo or not self.codigo.strip():
            raise ErroValidacao("Código da divisão de área não pode ser vazio.", ERR_VALIDACAO)
        if not self.descricao or not self.descricao.strip():
            raise ErroValidacao(f"Descrição da divisão '{self.codigo}' não pode ser vazia.", ERR_VALIDACAO)
        if self.area_real_m2_centesimos <= 0:
            raise ErroValidacao(
                f"Área real da divisão '{self.codigo}' deve ser maior que zero ({self.area_real_m2_centesimos} centésimos).",
                ERR_VALIDACAO,
            )
        if (self.coeficiente_customizado_num is not None) != (self.coeficiente_customizado_den is not None):
            raise ErroValidacao(
                f"Coeficiente customizado de '{self.codigo}' deve fornecer numerador e denominador conjuntamente.",
                ERR_VALIDACAO,
            )
        if self.coeficiente_customizado_den is not None and self.coeficiente_customizado_den <= 0:
            raise ErroValidacao(
                f"Denominador do coeficiente customizado de '{self.codigo}' deve ser positivo.",
                ERR_VALIDACAO,
            )
        if self.coeficiente_customizado_num is not None and self.coeficiente_customizado_num < 0:
            raise ErroValidacao(
                f"Numerador do coeficiente customizado de '{self.codigo}' não pode ser negativo.",
                ERR_VALIDACAO,
            )

    @property
    def coeficiente_equivalencia(self) -> Fraction:
        """Retorna a fração normativa padrão da NBR 12721 ou o coeficiente customizado informado."""
        if self.coeficiente_customizado_num is not None and self.coeficiente_customizado_den is not None:
            return Fraction(self.coeficiente_customizado_num, self.coeficiente_customizado_den)
        return COEFICIENTES_EQUIVALENCIA_NBR12721[self.tipo_area]


@dataclass(frozen=True)
class ItemNaoInclusoEntrada:
    """Item adicional não incluído no cálculo do CUB básico (Art. 54 da Lei 4.591/64)."""

    codigo: str
    descricao: str
    tipo: TipoItemNaoIncluso
    custo_centavos: int

    def __post_init__(self) -> None:
        if not self.codigo or not self.codigo.strip():
            raise ErroValidacao("Código do item adicional não pode ser vazio.", ERR_VALIDACAO)
        if not self.descricao or not self.descricao.strip():
            raise ErroValidacao(f"Descrição do item adicional '{self.codigo}' não pode ser vazia.", ERR_VALIDACAO)
        if self.custo_centavos < 0:
            raise ErroValidacao(
                f"Custo do item adicional '{self.codigo}' não pode ser negativo ({self.custo_centavos} centavos).",
                ERR_VALIDACAO,
            )


@dataclass(frozen=True)
class ProjetoEmpreendimentoEntrada:
    """Empreendimento completo com áreas, tipologia CUB e itens complementares."""

    identificacao: str
    localizacao: str
    tipologia: TipologiaPadrao
    mes_ano_referencia: str
    sinduscon_estado: str
    valor_cub_m2_centavos: int
    desoneracao_folha: bool
    areas: List[DivisaoAreaEntrada]
    itens_nao_inclusos: List[ItemNaoInclusoEntrada]

    def __post_init__(self) -> None:
        if not self.identificacao or not self.identificacao.strip():
            raise ErroValidacao("Identificação do empreendimento não pode ser vazia.", ERR_VALIDACAO)
        if not self.localizacao or not self.localizacao.strip():
            raise ErroValidacao("Localização do empreendimento não pode ser vazia.", ERR_VALIDACAO)
        if not self.mes_ano_referencia or not self.mes_ano_referencia.strip():
            raise ErroValidacao("Mês/ano de referência do CUB não pode ser vazio.", ERR_VALIDACAO)
        if not self.sinduscon_estado or not self.sinduscon_estado.strip():
            raise ErroValidacao("Entidade SINDUSCON do estado não pode ser vazia.", ERR_VALIDACAO)
        if self.valor_cub_m2_centavos <= 0:
            raise ErroValidacao(
                f"Valor do CUB/m² deve ser estritamente positivo ({self.valor_cub_m2_centavos} centavos).",
                ERR_VALIDACAO,
            )
        if not self.areas:
            raise ErroValidacao("Empreendimento deve possuir ao menos uma divisão de área.", ERR_VALIDACAO)

        # Checar unicidade de códigos de áreas
        cods_areas = set()
        for a in self.areas:
            cod = a.codigo.strip()
            if cod in cods_areas:
                raise ErroValidacao(f"Código de divisão de área duplicado: '{cod}'.", ERR_VALIDACAO)
            cods_areas.add(cod)

        # Checar unicidade de códigos de itens adicionais
        cods_itens = set()
        for item in self.itens_nao_inclusos:
            cod = item.codigo.strip()
            if cod in cods_itens:
                raise ErroValidacao(f"Código de item adicional duplicado: '{cod}'.", ERR_VALIDACAO)
            cods_itens.add(cod)
