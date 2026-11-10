"""Hierarquia de exceções e códigos de erro para orçamentação CUB e NBR 12721.

LOFRANO TECNOLOGIA.
"""

ERR_VALIDACAO = "ERR_VALIDACAO"
ERR_FLOAT_PROIBIDO = "ERR_FLOAT_PROIBIDO"
ERR_CHAVE_DUPLICADA = "ERR_CHAVE_DUPLICADA"
ERR_BOM_PROIBIDO = "ERR_BOM_PROIBIDO"
ERR_PROFUNDIDADE_EXCEDIDA = "ERR_PROFUNDIDADE_EXCEDIDA"
ERR_JSON_INVALIDO = "ERR_JSON_INVALIDO"
ERR_ARQUIVO_EXISTENTE = "ERR_ARQUIVO_EXISTENTE"
ERR_TIPOLOGIA_INVALIDA = "ERR_TIPOLOGIA_INVALIDA"
ERR_TIPO_AREA_INVALIDO = "ERR_TIPO_AREA_INVALIDO"


class CUBError(Exception):
    """Exceção base para orçamentação da construção civil e NBR 12721."""

    def __init__(self, mensagem: str, codigo: str = "ERR_GENERICO") -> None:
        super().__init__(mensagem)
        self.codigo = codigo
        self.mensagem = mensagem

    def __str__(self) -> str:
        return f"[{self.codigo}] {self.mensagem}"


class ErroValidacao(CUBError):
    """Lançada quando dados do projeto violam restrições técnicas ou regulamentares."""

    def __init__(self, mensagem: str, codigo: str = ERR_VALIDACAO) -> None:
        super().__init__(mensagem, codigo)


class ErroCodec(CUBError):
    """Lançada quando a decodificação ou serialização canônica do JSON falha."""

    def __init__(self, mensagem: str, codigo: str = ERR_JSON_INVALIDO) -> None:
        super().__init__(mensagem, codigo)
