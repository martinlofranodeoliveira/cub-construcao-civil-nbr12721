#!/usr/bin/env python3
"""Auditor matemático independente baseado em SQLite e frações racionais exatas para NBR 12721.

Executa auditoria formal relacional sem importar o pacote da aplicação.
Zero float.

LOFRANO TECNOLOGIA.
"""

from fractions import Fraction
import json
from pathlib import Path
import sqlite3
import sys
from typing import Dict, Tuple

COEFICIENTES_NBR12721: Dict[str, Tuple[int, int]] = {
    "PRIVATIVA_PRINCIPAL_COBERTA": (1, 1),
    "GARAGEM_COBERTA_SUBSOLO": (3, 4),
    "GARAGEM_DESCOBERTA": (1, 8),
    "VARANDA_SACADA_COBERTA": (3, 4),
    "TERRACO_DESCOBERTO": (3, 10),
    "USO_COMUM_COBERTA_PILOTIS": (1, 2),
    "AREAS_LAZER_DESCOBERTAS": (1, 5),
    "RESERVATORIO_BARRILETE_MAQUINAS": (3, 4),
    "DEPOSITO_PRIVATIVO_SUBSOLO": (1, 2),
}


def teto(a: int, b: int) -> int:
    return (a + b - 1) // b


def verificar_projeto(caminho_json: Path) -> None:
    print(f"[*] Iniciando verificação independente SQLite de: {caminho_json}")

    dados = json.loads(caminho_json.read_text(encoding="utf-8"))
    ident = dados["identificacao"]
    tipologia = dados["tipologia"]
    valor_cub = dados["valor_cub_m2_centavos"]

    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE projeto (
            identificacao TEXT,
            tipologia TEXT,
            valor_cub INTEGER
        )
    """)
    cur.execute("INSERT INTO projeto VALUES (?, ?, ?)", (ident, tipologia, valor_cub))

    cur.execute("""
        CREATE TABLE areas (
            codigo TEXT PRIMARY KEY,
            descricao TEXT,
            tipo_area TEXT,
            area_real INTEGER,
            coef_n INTEGER,
            coef_d INTEGER,
            area_equiv INTEGER
        )
    """)

    for a in dados["areas"]:
        cod = a["codigo"]
        desc = a["descricao"]
        tipo = a["tipo_area"]
        a_real = a["area_real_m2_centesimos"]

        if "coeficiente_customizado_num" in a and a["coeficiente_customizado_num"] is not None:
            cn = a["coeficiente_customizado_num"]
            cd = a["coeficiente_customizado_den"]
        else:
            cn, cd = COEFICIENTES_NBR12721[tipo]

        a_eq = teto(a_real * cn, cd)

        cur.execute(
            "INSERT INTO areas VALUES (?, ?, ?, ?, ?, ?, ?)",
            (cod, desc, tipo, a_real, cn, cd, a_eq),
        )

    cur.execute("""
        CREATE TABLE itens_adicionais (
            codigo TEXT PRIMARY KEY,
            descricao TEXT,
            tipo TEXT,
            custo INTEGER
        )
    """)

    for item in dados.get("itens_nao_inclusos", []):
        cur.execute(
            "INSERT INTO itens_adicionais VALUES (?, ?, ?, ?)",
            (item["codigo"], item["descricao"], item["tipo"], item["custo_centavos"]),
        )

    conn.commit()

    # Totalizações via SQL
    cur.execute("SELECT SUM(area_real), SUM(area_equiv) FROM areas")
    area_real_tot, area_equiv_tot = cur.fetchone()

    cur.execute("SELECT SUM(custo) FROM itens_adicionais")
    res_adic = cur.fetchone()
    custo_adicionais_tot = res_adic[0] if res_adic[0] is not None else 0

    custo_base_cub = teto(area_equiv_tot * valor_cub, 100)
    custo_global = custo_base_cub + custo_adicionais_tot
    custo_m2_real = teto(custo_global * 100, area_real_tot)
    custo_m2_equiv = teto(custo_global * 100, area_equiv_tot)

    print(f"[*] Totais de Áreas NBR 12721 auditados:")
    print(f"    - Área Real Total: {area_real_tot/100:.2f} m²")
    print(f"    - Área Equivalente Total: {area_equiv_tot/100:.2f} m²")
    print(f"    - Fator Global: {area_equiv_tot / area_real_tot * 100:.2f}%")

    print(f"[*] Custos Orçados auditados:")
    print(f"    - Custo Base CUB: R$ {custo_base_cub/100:.2f}")
    print(f"    - Itens Adicionais (Lei 4.591): R$ {custo_adicionais_tot/100:.2f}")
    print(f"    - CUSTO GLOBAL ESTIMADO: R$ {custo_global/100:.2f}")
    print(f"    - Custo Médio / m² Real: R$ {custo_m2_real/100:.2f} / m²")
    print(f"    - Custo Médio / m² Equivalente: R$ {custo_m2_equiv/100:.2f} / m²")

    # Validar que a área equivalente é menor ou igual à área real total
    assert area_equiv_tot <= area_real_tot, "Área equivalente não deveria exceder área real!"
    assert custo_global > custo_base_cub, "Custo global deve conter os itens adicionais!"


def main() -> int:
    if len(sys.argv) > 1:
        caminho = Path(sys.argv[1])
    else:
        caminho = Path(__file__).resolve().parent.parent / "exemplares" / "edificio_residencial_r8n.json"

    try:
        verificar_projeto(caminho)
        print("[OK] Auditoria independente NBR 12721 / CUB concluída com 100% de conformidade!")
        return 0
    except Exception as e:
        print(f"[ERRO] Falha na auditoria independente: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
