#!/usr/bin/env python3
"""
Gera as instâncias OML dos bolsistas PBPG a partir do Tabelão Financeiro do AgilFAP.

Transformação determinística: lê a planilha, agrupa e emite OML. Sem rede e sem LLM,
para que o resultado seja reproduzível e verificável pelo raciocinador.

Princípio de projeto: NÃO INVENTAR DADO. Atributo sem fonte na planilha é omitido
(em OWL, ausência significa "desconhecido", não "inexistente") e reportado ao final,
em vez de preenchido com valor plausível.

Uso:
    python3 scripts/gerar_instancias_bolsistas.py --help
"""

import argparse
import csv
import datetime
import hashlib
import re
import sys
import unicodedata
from collections import defaultdict

# --------------------------------------------------------------------------
# Configuração de domínio
# --------------------------------------------------------------------------

MODALIDADE_PBPG = "IBPG"  # 36.162 linhas na planilha de 15/04/2026

IRI_BASE = "http://secti.pe.gov.br/indicador_cti"
PREFIXO_DESC = f"{IRI_BASE}/description/programas/programasFormacaoFixacaoTalentos/PBPG"

# Colunas do Tabelão efetivamente consumidas
COL = {
    "modalidade": "MODALIDADE",
    "num_edital": "Nº DO EDITAL",
    "nome_edital": "NOME DO EDITAL",
    "titulo_projeto": "TÍTULO DO PROJETO",
    "rd_exec": "INST.EXEC. (RD)",
    "inicio": "INÍCIO DE VIGÊNCIA",
    "termino": "TÉRMINO DE VIGÊNCIA",
    "beneficiario": "BENEFICIÁRIO",
    "cpf": "CPF BENEFICIÁRIO",
    "valor": "VALOR (R$)",
    "nivel": "NÍVEL DA MODALIDADE",
    "envio_tese": "DATA DE ENVIO DA DISSERTAÇÃO/TESE",
}

# Atributos do vocabulário sem fonte no Tabelão — omitidos e reportados
SEM_FONTE = [
    "bolsista:id_bolsa (não há código IBPG-* na planilha)",
    "bolsista:nm_status (ADIMPLENTE/INADIMPLENTE)",
    "bolsista:id_semestre_titulacao",
    "pessoa:an_nascimento",
    "pessoa:nm_pais_nacionalidade",
    "pessoa:nm_cidade_endereco",
    "pessoa:ds_url_cv_lattes",
    "projeto:nm_area_conhecimento (HUMANAS/EXATAS/SAÚDE)",
    "projeto:vl_area_prioritaria (SIM/NÃO)",
    "edital:dt_publicacao",
    "edital:vl_investimento",
]


# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------

def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", str(s))
                   if unicodedata.category(c) != "Mn")


def slug(s, maxlen=40):
    """Identificador OML seguro: sem acento, só alfanumérico e hífen."""
    s = sem_acento(s).upper()
    s = re.sub(r"[^A-Z0-9]+", "-", s).strip("-")
    return s[:maxlen]


def escapar(s):
    """Literal de string OML."""
    return str(s).replace("\\", "\\\\").replace('"', '\\"')


def texto(v):
    return "" if v is None else str(v).strip()


def data_br(v):
    """Normaliza para dd/mm/aaaa. Aceita datetime da planilha ou texto."""
    if v is None or v == "":
        return None
    if isinstance(v, (datetime.datetime, datetime.date)):
        return v.strftime("%d/%m/%Y")
    s = str(v).strip()
    m = re.match(r"^(\d{2})/(\d{2})/(\d{2})$", s)  # dd/mm/aa -> assume século 21
    if m:
        return f"{m.group(1)}/{m.group(2)}/20{m.group(3)}"
    return s if re.match(r"^\d{2}/\d{2}/\d{4}$", s) else None


def semestre(v):
    """Data -> 'AAAA.S'. Usado para o semestre de defesa."""
    d = data_br(v)
    if not d:
        return None
    dia, mes, ano = d.split("/")
    return f"{ano}.{1 if int(mes) <= 6 else 2}"


def para_decimal(v):
    if v is None or v == "":
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def normalizar_modalidade(nivel):
    """NÍVEL DA MODALIDADE do AgilFAP -> scalar `modalidade` do vocabulário.

    A planilha distingue Mestrado Acadêmico / Profissionalizante /
    Complementação CAPES; o vocabulário só tem MESTRADO e DOUTORADO.
    """
    n = sem_acento(texto(nivel)).upper()
    if "DOUTORADO" in n:
        return "DOUTORADO"
    if "MESTRADO" in n:
        return "MESTRADO"
    return None


def normalizar_rde(rd):
    """INST.EXEC. (RD) -> scalar `rde` do vocabulário (RMR / FORA RMR)."""
    r = sem_acento(texto(rd)).upper()
    if not r:
        return None
    return "RMR" if "METROPOLITANA" in r else "FORA RMR"


def pseudonimo(cpf):
    return hashlib.sha256(f"pbpg:{cpf}".encode()).hexdigest()[:11]


# --------------------------------------------------------------------------
# Leitura
# --------------------------------------------------------------------------

def ler_linhas(caminho, coluna_modalidade=MODALIDADE_PBPG):
    """Itera as linhas do PBPG como dicionários. Aceita .xlsx ou .csv."""
    if caminho.lower().endswith(".csv"):
        with open(caminho, encoding="utf-8-sig", newline="") as f:
            for reg in csv.DictReader(f):
                if texto(reg.get(COL["modalidade"])) == coluna_modalidade:
                    yield reg
        return

    import openpyxl
    ws = openpyxl.load_workbook(caminho, read_only=True, data_only=True).active
    it = ws.iter_rows(values_only=True)
    hdr = [texto(c) for c in next(it)]
    faltando = [c for c in COL.values() if c not in hdr]
    if faltando:
        sys.exit(f"ERRO: colunas ausentes na planilha: {faltando}")
    idx = {h: i for i, h in enumerate(hdr)}
    for row in it:
        if texto(row[idx[COL["modalidade"]]]) == coluna_modalidade:
            yield {h: row[idx[h]] for h in hdr}


# --------------------------------------------------------------------------
# Agregação
# --------------------------------------------------------------------------

def agregar(linhas, filtro_edital=None):
    """Agrupa por (CPF, edital) — uma bolsa por grupo.

    O Tabelão é financeiro: uma linha por parcela/exercício. O valor da bolsa é a
    soma das parcelas; a vigência vai do menor início ao maior término.
    """
    bolsas = {}
    editais = {}
    descartes = defaultdict(int)

    for reg in linhas:
        cpf = re.sub(r"\D", "", texto(reg.get(COL["cpf"])))
        nome = texto(reg.get(COL["beneficiario"]))
        num_ed = texto(reg.get(COL["num_edital"]))
        nome_ed = texto(reg.get(COL["nome_edital"]))

        if not cpf or not nome:
            descartes["sem CPF ou sem nome do beneficiário"] += 1
            continue
        if filtro_edital and filtro_edital.upper() not in nome_ed.upper():
            continue
        if not nome_ed:
            descartes["sem edital"] += 1
            continue

        if num_ed:
            editais.setdefault(num_ed, nome_ed)

        chave = (cpf, nome_ed)
        b = bolsas.setdefault(chave, {
            "cpf": cpf, "nome": nome, "num_edital": num_ed, "nome_edital": nome_ed,
            "titulo": texto(reg.get(COL["titulo_projeto"])),
            "rd": texto(reg.get(COL["rd_exec"])),
            "valor": 0.0, "inicios": [], "terminos": [],
            "modalidades": set(), "envio_tese": None, "parcelas": 0,
        })
        b["valor"] += para_decimal(reg.get(COL["valor"]))
        b["parcelas"] += 1
        for campo, destino in (("inicio", "inicios"), ("termino", "terminos")):
            d = data_br(reg.get(COL[campo]))
            if d:
                b[destino].append(datetime.datetime.strptime(d, "%d/%m/%Y"))
        m = normalizar_modalidade(reg.get(COL["nivel"]))
        if m:
            b["modalidades"].add(m)
        env = data_br(reg.get(COL["envio_tese"]))
        if env and not b["envio_tese"]:
            b["envio_tese"] = env
        if not b["titulo"]:
            b["titulo"] = texto(reg.get(COL["titulo_projeto"]))

    return bolsas, editais, descartes


# --------------------------------------------------------------------------
# Emissão de OML
# --------------------------------------------------------------------------

CABECALHO = '''description <{prefixo}/{nome}#> as {nome} {{

\t// ARQUIVO GERADO por scripts/gerar_instancias_bolsistas.py .
\t// Fonte: {fonte}
\t// Gerado em: {quando}
\t// Bolsas: {n_bolsas} | Editais: {n_editais} | Projetos: {n_projetos}
\t//
\t// Convenções e aproximações desta geração:
\t//  - O Tabelão é financeiro (uma linha por parcela). vl_recebido é a SOMA das
\t//    parcelas; dt_inicio_bolsa e dt_fim_bolsa são o menor início e o maior término.
\t//  - O Tabelão não traz o código da bolsa (IBPG-*) nem o do projeto (APQ-*).
\t//    id_bolsa é omitido; o base:id do projeto é um substituto determinístico
\t//    derivado do título (prefixo PRJ-), estável entre execuções.
\t//  - id_semestre_defesa deriva de DATA DE ENVIO DA DISSERTAÇÃO/TESE.
\t//  - nm_modalidade colapsa os níveis do AgilFAP (Mestrado Acadêmico,
\t//    Profissionalizante, Complementação CAPES) em MESTRADO/DOUTORADO.
\t//  - nm_rde: RD com "METROPOLITANA" vira RMR; demais, FORA RMR.

\textends <{prefixo}/PBPG#> as PBPG
\tuses <{iri}/vocabulary/base#> as base
\tuses <{iri}/vocabulary/AvaliacaoProgramas/PBPG/bolsista#> as bolsista
\tuses <{iri}/vocabulary/AvaliacaoProgramas/PBPG/projeto#> as projeto
\tuses <{iri}/vocabulary/AvaliacaoProgramas/PBPG/edital#> as edital
\tuses <http://www.w3.org/2001/XMLSchema#> as xsd
'''


def gerar_oml(bolsas, editais, nome_modulo, fonte, pseudonimizar=False):
    linhas = []
    projetos = {}  # id -> (nome, rde, num_edital)

    # ---- identidade dos bolsistas -------------------------------------
    # Uma pessoa pode ter bolsa em mais de um edital, mas o vocabulário admite
    # uma bolsa por indivíduo (propriedades functional). Nesses casos emitimos
    # um indivíduo por bolsa, com IRI sufixada. Ver relatório.
    por_cpf = defaultdict(list)
    for (cpf, ed) in bolsas:
        por_cpf[cpf].append(ed)

    corpo = []
    for (cpf, nome_ed), b in sorted(bolsas.items()):
        # Sob pseudonimização o CPF real não pode aparecer nem no IRI da instância
        cpf_saida = pseudonimo(cpf) if pseudonimizar else cpf
        nome_pessoa = f"Bolsista {cpf_saida}" if pseudonimizar else b["nome"]

        ident = f"Bolsista-{cpf_saida}"
        if len(por_cpf[cpf]) > 1:
            ident = f"Bolsista-{cpf_saida}-{slug(nome_ed, 12)}"

        props = [f'\t\tbolsista:nr_cpf "{escapar(cpf_saida)}"',
                 f'\t\tbase:nome "{escapar(nome_pessoa)}"']

        if b["inicios"]:
            props.append(f'\t\tbolsista:dt_inicio_bolsa "{min(b["inicios"]).strftime("%d/%m/%Y")}"')
        if b["terminos"]:
            props.append(f'\t\tbolsista:dt_fim_bolsa "{max(b["terminos"]).strftime("%d/%m/%Y")}"')
        if b["valor"]:
            props.append(f'\t\tbolsista:vl_recebido "{b["valor"]:.2f}"^^xsd:double')
        if len(b["modalidades"]) == 1:
            props.append(f'\t\tbolsista:nm_modalidade "{next(iter(b["modalidades"]))}"')
        if b["envio_tese"]:
            s = semestre(b["envio_tese"])
            if s:
                props.append(f'\t\tbolsista:id_semestre_defesa "{s}"')

        if b["titulo"]:
            pid = "PRJ-" + hashlib.sha1(b["titulo"].encode()).hexdigest()[:12].upper()
            projetos.setdefault(pid, (b["titulo"], b["rd"], b["num_edital"]))
            props.append(f"\t\tbolsista:desenvolve Projeto-{pid}")

        corpo.append(f"\tinstance {ident} : bolsista:bolsista [\n" +
                     "\n".join(props) + "\n\t]")

    # ---- editais -------------------------------------------------------
    bloco_editais = []
    for num, nome_ed in sorted(editais.items()):
        bloco_editais.append(
            f"\tinstance Edital-{slug(num)} : edital:edital [\n"
            f'\t\tbase:id "{escapar(num)}"\n'
            f'\t\tbase:nome "{escapar(nome_ed)}"\n'
            f"\t\tedital:vinculadoA PBPG:PR1\n\t]")

    # ---- projetos ------------------------------------------------------
    bloco_projetos = []
    for pid, (titulo, rd, num_ed) in sorted(projetos.items()):
        p = [f'\t\tbase:id "{pid}"', f'\t\tbase:nome "{escapar(titulo)}"']
        rde = normalizar_rde(rd)
        if rde:
            p.append(f'\t\tprojeto:nm_rde "{rde}"')
        if num_ed:
            p.append(f"\t\tprojeto:submetidoA Edital-{slug(num_ed)}")
        bloco_projetos.append(f"\tinstance Projeto-{pid} : projeto:projeto [\n" +
                              "\n".join(p) + "\n\t]")

    cab = CABECALHO.format(
        prefixo=PREFIXO_DESC, iri=IRI_BASE, nome=nome_modulo, fonte=fonte,
        quando=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        n_bolsas=len(bolsas), n_editais=len(editais), n_projetos=len(projetos))

    linhas.append(cab)
    linhas.append("\n\t//" + "-" * 68 + "\n\t// EDITAIS\n\t//" + "-" * 68 + "\n")
    linhas.extend(bloco_editais)
    linhas.append("\n\t//" + "-" * 68 + "\n\t// PROJETOS\n\t//" + "-" * 68 + "\n")
    linhas.extend(bloco_projetos)
    linhas.append("\n\t//" + "-" * 68 + "\n\t// BOLSISTAS\n\t//" + "-" * 68 + "\n")
    linhas.extend(corpo)
    linhas.append("}\n")
    return "\n".join(linhas), projetos, por_cpf


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Gera instâncias OML dos bolsistas PBPG a partir do Tabelão AgilFAP.")
    ap.add_argument("--xlsx", required=True, help="Tabelão do AgilFAP (.xlsx ou .csv)")
    ap.add_argument("--saida", default="generated/bolsistas-PBPG.oml",
                    help="arquivo OML de saída (padrão: generated/bolsistas-PBPG.oml)")
    ap.add_argument("--modulo", default="bolsistas-PBPG",
                    help="nome do módulo OML (padrão: bolsistas-PBPG)")
    ap.add_argument("--edital", help="filtra por edital, ex.: 'PBPG 2023.1'")
    ap.add_argument("--limite", type=int, help="processa no máximo N bolsas (amostra)")
    ap.add_argument("--pseudonimizar", action="store_true",
                    help="substitui nome e CPF por pseudônimo estável (LGPD)")
    args = ap.parse_args()

    print(f"Lendo {args.xlsx} ...", file=sys.stderr)
    bolsas, editais, descartes = agregar(ler_linhas(args.xlsx), args.edital)

    if args.limite:
        bolsas = dict(sorted(bolsas.items())[:args.limite])
        usados = {b["num_edital"] for b in bolsas.values() if b["num_edital"]}
        editais = {k: v for k, v in editais.items() if k in usados}

    oml, projetos, por_cpf = gerar_oml(
        bolsas, editais, args.modulo, args.xlsx.split("/")[-1], args.pseudonimizar)

    import os
    os.makedirs(os.path.dirname(os.path.abspath(args.saida)), exist_ok=True)
    with open(args.saida, "w", encoding="utf-8") as f:
        f.write(oml)

    # ---- relatório -----------------------------------------------------
    multi = {c: e for c, e in por_cpf.items() if len(e) > 1}
    sem_modalidade = sum(1 for b in bolsas.values() if len(b["modalidades"]) != 1)
    sem_titulo = sum(1 for b in bolsas.values() if not b["titulo"])
    com_defesa = sum(1 for b in bolsas.values() if b["envio_tese"])

    print(f"\n{'='*70}\nRELATÓRIO\n{'='*70}")
    print(f"  Arquivo gerado ....... {args.saida}")
    print(f"  Bolsas ............... {len(bolsas):,}")
    print(f"  Pessoas distintas .... {len(por_cpf):,}")
    print(f"  Editais .............. {len(editais):,}")
    print(f"  Projetos ............. {len(projetos):,}")
    print(f"  Pseudonimizado ....... {'SIM' if args.pseudonimizar else 'NÃO (dado pessoal real)'}")

    print(f"\n  ATENÇÃO -- pessoas com bolsa em mais de um edital: {len(multi):,}")
    if multi:
        print("    O vocabulário admite uma bolsa por indivíduo (propriedades functional),")
        print("    então cada bolsa virou um indivíduo com IRI sufixada pelo edital.")
        print("    Isso duplica a pessoa e impede consultar sua trajetória (PA3.ME2/ME3).")
        for c, e in list(multi.items())[:3]:
            print(f"      {c}: {sorted(e)}")

    print(f"\n  Qualidade dos dados:")
    print(f"    bolsas sem modalidade única ... {sem_modalidade:,}")
    print(f"    bolsas sem título de projeto .. {sem_titulo:,}")
    print(f"    bolsas com data de defesa ..... {com_defesa:,}")
    for motivo, n in descartes.items():
        print(f"    descartadas ({motivo}): {n:,}")

    print(f"\n  Atributos do vocabulário SEM fonte no Tabelão (omitidos):")
    for a in SEM_FONTE:
        print(f"    - {a}")
    print()


if __name__ == "__main__":
    main()
