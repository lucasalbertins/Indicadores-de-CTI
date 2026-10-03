#!/usr/bin/env python3
"""
Gera as descrições OML das métricas a partir de formulas.json.

O formulas.json traz a árvore da fórmula (operação OpenMath, argumentos,
posições e valores) numa forma tabular que mapeia 1:1 no vocabulário
DesignAvaliacao/formulas. Os demais atributos da métrica -- temFonte,
finalidade, valorAtual e valorMeta -- não estão no JSON e são lidos do
PA-PBPG.oml, casando pelo código da métrica (PA3.ME1_PBPG <-> "PA3.ME1 - PBPG").

Uso:
    python3 scripts/gerar_metricas_oml.py [--saida DIR] [--todas]

Por padrão gera apenas as métricas que ainda não têm arquivo em metricasPBPG/.
Com --todas gera também as já existentes, para conferência por diff.
"""

import argparse
import json
import os
import re
import unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORMULAS_JSON = os.path.join(os.path.dirname(os.path.dirname(RAIZ)), 'formulas.json')
BASE_DESC = 'src/oml/secti.pe.gov.br/indicador_cti/description'
PA_PBPG = os.path.join(RAIZ, BASE_DESC,
                       'programas/programasFormacaoFixacaoTalentos/PBPG/PA-PBPG.oml')
DIR_METRICAS = os.path.join(RAIZ, BASE_DESC,
                            'programas/programasFormacaoFixacaoTalentos/PBPG/metricasPBPG')
IRI_METRICAS = ('http://secti.pe.gov.br/indicador_cti/description/programas/'
                'programasFormacaoFixacaoTalentos/PBPG/metricasPBPG')
IRI_FONTES = 'http://secti.pe.gov.br/indicador_cti/description/fontesInformacao'

# Métricas já descritas à mão em metricasPBPG/, com o nome da instância que
# outras métricas usam para referenciá-las.
JA_EXISTENTES = {
    'PA1.ME1_PBPG': ('PA1.ME1', 'taxaTitulacao'),
    'PA1.ME2_PBPG': ('PA1.ME2', 'quantidadeTitulados'),
    'PA1.ME3_PBPG': ('PA1.ME3', 'taxaNaoTitulacao'),
    'PA1.ME4_PBPG': ('PA1ME4', 'taxaTomadaContas'),
    'PA2.ME1_PBPG': ('PA2.ME1', 'quantidadeTrabalhosAreasPrioritarias'),
    'PA2.ME2_PBPG': ('PA2.ME2', 'taxaTrabalhosAreasPrioritarias'),
}

# Desagregações reconhecidas na descrição da métrica. A ordem é fixa para que a
# geração seja determinística.
ESTRATIFICACOES = [
    ('Edital',      'edital',     r'\bedital\b'),
    ('Semestre',    'semestre',   r'\bsemestr'),
    ('Ano',         'ano',        r'\bano\b|\banual\b|ano de titula|ano de public'),
    ('Quadrienio',  'quadrienio', r'quadrienal|quadri.nio'),
    ('Modalidade',  'modalidade', r'\bmodalidade\b'),
    ('PrazoConclusao', 'prazo',   r'prazo de conclus'),
    ('Area',        'area',       r'.rea (?:do|de) conhecimento'),
    ('Segmento',    'segmento',   r'\bsegmento\b'),
    ('Quartil',     'quartil',    r'\bquartil\b'),
    ('RDE',         'rde',        r'Regi.o de Desenvolvimento|\bRDE\b'),
]
NOME_ESTRAT = {
    'Edital': 'Edital',
    'Semestre': 'Semestre',
    'Ano': 'Ano',
    'Quadrienio': 'Quadriênio de Avaliação',
    'Modalidade': 'Modalidade',
    'PrazoConclusao': 'Prazo de Conclusão',
    'Area': 'Grande Área do Conhecimento FACEPE',
    'Segmento': 'Segmento',
    'Quartil': 'Quartil do Periódico',
    'RDE': 'Região de Desenvolvimento do Estado',
}

# Prefixo da chave de extração, derivado da primeira fonte de informação da
# métrica. Segue o padrão já usado no repositório ("agilfap.cotas.encerradas").
PREFIXO_FONTE = {
    'FI1.1': 'primario', 'FI2.1': 'agilfap', 'FI2.2': 'rais', 'FI2.6': 'jucepe',
    'FI3.1': 'sucupira', 'FI3.2': 'lattes', 'FI3.3': 'scholar', 'FI3.4': 'scopus',
    'FI4.2': 'inpi',
}

ALIAS_FONTE = {
    'fontesDadosPrimarios': 'fontesDadosPrimarios',
    'fontesSistemasBasesGovernamentais': 'fontesSistemasBasesGovernamentais',
    'fontesBasesAcademicasCientificasEducacionais': 'fontesBasesAcademicasCientificasEducacionais',
    'fontesInfraestruturaAtivosCTI': 'fontesInfraestruturaAtivosCTI',
    'fontesDadosSocioeconomicosTerritoriais': 'fontesDadosSocioeconomicosTerritoriais',
}

OPERACAO_APELIDO = {
    'http://www.openmath.org/cd/fns1#identity': 'identidade',
    'http://www.openmath.org/cd/arith1#divide': 'divisao',
    'http://www.openmath.org/cd/arith1#times': 'multiplicacao',
}


def nome_instancia_formula(operacao):
    """Cada métrica tem no máximo uma fórmula por operação, então o apelido basta."""
    return camel('formula ' + OPERACAO_APELIDO[operacao])


def sem_acento(txt):
    return ''.join(c for c in unicodedata.normalize('NFD', txt)
                   if unicodedata.category(c) != 'Mn')


def camel(txt, inicial_maiuscula=False):
    palavras = re.split(r'[^0-9A-Za-z]+', sem_acento(txt))
    palavras = [p for p in palavras if p]
    if not palavras:
        return 'x'
    saida = palavras[0].lower() + ''.join(p.capitalize() for p in palavras[1:])
    if inicial_maiuscula:
        saida = saida[0].upper() + saida[1:]
    if saida[0].isdigit():
        saida = 'x' + saida
    return saida


def slug_pontos(txt):
    return '.'.join(p.lower() for p in re.split(r'[^0-9A-Za-z]+', sem_acento(txt)) if p)


def ler_metadados_pa(caminho):
    """Extrai temFonte, finalidade, valorAtual e valorMeta de cada métrica do PA-PBPG.oml."""
    src = open(caminho, encoding='utf-8').read()
    props = ('base:', 'metricas:', 'formulas:', 'planoAvaliacao:')
    meta = {}
    for bloco in re.finditer(r'instance\s+\S+\s*:\s*metricas:metrica\s*\[(.*?)\n\t\]', src, re.S):
        acc, atual = {}, None
        for linha in bloco.group(1).split('\n'):
            s = linha.strip()
            if not s:
                continue
            if any(s.startswith(p) for p in props):
                atual = s.split(None, 1)[0]
                acc[atual] = acc.get(atual, '') + (s.split(None, 1)[1] if ' ' in s else '')
            elif atual:
                acc[atual] += ' ' + s
        bid = re.search(r'"([^"]+)"', acc.get('base:id', ''))
        if not bid:
            continue
        fin = re.search(r'"([^"]+)"', acc.get('metricas:finalidade', ''))
        meta[bid.group(1).split()[0]] = {
            'fontes': [f.strip() for f in acc.get('metricas:temFonte', '').split(',') if f.strip()],
            'finalidade': fin.group(1) if fin else None,
            'valorAtual': acc.get('metricas:valorAtual', '').strip() or None,
            'valorMeta': acc.get('metricas:valorMeta', '').strip() or None,
        }
    return meta


def estratificacoes_de(descricao):
    achadas = []
    for chave, sufixo, padrao in ESTRATIFICACOES:
        if re.search(padrao, descricao, re.I):
            achadas.append((chave, sufixo))
    return achadas


class Metrica:
    def __init__(self, mid, linhas):
        self.id = mid
        self.nome = linhas[0]['nome']
        self.descricao = linhas[0]['desc']
        self.raiz = linhas[0]['rootFormulaId']
        self.codigo_pa = mid.rsplit('_', 1)[0]          # PA3.ME1_PBPG -> PA3.ME1
        self.sufixo = self.codigo_pa                     # usado nos base:id
        self.instancia = camel(self.nome)
        # formulaId -> lista de argumentos (linhas), em ordem de posição
        self.formulas = {}
        self.pai = {}
        self.operacao = {}
        for ln in linhas:
            fid = ln['formulaId']
            self.formulas.setdefault(fid, []).append(ln)
            self.operacao[fid] = ln['operacao']
            self.pai[fid] = ln['parentFormulaId']
        for fid in self.formulas:
            self.formulas[fid].sort(key=lambda r: int(r['argPosicao']))

    def ordem_pos_ordem(self):
        """Fórmulas das mais internas para a raiz, para declarar antes de referenciar."""
        vistas, ordem = set(), []

        def visita(fid):
            if fid in vistas:
                return
            vistas.add(fid)
            for arg in self.formulas.get(fid, []):
                if arg['valFormulaAninhada']:
                    visita(arg['valFormulaAninhada'])
            ordem.append(fid)

        visita(self.raiz)
        for fid in self.formulas:
            visita(fid)
        return ordem


def gerar_oml(m, meta, indice):
    """Devolve (texto_oml, avisos)."""
    avisos = []
    L = []
    ref_externas = {}    # alias -> IRI, para o extends

    # ---- descobre referências a outras métricas, para montar o extends
    for args in m.formulas.values():
        for a in args:
            alvo = a['valMetricaVinculada']
            if alvo and alvo != m.id and alvo in indice:
                alias, _ = indice[alvo]
                ref_externas[alias] = '%s/%s#' % (IRI_METRICAS, alias)

    dados = meta.get(m.codigo_pa, {})
    fontes = dados.get('fontes', [])
    aliases_fonte = sorted({f.split(':')[0] for f in fontes})

    L.append('description <%s/%s#> as %s {' % (IRI_METRICAS, m.codigo_pa, m.codigo_pa))
    L.append('')
    L.append('\t// Gerado por scripts/gerar_metricas_oml.py a partir de formulas.json.')
    L.append('\t// Fórmula, argumentos e operações OpenMath vêm do JSON; temFonte,')
    L.append('\t// finalidade e valores vêm do PA-PBPG.oml (métrica %s).' % m.codigo_pa)
    L.append('')
    for alias in sorted(ref_externas):
        L.append('\textends <%s> as %s' % (ref_externas[alias], alias))
    for alias in aliases_fonte:
        L.append('\textends <%s/%s#> as %s' % (IRI_FONTES, alias, alias))
    L.append('\tuses <http://secti.pe.gov.br/indicador_cti/vocabulary/DesignAvaliacao/metricas#> as metricas')
    L.append('\tuses <http://secti.pe.gov.br/indicador_cti/vocabulary/DesignAvaliacao/formulas#> as formulas')
    L.append('\tuses <http://secti.pe.gov.br/indicador_cti/vocabulary/base#> as base')
    L.append('\tuses <http://www.w3.org/2001/XMLSchema#> as xsd')
    L.append('')

    # ---- estratificações
    estrats = estratificacoes_de(m.descricao)
    if estrats:
        L.append('\t// ESTRATIFICAÇÕES (dimensões de desagregação citadas na descrição)')
        for chave, sufixo in estrats:
            L.append('\tinstance estrat%s : formulas:estratificacao [' % chave)
            L.append('\t\tbase:id "estrat_%s_%s"' % (sufixo, m.sufixo))
            L.append('\t\tbase:nome "%s"' % NOME_ESTRAT[chave])
            L.append('\t]')
            L.append('')

    # ---- métrica
    L.append('\t// MÉTRICA')
    L.append('\tinstance %s : metricas:metrica [' % m.instancia)
    L.append('\t\tbase:id "%s"' % m.id)
    L.append('\t\tbase:nome "%s"' % m.nome.replace('"', '\\"'))
    L.append('\t\tbase:descricao "%s"' % m.descricao.replace('"', '\\"'))
    if dados.get('finalidade'):
        L.append('\t\tmetricas:finalidade "%s"' % dados['finalidade'])
    L.append('\t\tformulas:possuiFormula %s' % nome_instancia_formula(m.operacao[m.raiz]))
    for chave, _ in estrats:
        L.append('\t\tformulas:estratificadaPor estrat%s' % chave)
    if fontes:
        L.append('\t\tmetricas:temFonte %s' % ', '.join(fontes))
    if dados.get('valorAtual'):
        L.append('\t\tmetricas:valorAtual %s' % dados['valorAtual'])
    if dados.get('valorMeta'):
        L.append('\t\tmetricas:valorMeta %s' % dados['valorMeta'])
    L.append('\t]')
    L.append('')

    # ---- fórmulas, das mais internas para a raiz
    prefixo_chave = 'fonte'
    for f in fontes:
        cod = f.split(':')[-1]
        if cod in PREFIXO_FONTE:
            prefixo_chave = PREFIXO_FONTE[cod]
            break

    for fid in m.ordem_pos_ordem():
        args = m.formulas.get(fid, [])
        if not args:
            continue
        op = m.operacao[fid]
        nome_formula = nome_instancia_formula(op)
        eh_raiz = (fid == m.raiz)

        L.append('\t// %s' % ('fórmula raiz' if eh_raiz else 'fórmula aninhada'))
        L.append('\tinstance %s : formulas:formula [' % nome_formula)
        L.append('\t\tbase:id "%s"' % fid)
        L.append('\t\tformulas:referenciaOperacao "%s"' % op)
        for a in args:
            L.append('\t\tformulas:possuiArgumento %s' % camel('arg ' + a['argNome']))
        if eh_raiz:
            L.append('\t\tformulas:formulaDe %s' % m.instancia)
        L.append('\t]')
        L.append('')

        for a in args:
            nome_arg = camel('arg ' + a['argNome'])
            nome_val = camel('val ' + a['argNome'])
            L.append('\tinstance %s : formulas:argumento [' % nome_arg)
            L.append('\t\tbase:id "arg_%s_%s"' % (slug_pontos(a['argNome']).replace('.', '_'), m.sufixo))
            L.append('\t\tformulas:posicao "%s"^^xsd:int' % a['argPosicao'])
            L.append('\t\tformulas:nome "%s"' % a['argNome'].replace('"', '\\"'))
            L.append('\t\tformulas:possuiValor %s' % nome_val)
            L.append('\t\tformulas:argumentoDe %s' % nome_formula)
            L.append('\t]')
            L.append('')

            if a['valLiteral'] is not None:
                L.append('\tinstance %s : formulas:tipovalorLiteral [' % nome_val)
                L.append('\t\tbase:id "val_%s_%s"' % (slug_pontos(a['argNome']).replace('.', '_'), m.sufixo))
                L.append('\t\tformulas:valorLiteral %s' % a['valLiteral'])
                L.append('\t]')
            elif a['valFormulaAninhada']:
                alvo = nome_instancia_formula(m.operacao[a['valFormulaAninhada']])
                L.append('\tinstance %s : formulas:tipovalorFormula [' % nome_val)
                L.append('\t\tbase:id "val_%s_%s"' % (slug_pontos(a['argNome']).replace('.', '_'), m.sufixo))
                L.append('\t\tformulas:valorFormula %s' % alvo)
                L.append('\t]')
            elif a['valMetricaVinculada']:
                alvo_id = a['valMetricaVinculada']
                if alvo_id in indice:
                    alias, inst = indice[alvo_id]
                    ref = '%s:%s' % (alias, inst) if alias != m.codigo_pa else inst
                else:
                    ref = None
                    avisos.append('%s: referencia a métrica desconhecida %s' % (m.id, alvo_id))
                L.append('\tinstance %s : formulas:tipovalorMetrica [' % nome_val)
                L.append('\t\tbase:id "val_%s_%s"' % (slug_pontos(a['argNome']).replace('.', '_'), m.sufixo))
                if ref:
                    L.append('\t\tformulas:valorMetrica %s' % ref)
                L.append('\t]')
            else:
                # Argumento sem valor no JSON: no plano homologado ele é uma
                # métrica simples própria, que ainda não existe no repositório.
                # Mantém-se o padrão já usado no repo (chave de extração como
                # string) para não introduzir construto novo no vocabulário.
                chave = '%s.%s' % (prefixo_chave, slug_pontos(a['argNome']))
                avisos.append('%s: argumento "%s" sem valor no JSON -> chave "%s"'
                              % (m.id, a['argNome'], chave))
                L.append('\t// PENDENTE: no Plano de Avaliação este operando é uma métrica')
                L.append('\t// simples própria; até que ela exista, fica a chave de extração.')
                L.append('\tinstance %s : formulas:tipovalorMetrica [' % nome_val)
                L.append('\t\tbase:id "val_%s_%s"' % (slug_pontos(a['argNome']).replace('.', '_'), m.sufixo))
                L.append('\t\tformulas:valorMetrica "%s"' % chave)
                L.append('\t]')
            L.append('')

    L.append('}')
    return '\n'.join(L) + '\n', avisos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--saida', default=DIR_METRICAS)
    ap.add_argument('--todas', action='store_true',
                    help='gera também as métricas que já têm arquivo escrito à mão')
    ap.add_argument('--json', default=FORMULAS_JSON)
    args = ap.parse_args()

    linhas = json.load(open(args.json, encoding='utf-8'))
    por_metrica = {}
    for ln in linhas:
        por_metrica.setdefault(ln['id'], []).append(ln)

    meta = ler_metadados_pa(PA_PBPG)

    # índice completo: id da métrica -> (alias do description, nome da instância)
    indice = dict(JA_EXISTENTES)
    metricas = {}
    for mid, ls in por_metrica.items():
        if not mid.endswith('_PBPG'):
            continue                      # BPP já está descrito em metricasBPP/
        m = Metrica(mid, ls)
        metricas[mid] = m
        indice.setdefault(mid, (m.codigo_pa, m.instancia))

    os.makedirs(args.saida, exist_ok=True)
    gerados, todos_avisos = [], []
    for mid, m in sorted(metricas.items()):
        if mid in JA_EXISTENTES and not args.todas:
            continue
        texto, avisos = gerar_oml(m, meta, indice)
        destino = os.path.join(args.saida, '%s.oml' % m.codigo_pa)
        open(destino, 'w', encoding='utf-8').write(texto)
        gerados.append(destino)
        todos_avisos.extend(avisos)

    for g in gerados:
        print('gerado: %s' % os.path.relpath(g, RAIZ))
    print('\n%d arquivo(s) gerado(s)' % len(gerados))
    if todos_avisos:
        print('\n%d aviso(s):' % len(todos_avisos))
        for a in todos_avisos:
            print('  - %s' % a)


if __name__ == '__main__':
    main()
