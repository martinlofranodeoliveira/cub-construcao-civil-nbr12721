"""Codec JSON canônico e determinístico para projetos NBR 12721 e orçamentos CUB.

LOFRANO TECNOLOGIA.
"""

from fractions import Fraction
import json
from pathlib import Path
from typing import Any, Dict, List, Union

from .calculator import OrcamentoGlobalResultado
from .domain import DivisaoAreaEntrada, ItemNaoInclusoEntrada, ProjetoEmpreendimentoEntrada
from .errors import (
    ERR_BOM_PROIBIDO,
    ERR_CHAVE_DUPLICADA,
    ERR_FLOAT_PROIBIDO,
    ERR_JSON_INVALIDO,
    ERR_PROFUNDIDADE_EXCEDIDA,
    ERR_TIPO_AREA_INVALIDO,
    ERR_TIPOLOGIA_INVALIDA,
    ErroCodec,
)
from .tabelas_nbr12721 import (
    TipoDivisaoArea,
    TipoItemNaoIncluso,
    TipologiaPadrao,
    formatar_area_m2,
    formatar_centavos_br,
    formatar_fracao_pct,
)

LIMITE_PROFUNDIDADE_MAXIMA = 32


def _verificar_profundidade(obj: Any, nivel: int = 0) -> None:
    if nivel > LIMITE_PROFUNDIDADE_MAXIMA:
        raise ErroCodec(
            f"Profundidade de aninhamento excedeu o limite máximo de {LIMITE_PROFUNDIDADE_MAXIMA}.",
            ERR_PROFUNDIDADE_EXCEDIDA,
        )
    if isinstance(obj, dict):
        for v in obj.values():
            _verificar_profundidade(v, nivel + 1)
    elif isinstance(obj, list):
        for item in obj:
            _verificar_profundidade(item, nivel + 1)


def _verificar_sem_float(obj: Any) -> None:
    if isinstance(obj, float):
        raise ErroCodec("Tentativa de serializar float detectada.", ERR_FLOAT_PROIBIDO)
    if isinstance(obj, dict):
        for v in obj.values():
            _verificar_sem_float(v)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            _verificar_sem_float(item)


def _object_pairs_sem_duplicadas(pairs: List[tuple]) -> Dict[str, Any]:
    res: Dict[str, Any] = {}
    for k, v in pairs:
        if k in res:
            raise ErroCodec(f"Chave duplicada encontrada no JSON: '{k}'.", ERR_CHAVE_DUPLICADA)
        res[k] = v
    return res


def _parse_float_proibido(s: str) -> None:
    raise ErroCodec(
        f"Uso de ponto flutuante (float) é proibido pelo padrão de integridade: '{s}'. "
        "Utilize inteiros em centavos para valores monetários e inteiros em centésimos de m² para áreas.",
        ERR_FLOAT_PROIBIDO,
    )


def decodificar_json_canonico(texto_ou_bytes: Union[str, bytes]) -> Any:
    """Decodifica JSON sob regras canônicas restritas."""
    if isinstance(texto_ou_bytes, bytes):
        if texto_ou_bytes.startswith(b"\xef\xbb\xbf"):
            raise ErroCodec("Byte Order Mark (BOM) UTF-8 detectado e proibido.", ERR_BOM_PROIBIDO)
        try:
            texto = texto_ou_bytes.decode("utf-8")
        except UnicodeDecodeError as e:
            raise ErroCodec(f"Erro na decodificação UTF-8: {e}", ERR_JSON_INVALIDO)
    else:
        if texto_ou_bytes.startswith("\ufeff"):
            raise ErroCodec("Byte Order Mark (BOM) UTF-8 detectado e proibido.", ERR_BOM_PROIBIDO)
        texto = texto_ou_bytes

    try:
        dados = json.loads(
            texto,
            object_pairs_hook=_object_pairs_sem_duplicadas,
            parse_float=_parse_float_proibido,
        )
    except json.JSONDecodeError as e:
        raise ErroCodec(f"Sintaxe JSON inválida: {e}", ERR_JSON_INVALIDO)

    _verificar_profundidade(dados)
    return dados


def serializar_json_canonico(obj: Any) -> str:
    """Serializa estruturas para JSON canônico determinístico com indentação 2."""
    _verificar_sem_float(obj)

    def _converter(o: Any) -> Any:
        if isinstance(o, Fraction):
            return {"num": o.numerator, "den": o.denominator}
        if isinstance(o, float):
            raise ErroCodec("Tentativa de serializar float detectada.", ERR_FLOAT_PROIBIDO)
        raise TypeError(f"Objeto do tipo {type(o)} não é serializável.")

    return json.dumps(
        obj,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
        default=_converter,
    ) + "\n"


def carregar_projeto(caminho: Union[str, Path]) -> ProjetoEmpreendimentoEntrada:
    """Carrega e valida um projeto de empreendimento a partir de arquivo JSON."""
    caminho_p = Path(caminho)
    if not caminho_p.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    dados = decodificar_json_canonico(caminho_p.read_bytes())
    if not isinstance(dados, dict):
        raise ErroCodec("O nó raiz deve ser um objeto JSON.", ERR_JSON_INVALIDO)

    ident = dados.get("identificacao")
    loc = dados.get("localizacao")
    tipologia_str = dados.get("tipologia")
    mes_ano = dados.get("mes_ano_referencia")
    sinduscon = dados.get("sinduscon_estado")
    valor_cub = dados.get("valor_cub_m2_centavos")
    deson = dados.get("desoneracao_folha", False)
    areas_brutas = dados.get("areas")
    itens_brutos = dados.get("itens_nao_inclusos", [])

    if not isinstance(ident, str) or not ident.strip():
        raise ErroCodec("Campo 'identificacao' é obrigatório.", ERR_JSON_INVALIDO)
    if not isinstance(loc, str) or not loc.strip():
        raise ErroCodec("Campo 'localizacao' é obrigatório.", ERR_JSON_INVALIDO)
    if not isinstance(mes_ano, str) or not mes_ano.strip():
        raise ErroCodec("Campo 'mes_ano_referencia' é obrigatório.", ERR_JSON_INVALIDO)
    if not isinstance(sinduscon, str) or not sinduscon.strip():
        raise ErroCodec("Campo 'sinduscon_estado' é obrigatório.", ERR_JSON_INVALIDO)
    if not isinstance(valor_cub, int):
        raise ErroCodec("Campo 'valor_cub_m2_centavos' deve ser um inteiro em centavos.", ERR_JSON_INVALIDO)
    if not isinstance(deson, bool):
        raise ErroCodec("Campo 'desoneracao_folha' deve ser booleano.", ERR_JSON_INVALIDO)
    if not isinstance(areas_brutas, list):
        raise ErroCodec("Campo 'areas' deve ser uma lista.", ERR_JSON_INVALIDO)
    if not isinstance(itens_brutos, list):
        raise ErroCodec("Campo 'itens_nao_inclusos' deve ser uma lista.", ERR_JSON_INVALIDO)

    try:
        tipologia = TipologiaPadrao(tipologia_str)
    except ValueError:
        raise ErroCodec(f"Tipologia CUB inválida: '{tipologia_str}'.", ERR_TIPOLOGIA_INVALIDA)

    areas_lista: List[DivisaoAreaEntrada] = []
    for idx, a in enumerate(areas_brutas):
        if not isinstance(a, dict):
            raise ErroCodec(f"Área no índice {idx} deve ser um objeto JSON.", ERR_JSON_INVALIDO)

        cod = a.get("codigo")
        desc = a.get("descricao")
        tipo_area_str = a.get("tipo_area")
        area_real = a.get("area_real_m2_centesimos")
        coef_n = a.get("coeficiente_customizado_num")
        coef_d = a.get("coeficiente_customizado_den")

        if not isinstance(cod, str) or not cod.strip():
            raise ErroCodec(f"Divisão de área no índice {idx} possui 'codigo' inválido.", ERR_JSON_INVALIDO)
        if not isinstance(desc, str) or not desc.strip():
            raise ErroCodec(f"Divisão de área '{cod}' possui 'descricao' inválida.", ERR_JSON_INVALIDO)
        if not isinstance(area_real, int):
            raise ErroCodec(f"Divisão de área '{cod}' possui 'area_real_m2_centesimos' inválido.", ERR_JSON_INVALIDO)

        try:
            tipo_area = TipoDivisaoArea(tipo_area_str)
        except ValueError:
            raise ErroCodec(f"Tipo de divisão de área inválido: '{tipo_area_str}'.", ERR_TIPO_AREA_INVALIDO)

        areas_lista.append(
            DivisaoAreaEntrada(
                codigo=cod,
                descricao=desc,
                tipo_area=tipo_area,
                area_real_m2_centesimos=area_real,
                coeficiente_customizado_num=coef_n,
                coeficiente_customizado_den=coef_d,
            )
        )

    itens_lista: List[ItemNaoInclusoEntrada] = []
    for idx, item in enumerate(itens_brutos):
        if not isinstance(item, dict):
            raise ErroCodec(f"Item adicional no índice {idx} deve ser um objeto JSON.", ERR_JSON_INVALIDO)

        cod = item.get("codigo")
        desc = item.get("descricao")
        tipo_item_str = item.get("tipo")
        custo = item.get("custo_centavos")

        if not isinstance(cod, str) or not cod.strip():
            raise ErroCodec(f"Item adicional no índice {idx} possui 'codigo' inválido.", ERR_JSON_INVALIDO)
        if not isinstance(desc, str) or not desc.strip():
            raise ErroCodec(f"Item adicional '{cod}' possui 'descricao' inválida.", ERR_JSON_INVALIDO)
        if not isinstance(custo, int):
            raise ErroCodec(f"Item adicional '{cod}' possui 'custo_centavos' inválido.", ERR_JSON_INVALIDO)

        try:
            tipo_item = TipoItemNaoIncluso(tipo_item_str)
        except ValueError:
            raise ErroCodec(f"Tipo de item adicional inválido: '{tipo_item_str}'.", ERR_JSON_INVALIDO)

        itens_lista.append(
            ItemNaoInclusoEntrada(
                codigo=cod,
                descricao=desc,
                tipo=tipo_item,
                custo_centavos=custo,
            )
        )

    return ProjetoEmpreendimentoEntrada(
        identificacao=ident,
        localizacao=loc,
        tipologia=tipologia,
        mes_ano_referencia=mes_ano,
        sinduscon_estado=sinduscon,
        valor_cub_m2_centavos=valor_cub,
        desoneracao_folha=deson,
        areas=areas_lista,
        itens_nao_inclusos=itens_lista,
    )


def orcamento_para_dict(orcamento: OrcamentoGlobalResultado) -> Dict[str, Any]:
    """Converte o resultado orçamentário em dicionário canônico determinístico."""
    areas_json = []
    for a in orcamento.areas:
        areas_json.append({
            "codigo": a.codigo,
            "descricao": a.descricao,
            "tipo_area": a.tipo_area.value,
            "area_real_m2_centesimos": a.area_real_m2_centesimos,
            "area_real_m2_formatada": formatar_area_m2(a.area_real_m2_centesimos),
            "coeficiente_equivalencia": f"{a.coeficiente_num}/{a.coeficiente_den}",
            "coeficiente_equivalencia_pct": formatar_fracao_pct(a.coeficiente_num, a.coeficiente_den),
            "area_equivalente_m2_centesimos": a.area_equivalente_m2_centesimos,
            "area_equivalente_m2_formatada": formatar_area_m2(a.area_equivalente_m2_centesimos),
            "participacao_area_real_pct": formatar_fracao_pct(a.participacao_area_real_pct_num, a.participacao_area_real_pct_den),
            "custo_atribuido_centavos": a.custo_atribuido_centavos,
            "custo_atribuido_br": formatar_centavos_br(a.custo_atribuido_centavos),
        })

    itens_json = []
    for item in orcamento.itens_adicionais:
        itens_json.append({
            "codigo": item.codigo,
            "descricao": item.descricao,
            "tipo": item.tipo.value,
            "custo_centavos": item.custo_centavos,
            "custo_br": formatar_centavos_br(item.custo_centavos),
            "participacao_adicional_pct": formatar_fracao_pct(item.participacao_adicional_num, item.participacao_adicional_den),
        })

    return {
        "identificacao": orcamento.identificacao,
        "localizacao": orcamento.localizacao,
        "tipologia": orcamento.tipologia.value,
        "mes_ano_referencia": orcamento.mes_ano_referencia,
        "sinduscon_estado": orcamento.sinduscon_estado,
        "desoneracao_folha": orcamento.desoneracao_folha,
        "valor_cub_m2_centavos": orcamento.valor_cub_m2_centavos,
        "valor_cub_m2_br": formatar_centavos_br(orcamento.valor_cub_m2_centavos),
        "totais_areas": {
            "area_real_total_centesimos": orcamento.area_real_total_centesimos,
            "area_real_total_m2": formatar_area_m2(orcamento.area_real_total_centesimos),
            "area_equivalente_total_centesimos": orcamento.area_equivalente_total_centesimos,
            "area_equivalente_total_m2": formatar_area_m2(orcamento.area_equivalente_total_centesimos),
            "fator_equivalencia_global": formatar_fracao_pct(orcamento.fator_equivalencia_global_num, orcamento.fator_equivalencia_global_den),
        },
        "totais_custos": {
            "custo_base_cub_centavos": orcamento.custo_base_cub_centavos,
            "custo_base_cub_br": formatar_centavos_br(orcamento.custo_base_cub_centavos),
            "custo_itens_adicionais_centavos": orcamento.custo_itens_adicionais_centavos,
            "custo_itens_adicionais_br": formatar_centavos_br(orcamento.custo_itens_adicionais_centavos),
            "custo_global_construcao_centavos": orcamento.custo_global_construcao_centavos,
            "custo_global_construcao_br": formatar_centavos_br(orcamento.custo_global_construcao_centavos),
            "custo_m2_area_real_centavos": orcamento.custo_m2_area_real_centavos,
            "custo_m2_area_real_br": formatar_centavos_br(orcamento.custo_m2_area_real_centavos),
            "custo_m2_area_equivalente_centavos": orcamento.custo_m2_area_equivalente_centavos,
            "custo_m2_area_equivalente_br": formatar_centavos_br(orcamento.custo_m2_area_equivalente_centavos),
        },
        "areas": areas_json,
        "itens_adicionais": itens_json,
    }
