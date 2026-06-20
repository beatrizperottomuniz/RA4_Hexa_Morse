'''
Integrantes do grupo (ordem alfabética):
Beatriz Perotto Muniz - @beatrizperottomuniz

Nome do grupo no Canvas: RA3 6
'''
import globalVars

# aux

def lexema(token):
    if token is None or token.simbolo_id is None:
        return None
    return globalVars.string_pool_global.obterString(token.simbolo_id)


def inferirTipoNum(no, tipos_nos):
    for filho in no.filhos:
        if filho.tipo == 'NUM_INT':
            tipos_nos[id(filho)] = 'int'
            tipos_nos[id(no)]    = 'int'
            return 'int'
        if filho.tipo == 'NUM_FLOAT':
            tipos_nos[id(filho)] = 'float'
            tipos_nos[id(no)]    = 'float'
            return 'float'
        if filho.tipo in ('num', 'num_tipo'):
            resultado = inferirTipoNum(filho, tipos_nos)
            if resultado:
                tipos_nos[id(no)] = resultado
                return resultado
    return None


def extrairValorNum(no):
    # considera MINUS
    negativo = any(f.tipo == 'MINUS' for f in no.filhos)
    for filho in no.filhos:
        if filho.tipo in ('NUM_INT', 'NUM_FLOAT') and filho.token:
            try:
                val = float(lexema(filho.token) or '0')
                return -val if negativo else val
            except (ValueError, TypeError):
                return None
        if filho.tipo in ('num', 'num_tipo'):
            val = extrairValorNum(filho)
            if val is not None:
                return -val if negativo else val
    return None


def encontrarOperador(no):
    OPS = {'PLUS', 'MINUS', 'MULT', 'DIV', 'INT_DIV', 'MOD', 'POW',
           'GT', 'LT', 'GTE', 'LTE', 'EQ', 'NEQ',
           'KEYWORD_IF', 'KEYWORD_FOR'}
    if no.tipo in OPS:
        return no.tipo
    for filho in no.filhos:
        resultado = encontrarOperador(filho)
        if resultado:
            return resultado
    return None


def linhaNo(no):
    if hasattr(no, 'token') and no.token and hasattr(no.token, 'linha'):
        return no.token.linha
    for filho in no.filhos:
        linha = linhaNo(filho)
        if linha:
            return linha
    return '?'


simbolo_op = {
    'PLUS': '+', 'MINUS': '-', 'MULT': '*',
    'DIV': '|', 'INT_DIV': '/', 'MOD': '%', 'POW': '^',
    'GT': '>', 'LT': '<', 'GTE': '>=', 'LTE': '<=', 'EQ': '==', 'NEQ': '!='
}


# ver op

def verificarOpBin(tipo_esq, tipo_dir, op, linha, erros):
    simb = simbolo_op.get(op, op)

    # propaga ERRO
    if tipo_esq == 'ERRO' or tipo_dir == 'ERRO':
        return 'ERRO'
    # IF/FOR como operando -> nao produz valor
    if tipo_esq is None or tipo_dir is None:
        erros.append(
            f"Erro semântico (linha {linha}): operador '{simb}' recebeu operando "
            f"de estrutura de controle que não produz valor"
        )
        return 'ERRO'

    if op in ('PLUS', 'MINUS', 'MULT'):
        if tipo_esq == tipo_dir and tipo_esq in ('int', 'float'):
            return tipo_esq
        erros.append(
            f"Erro semântico (linha {linha}): operador '{simb}' requer operandos "
            f"do mesmo tipo numérico, recebeu '{tipo_esq}' e '{tipo_dir}'"
        )
        return 'ERRO'

    if op == 'DIV':  
        if tipo_esq == tipo_dir and tipo_esq in ('int', 'float'):
            return 'float'
        erros.append(
            f"Erro semântico (linha {linha}): operador '|' requer operandos "
            f"do mesmo tipo numérico, recebeu '{tipo_esq}' e '{tipo_dir}'"
        )
        return 'ERRO'

    if op == 'INT_DIV':
        if tipo_esq == 'int' and tipo_dir == 'int':
            return 'int'
        erros.append(
            f"Erro semântico (linha {linha}): operador '/' requer ambos operandos "
            f"int, recebeu '{tipo_esq}' e '{tipo_dir}'"
        )
        return 'ERRO'

    if op == 'MOD':
        if tipo_esq == 'int' and tipo_dir == 'int':
            return 'int'
        erros.append(
            f"Erro semântico (linha {linha}): operador '%' requer ambos operandos "
            f"int, recebeu '{tipo_esq}' e '{tipo_dir}'"
        )
        return 'ERRO'

    if op == 'POW':
        if tipo_dir != 'int':
            erros.append(
                f"Erro semântico (linha {linha}): expoente em '^' deve ser int, "
                f"recebeu '{tipo_dir}'"
            )
            return 'ERRO'
        if tipo_esq not in ('int', 'float'):
            erros.append(
                f"Erro semântico (linha {linha}): base em '^' deve ser numérica, "
                f"recebeu '{tipo_esq}'"
            )
            return 'ERRO'
        return tipo_esq

    if op in ('GT', 'LT', 'GTE', 'LTE', 'EQ', 'NEQ'):
        if tipo_esq == tipo_dir and tipo_esq in ('int', 'float'):
            return 'bool'
        erros.append(
            f"Erro semântico (linha {linha}): operador '{simb}' requer operandos "
            f"do mesmo tipo numérico, recebeu '{tipo_esq}' e '{tipo_dir}'"
        )
        return 'ERRO'

    return None


def verificarIF(tipo_cond, linha, erros):
    if tipo_cond == 'ERRO':
        return 'ERRO'
    if tipo_cond != 'bool':
        erros.append(
            f"Erro semântico (linha {linha}): condição do IF deve ser bool, "
            f"recebeu '{tipo_cond}'"
        )
        return 'ERRO'
    return None  # julgamento ok


def verificarFOR(tipo_n, no_num, linha, erros):
    if tipo_n == 'ERRO':
        return 'ERRO'
    if tipo_n != 'int':
        erros.append(
            f"Erro semântico (linha {linha}): contador do FOR deve ser int, "
            f"recebeu '{tipo_n}'"
        )
        return 'ERRO'
    val = extrairValorNum(no_num)
    if val is not None and val <= 0:
        erros.append(
            f"Erro semântico (linha {linha}): contador do FOR deve ser positivo, "
            f"recebeu {int(val)}"
        )
        return 'ERRO'
    return None  # julgamento ok


# inf tipos

def inferirTipoStmt(no_stmt, tabela, historico, erros, tipos_nos):
    for filho in no_stmt.filhos:
        if filho.tipo == 'rpn':
            tipo = inferirTipoRpn(filho, tabela, historico, erros, tipos_nos)
            tipos_nos[id(no_stmt)] = tipo
            return tipo
    tipos_nos[id(no_stmt)] = None
    return None


def inferirTipoRpn(no_rpn, tabela, historico, erros, tipos_nos):
    filhos = no_rpn.filhos
    if not filhos:
        tipos_nos[id(no_rpn)] = None
        return None

    primeiro = filhos[0]

    if primeiro.tipo == 'ID':
        nome = lexema(primeiro.token)
        if nome:
            simbolo = tabela.get(nome)
            tipo = simbolo.tipo if simbolo else 'ERRO'
        else:
            tipo = 'ERRO'
        tipos_nos[id(primeiro)] = tipo
        tipos_nos[id(no_rpn)]   = tipo
        return tipo

    if primeiro.tipo == 'num' and len(filhos) > 1:
        tipo_esq = inferirTipoNum(primeiro, tipos_nos)
        tipo = inferirTipoTailNum(tipo_esq, primeiro, filhos[1], tabela, historico, erros, tipos_nos)
        tipos_nos[id(no_rpn)] = tipo
        return tipo

    if primeiro.tipo == 'stmt' and len(filhos) > 1:
        tipo_esq = inferirTipoStmt(primeiro, tabela, historico, erros, tipos_nos)
        tipo = inferirTipoTailStmt(tipo_esq, primeiro, filhos[1], tabela, historico, erros, tipos_nos)
        tipos_nos[id(no_rpn)] = tipo
        return tipo

    tipos_nos[id(no_rpn)] = None
    return None


def inferirTipoTailNum(tipo_esq, no_num, no_tail, tabela, historico, erros, tipos_nos):
    if not no_tail.filhos:
        return tipo_esq

    tail_filho = no_tail.filhos[0]
    linha = linhaNo(no_tail)

    # ver historico de tipos
    if tail_filho.tipo == 'KEYWORD_RES':
        val = extrairValorNum(no_num)
        N = int(val) if val is not None else 0
        idx = len(historico) - N
        if N == 0:
            erros.append(
                f"Erro semântico (linha {linha}): RES(0) referencia a linha "
                f"corrente — resultado ainda não disponível"
            )
            return 'ERRO'
        if 0 <= idx < len(historico):
            tipo_ref = historico[idx]
            if tipo_ref is None:
                erros.append(
                    f"Erro semântico (linha {linha}): RES referencia linha de "
                    f"estrutura de controle (IF/FOR) que não produz valor"
                )
                return 'ERRO'
            return tipo_ref
        return 'ERRO'  # indice invalido reportado por func construirTabelaSimbolos

    # ID — validacao feita por construirTabelaSimbolos
    if tail_filho.tipo == 'ID':
        return tipo_esq

    # num op_bin
    if tail_filho.tipo == 'num' and len(no_tail.filhos) > 1:
        tipo_dir = inferirTipoNum(tail_filho, tipos_nos)
        no_op    = no_tail.filhos[1]
        op       = encontrarOperador(no_op)
        if op == 'POW':
            val = extrairValorNum(tail_filho)
            if val is not None and val <= 0:
                erros.append(
                    f"Erro semântico (linha {linha}): expoente em '^' deve ser "
                    f"positivo, recebeu {int(val)}"
                )
                return 'ERRO'
        return verificarOpBin(tipo_esq, tipo_dir, op, linha, erros)

    # stmt op_stmt_num
    if tail_filho.tipo == 'stmt' and len(no_tail.filhos) > 1:
        tipo_dir = inferirTipoStmt(tail_filho, tabela, historico, erros, tipos_nos)
        no_op    = no_tail.filhos[1]
        op       = encontrarOperador(no_op)
        if op == 'KEYWORD_FOR':
            return verificarFOR(tipo_esq, no_num, linha, erros)
        return verificarOpBin(tipo_esq, tipo_dir, op, linha, erros)

    return tipo_esq


def inferirTipoTailStmt(tipo_esq, no_stmt, no_tail, tabela, historico, erros, tipos_nos):
    # ID / num op_bin / stmt op_stmt_stmt
    if not no_tail.filhos:
        return tipo_esq

    tail_filho = no_tail.filhos[0]
    linha = linhaNo(no_tail)

    if tail_filho.tipo == 'ID':
        if tipo_esq == 'bool':
            erros.append(
                f"Erro semântico (linha {linha}): "
                f"resultado relacional não pode ser armazenado em variável"
            )
            return 'ERRO'
        if tipo_esq is None:
            erros.append(
                f"Erro semântico (linha {linha}): "
                f"estrutura de controle não produz valor armazenável"
            )
            return 'ERRO'
        return tipo_esq

    # num op_bin
    if tail_filho.tipo == 'num' and len(no_tail.filhos) > 1:
        tipo_dir = inferirTipoNum(tail_filho, tipos_nos)
        no_op    = no_tail.filhos[1]
        op       = encontrarOperador(no_op)
        if op == 'POW':
            val = extrairValorNum(tail_filho)
            if val is not None and val <= 0:
                erros.append(
                    f"Erro semântico (linha {linha}): expoente em '^' deve ser "
                    f"positivo, recebeu {int(val)}"
                )
                return 'ERRO'
        return verificarOpBin(tipo_esq, tipo_dir, op, linha, erros)

    # stmt op_stmt_stmt
    if tail_filho.tipo == 'stmt' and len(no_tail.filhos) > 1:
        tipo_dir = inferirTipoStmt(tail_filho, tabela, historico, erros, tipos_nos)
        no_op    = no_tail.filhos[1]
        op       = encontrarOperador(no_op)
        if op == 'KEYWORD_IF':
            return verificarIF(tipo_esq, linha, erros)
        return verificarOpBin(tipo_esq, tipo_dir, op, linha, erros)

    return tipo_esq


# ------------------

def percorrerListStmts(no, tabela, historico, erros, tipos_nos):
    for filho in no.filhos:
        if filho.tipo == 'list_item':
            percorrerListItem(filho, tabela, historico, erros, tipos_nos)


def percorrerListItem(no, tabela, historico, erros, tipos_nos):
    # list_item -> KEYWORD_END RPAREN / rpn RPAREN list_stmts
    if not no.filhos or no.filhos[0].tipo == 'KEYWORD_END':
        return
    tipo_atual = None
    for filho in no.filhos:
        if filho.tipo == 'rpn':
            tipo_atual = inferirTipoRpn(filho, tabela, historico, erros, tipos_nos)
        elif filho.tipo == 'list_stmts':
            # statement processado - registra tipo no historico antes prox
            historico.append(tipo_atual)
            percorrerListStmts(filho, tabela, historico, erros, tipos_nos)


def buscarListStmts(no):
    if no.tipo == 'list_stmts':
        return no
    for filho in no.filhos:
        resultado = buscarListStmts(filho)
        if resultado:
            return resultado
    return None


# func do aluno

def verificarTipos(arvore, tabelaSimbolos):
    tabela    = tabelaSimbolos
    erros     = []
    historico = []# tipo de cada stmt processado
    tipos_nos = {}# id(no) -> tipo inferido

    if arvore is None:
        erros.append("Verificação de tipos não executada: árvore não disponível.")
        return erros, tipos_nos

    list_stmts = buscarListStmts(arvore)
    if list_stmts:
        percorrerListStmts(list_stmts, tabela, historico, erros, tipos_nos)

    return erros, tipos_nos

