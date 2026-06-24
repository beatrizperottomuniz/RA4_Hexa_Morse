'''
Integrantes do grupo (ordem alfabética):
Beatriz Perotto Muniz - @beatrizperottomuniz

Nome do grupo no Canvas: RA3 6
'''
import json
from globalVars import string_pool_global

arqv_atrib_json = "saida_arvore_atribuida.json"
arqv_atrib_txt  = "saida_arvore_atribuida.txt"
arqv_atrib_md   = "saida_arvore_atribuida.md"
arqv_atrib_png  = "saida_arvore_atribuida.png"


# aux

def lexema(token):
    if token is None or token.simbolo_id is None:
        return None
    return string_pool_global.obterString(token.simbolo_id)


ops_arit = {'PLUS', 'MINUS', 'MULT', 'DIV', 'INT_DIV', 'MOD', 'POW'}
ops_rel  = {'GT', 'LT', 'GTE', 'LTE', 'EQ', 'NEQ'}


def tipoOp(no):
    # retorna 'arit' / 'rel' / 'if' / 'for' / None
    if no.tipo in ops_arit:       return 'arit'
    if no.tipo in ops_rel:        return 'rel'
    if no.tipo == 'KEYWORD_IF':    return 'if'
    if no.tipo == 'KEYWORD_FOR':   return 'for'
    for filho in no.filhos:
        r = tipoOp(filho)
        if r:
            return r
    return None


def categoriaNo(no):
    # cat semantica nos rpn e stmt
    if no.tipo == 'stmt':
        return 'subexpressao'

    if no.tipo != 'rpn' or not no.filhos:
        return None

    primeiro = no.filhos[0]

    # rpn -> ID  (leitura de variavel)
    if primeiro.tipo == 'ID':
        return 'leitura'

    # rpn -> STRING KEYWORD_MORSE
    if primeiro.tipo == 'STRING':
        return 'morse'

    # rpn -> num rpn_tail_num
    if primeiro.tipo == 'num' and len(no.filhos) > 1:
        tail = no.filhos[1]
        if not tail.filhos:
            return None
        tf = tail.filhos[0]
        if tf.tipo == 'ID': return 'atribuicao'
        if tf.tipo == 'KEYWORD_RES': return 'recuperacao_resultado'
        if tf.tipo == 'num' and len(tail.filhos) > 1:
            op = tipoOp(tail.filhos[1])
            if op == 'arit': return 'expressao_aritmetica'
            if op == 'rel':  return 'expressao_relacional'
        if tf.tipo == 'stmt' and len(tail.filhos) > 1:
            op = tipoOp(tail.filhos[1])
            if op == 'for':  return 'repeticao'
            if op == 'arit': return 'expressao_aritmetica'
            if op == 'rel':  return 'expressao_relacional'

    # rpn -> stmt rpn_tail_stmt
    if primeiro.tipo == 'stmt' and len(no.filhos) > 1:
        tail = no.filhos[1]
        if not tail.filhos:
            return None
        tf = tail.filhos[0]
        if tf.tipo == 'ID':                               return 'atribuicao'
        if tf.tipo == 'num' and len(tail.filhos) > 1:
            op = tipoOp(tail.filhos[1])
            if op == 'arit': return 'expressao_aritmetica'
            if op == 'rel':  return 'expressao_relacional'
        if tf.tipo == 'stmt' and len(tail.filhos) > 1:
            op = tipoOp(tail.filhos[1])
            if op == 'if':   return 'decisao'
            if op == 'arit': return 'expressao_aritmetica'
            if op == 'rel':  return 'expressao_relacional'

    return None


# json

def noParaDictAtribuido(no, tabela, tipos_nos):
    tipo_inferido = tipos_nos.get(id(no))
    categoria     = categoriaNo(no)

    resultado = {
        'tipo':    no.tipo,
        'token':   None,
        'simbolo': None,
        'filhos':  [noParaDictAtribuido(f, tabela, tipos_nos) for f in no.filhos]
    }
    if tipo_inferido is not None:
        resultado['tipo_inferido'] = tipo_inferido
    if categoria is not None:
        resultado['categoria_semantica'] = categoria

    if no.token:
        lex = lexema(no.token)
        resultado['token'] = {
            'tipo':   no.token.tipo,
            'linha':  no.token.linha,
            'coluna': no.token.coluna,
            'simbolo_id': no.token.simbolo_id
        }
        # se for ID anexa entrada da tab simb
        if no.tipo == 'ID' and lex and tabela:
            s = tabela.get(lex)
            if s:
                resultado['simbolo'] = {
                    'tipo':       s.tipo,
                    'linha_def':  s.linha_def,
                    'linhas_uso': s.linhas_uso
                }

    return resultado


def salvarAtribuidaJSON(dados, arquivo=arqv_atrib_json):
    output = {
        'string_pool': string_pool_global.strings,
        'arvore': dados
    }
    with open(arquivo, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=4)


# txt

def labelNo(no, tipos_nos):
    label = no.tipo
    tipo_inf = tipos_nos.get(id(no))
    categoria = categoriaNo(no)
    if tipo_inf is not None:
        label += f' : {tipo_inf}'
    if categoria is not None:
        label += f'  [{categoria}]'
    if no.token:
        label += f'  [L{no.token.linha}:{no.token.coluna}]'
        lex = lexema(no.token)
        if lex and no.token.tipo in ('NUM_INT', 'NUM_FLOAT', 'ID', 'STRING'):
            label += f'  "{lex}"'
    return label


def linhasTXT(no, prefixo, ultimo, linhas, tipos_nos):
    conector = '└── ' if ultimo else '├── '
    linhas.append(prefixo + conector + labelNo(no, tipos_nos))
    extensao = '    ' if ultimo else '│   '
    for i, filho in enumerate(no.filhos):
        linhasTXT(filho, prefixo + extensao, i == len(no.filhos) - 1, linhas, tipos_nos)


def salvarAtribuidaTXT(raiz, tipos_nos, arquivo=arqv_atrib_txt):
    linhas = [labelNo(raiz, tipos_nos)]
    for i, filho in enumerate(raiz.filhos):
        linhasTXT(filho, '', i == len(raiz.filhos) - 1, linhas, tipos_nos)
    with open(arquivo, 'w', encoding='utf-8') as f:
        f.write('\n'.join(linhas))


# md

def linhasMD(no, nivel, linhas, tipos_nos):
    indent = '  ' * nivel
    label = f'`{no.tipo}`'
    tipo_inf  = tipos_nos.get(id(no))
    categoria = categoriaNo(no)
    if tipo_inf is not None:
        label += f' **`: {tipo_inf}`**'
    if categoria is not None:
        label += f' *`[{categoria}]`*'
    if no.token:
        label += f' `[L{no.token.linha}:{no.token.coluna}]`'
        lex = lexema(no.token)
        if lex and no.token.tipo in ('NUM_INT', 'NUM_FLOAT', 'ID', 'STRING'):
            label += f' `"{lex}"`'
    linhas.append(f'{indent}- {label}')
    for filho in no.filhos:
        linhasMD(filho, nivel + 1, linhas, tipos_nos)


def salvarAtribuidaMD(raiz, tipos_nos, arquivo=arqv_atrib_md):
    linhas = ['# Árvore Sintática Atribuída\n']
    linhasMD(raiz, 0, linhas, tipos_nos)
    with open(arquivo, 'w', encoding='utf-8') as f:
        f.write('\n'.join(linhas))


# png

def calcularPos(no, profundidade, posicoes, contador_folha):
    if not no.filhos:
        x = contador_folha[0]
        contador_folha[0] += 1
    else:
        for filho in no.filhos:
            calcularPos(filho, profundidade + 1, posicoes, contador_folha)
        xs = [posicoes[id(f)][0] for f in no.filhos]
        x  = (xs[0] + xs[-1]) / 2
    posicoes[id(no)] = (x, profundidade)


def desenharAtribuida(no, posicoes, ax, BOX_W, BOX_H, tipos_nos):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.patches as mpatches
    except ImportError:
        return

    x, y = posicoes[id(no)]
    y_plot = -y

    label = no.tipo
    tipo_inf = tipos_nos.get(id(no))
    if tipo_inf is not None:
        label += f'\n: {tipo_inf}'
    if no.token:
        lex = lexema(no.token)
        if lex and no.token.tipo in ('NUM_INT', 'NUM_FLOAT', 'ID', 'STRING'):
            label += f'\n"{lex}"'
        label += f'\nL{no.token.linha}:{no.token.coluna}'

    # nós com tipo anotado ficam com cor diferente
    if tipo_inf is not None:
        cor = "#c8f0c8"  # verde claro para nós anotados
    elif not no.token and no.tipo != 'ε':
        cor = "#f6dafb"  # roxo claro para não-terminais
    else:
        cor = "#dfcdfa"  # roxo para terminais

    caixa = mpatches.FancyBboxPatch(
        (x - BOX_W / 2, y_plot - BOX_H / 2), BOX_W, BOX_H,
        boxstyle="round,pad=0.05", linewidth=0.8,
        edgecolor='#555555', facecolor=cor
    )
    ax.add_patch(caixa)
    ax.text(x, y_plot, label, ha='center', va='center',
            fontsize=7, fontfamily='monospace')

    for filho in no.filhos:
        fx, fy = posicoes[id(filho)]
        fy_plot = -fy
        ax.plot([x, fx], [y_plot - BOX_H / 2, fy_plot + BOX_H / 2],
                color="#555555", linewidth=0.7, zorder=0)
        desenharAtribuida(filho, posicoes, ax, BOX_W, BOX_H, tipos_nos)


def gerarAtribuidaPNG(raiz, tipos_nos, arquivo=arqv_atrib_png):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print("[aviso] matplotlib não instalado — PNG não gerado. "
              "Execute: pip install matplotlib")
        return

    posicoes       = {}
    contador_folha = [0]
    calcularPos(raiz, 0, posicoes, contador_folha)

    total_folhas = contador_folha[0]
    max_prof     = max(y for x, y in posicoes.values()) if posicoes else 1

    larg  = max(10, total_folhas * 1.4)
    alt   = max(6,  (max_prof + 1) * 1.6)
    fig, ax = plt.subplots(figsize=(larg, alt))
    ax.set_xlim(-1, total_folhas)
    ax.set_ylim(-(max_prof + 0.8), 0.8)
    ax.axis('off')
    ax.set_title('Árvore Sintática Atribuída', fontsize=11, pad=10)

    BOX_W, BOX_H = 0.9, 0.55  # ligeiramente maior para caber anotacao de tipo

    desenharAtribuida(raiz, posicoes, ax, BOX_W, BOX_H, tipos_nos)

    plt.tight_layout()
    plt.savefig(arquivo, dpi=150, bbox_inches='tight')
    plt.close()


# anot nos nos

def anotarArvore(no, tipos_nos):
    # add tipo_inferido e categoria_semantica em cada NoArvore
    no.tipo_inferido       = tipos_nos.get(id(no))
    no.categoria_semantica = categoriaNo(no)
    for filho in no.filhos:
        anotarArvore(filho, tipos_nos)


# func aluno

def gerarArvoreAtribuida(arvore, tabelaSimbolos, tipos):
    tabela    = tabelaSimbolos
    tipos_nos = tipos

    if arvore is None:
        return None

    anotarArvore(arvore, tipos_nos)
    atribuida = noParaDictAtribuido(arvore, tabela, tipos_nos)
    salvarAtribuidaJSON(atribuida)
    salvarAtribuidaTXT(arvore, tipos_nos)
    salvarAtribuidaMD(arvore, tipos_nos)
    gerarAtribuidaPNG(arvore, tipos_nos)
    return arvore
