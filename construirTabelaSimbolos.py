'''
Integrantes do grupo (ordem alfabética):
Beatriz Perotto Muniz - @beatrizperottomuniz

Nome do grupo no Canvas: RA3 6
'''
import json
import globalVars

arqv_tabela_json = "saida_tabela_simbolos.json"
arqv_tabela_md   = "saida_tabela_simbolos.md"


class Simbolo:
    def __init__(self, nome, tipo, linha_def):
        self.nome       = nome
        self.tipo       = tipo        # 'int' / 'float' / 'bool' / None
        self.linha_def  = linha_def
        self.linhas_uso = []

    def __repr__(self):
        return (f"<Simbolo nome='{self.nome}' tipo='{self.tipo}' "
                f"def=L{self.linha_def} usos={self.linhas_uso}>")


class TabelaSimbolos:
    def __init__(self):
        self.tabela = {}
        self.erros  = []

    def declarar(self, nome, tipo, linha):
        # registra var, erro se tipo incompativel com declaracao anterior
        if nome in self.tabela:
            existente = self.tabela[nome]
            if tipo is not None and existente.tipo != tipo:
                self.erros.append(
                    f"Erro semântico (linha {linha}): variável '{nome}' "
                    f"já declarada como '{existente.tipo}', "
                    f"tentativa de redefinir como '{tipo}'"
                )
            else:
                # reatribuicao valida -> linha como uso da var
                existente.linhas_uso.append(linha)
            return False   # nao sobrescreve se existe
        self.tabela[nome] = Simbolo(nome, tipo, linha)
        return True

    def registrarUso(self, nome, linha):
        simbolo = self.tabela.get(nome)
        if simbolo is None:
            self.erros.append(
                f"Erro semântico (linha {linha}): "
                f"variável '{nome}' usada antes de ser definida"
            )
            return False
        simbolo.linhas_uso.append(linha)
        return True

    def salvarJSON(self, arquivo=arqv_tabela_json):
        dados = {
            nome: {
                'tipo':       s.tipo,
                'linha_def':  s.linha_def,
                'linhas_uso': s.linhas_uso
            }
            for nome, s in self.tabela.items()
        }
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)

    def salvarMD(self, arquivo=arqv_tabela_md):
        linhas = [
            "# Tabela de Símbolos\n",
            "| Nome | Tipo | Linha definição | Linhas de uso |",
            "|------|------|-----------------|---------------|"
        ]
        for nome, s in sorted(self.tabela.items()):
            usos = ', '.join(str(l) for l in s.linhas_uso) if s.linhas_uso else '—'
            linhas.append(f"| {nome} | {s.tipo} | {s.linha_def} | {usos} |")
        with open(arquivo, 'w', encoding='utf-8') as f:
            f.write('\n'.join(linhas))

# aux

def lexema(token):
    if token is None or token.simbolo_id is None:
        return None
    return globalVars.string_pool_global.obterString(token.simbolo_id)


def inferirTipoNum(no):
    # percorre subarvore num/num_tipo ate achar int ou float
    for filho in no.filhos:
        if filho.tipo == 'NUM_INT':
            return 'int'
        if filho.tipo == 'NUM_FLOAT':
            return 'float'
        if filho.tipo in ('num', 'num_tipo'):
            resultado = inferirTipoNum(filho)
            if resultado:
                return resultado
    return None


def temOpRelacional(no):
    #  se subarvore tem op relacional - resultado bool
    if no.tipo in ('op_rel', 'GT', 'LT', 'GTE', 'LTE', 'EQ', 'NEQ'):
        return True
    for filho in no.filhos:
        if temOpRelacional(filho):
            return True
    return False


def inferirTipoStmt(no_stmt, tabela, historico_tipos):
    # stmt → LPAREN rpn RPAREN — delega para inferirTipoRpnNo
    for filho in no_stmt.filhos:
        if filho.tipo == 'rpn':
            return inferirTipoRpnNo(filho, tabela, historico_tipos)
    return None


def encontrarTokenInt(no):
    # acha primeiro NUM_INT na subarvore , pra N do RES
    if no.tipo == 'NUM_INT' and no.token:
        return no.token
    for filho in no.filhos:
        resultado = encontrarTokenInt(filho)
        if resultado:
            return resultado
    return None


def encontrarOp(no):
    # encontra tipo do op na subarvore op_bin / op_stmt_...
    _OPS = {'PLUS', 'MINUS', 'MULT', 'DIV', 'INT_DIV', 'MOD', 'POW',
            'GT', 'LT', 'GTE', 'LTE', 'EQ', 'NEQ',
            'KEYWORD_IF', 'KEYWORD_FOR'}
    if no.tipo in _OPS:
        return no.tipo
    for filho in no.filhos:
        resultado = encontrarOp(filho)
        if resultado:
            return resultado
    return None


def tipoResultadoOp(op, tipo_esq, tipo_dir):
    # inferir saida simples com base no op sem validacao (valida em verificarTipos)
    if op in ('PLUS', 'MINUS', 'MULT'):
        return tipo_esq   # assume op =, se erro -> verificarTipos
    if op == 'DIV':
        return 'float'
    if op in ('INT_DIV', 'MOD'):
        return 'int'
    if op == 'POW':
        return tipo_esq
    if op in ('GT', 'LT', 'GTE', 'LTE', 'EQ', 'NEQ'):
        return 'bool'
    return None           # IF/FOR -> ok


def inferirTipoRpnNo(no_rpn, tabela, historico_tipos):
    # infere tipo de resultado de um no rpn (sem validacao — so inferencia)
    filhos = no_rpn.filhos
    if not filhos:
        return None
    primeiro = filhos[0]

    # leitura de var
    if primeiro.tipo == 'ID':
        nome = lexema(primeiro.token)
        if nome and tabela:
            s = tabela.tabela.get(nome)
            return s.tipo if s else None
        return None

    # rpn -> num rpn_tail_num
    if primeiro.tipo == 'num' and len(filhos) > 1:
        tipo_esq = inferirTipoNum(primeiro)
        tail = filhos[1]
        if not tail.filhos:
            return tipo_esq
        tf = tail.filhos[0]
        if tf.tipo == 'ID':
            return tipo_esq
        if tf.tipo == 'KEYWORD_RES':
            token_n = encontrarTokenInt(primeiro)
            if token_n:
                n = int(lexema(token_n) or '0')
                if any(f.tipo == 'MINUS' for f in primeiro.filhos):
                    n = -n
                idx = len(historico_tipos) - n
                if 0 <= idx < len(historico_tipos):
                    return historico_tipos[idx]
            return None
        if tf.tipo == 'num' and len(tail.filhos) > 1:
            tipo_dir = inferirTipoNum(tf)
            op = encontrarOp(tail.filhos[1])
            return tipoResultadoOp(op, tipo_esq, tipo_dir)
        if tf.tipo == 'stmt' and len(tail.filhos) > 1:
            tipo_dir = inferirTipoStmt(tf, tabela, historico_tipos)
            op = encontrarOp(tail.filhos[1])
            return tipoResultadoOp(op, tipo_esq, tipo_dir)
        return tipo_esq

    # rpn -> stmt rpn_tail_stmt
    if primeiro.tipo == 'stmt' and len(filhos) > 1:
        tipo_esq = inferirTipoStmt(primeiro, tabela, historico_tipos)
        tail = filhos[1]
        if not tail.filhos:
            return tipo_esq
        tf = tail.filhos[0]
        if tf.tipo == 'ID':
            return tipo_esq
        if tf.tipo == 'num' and len(tail.filhos) > 1:
            tipo_dir = inferirTipoNum(tf)
            op = encontrarOp(tail.filhos[1])
            return tipoResultadoOp(op, tipo_esq, tipo_dir)
        if tf.tipo == 'stmt' and len(tail.filhos) > 1:
            tipo_dir = inferirTipoStmt(tf, tabela, historico_tipos)
            op = encontrarOp(tail.filhos[1])
            return tipoResultadoOp(op, tipo_esq, tipo_dir)
        return tipo_esq

    return None


# --------------

def percorrerArvore(no, tabela, contador, historico_tipos):
    if no is None:
        return
    if no.tipo == 'rpn':
        processarRpn(no, tabela, contador, historico_tipos)
        return
    if no.tipo == 'list_stmts':
        processarListStmts(no, tabela, contador, historico_tipos)
        return
    if no.tipo == 'list_item':
        processarListItem(no, tabela, contador, historico_tipos)
        return
    for filho in no.filhos:
        percorrerArvore(filho, tabela, contador, historico_tipos)


def processarListStmts(no, tabela, contador, historico_tipos):
    # list_stmts -> LPAREN list_item
    for filho in no.filhos:
        if filho.tipo == 'list_item':
            processarListItem(filho, tabela, contador, historico_tipos)


def processarListItem(no, tabela, contador, historico_tipos):
    # list_item -> KEYWORD_END RPAREN  |  rpn RPAREN list_stmts
    if not no.filhos:
        return
    if no.filhos[0].tipo == 'KEYWORD_END':
        return

    rpn_atual = None
    for filho in no.filhos:
        if filho.tipo == 'rpn':
            rpn_atual = filho
            processarRpn(filho, tabela, contador, historico_tipos)
        elif filho.tipo == 'list_stmts':
            tipo_atual = inferirTipoRpnNo(rpn_atual, tabela, historico_tipos) if rpn_atual else None
            historico_tipos.append(tipo_atual)
            contador[0] += 1
            processarListStmts(filho, tabela, contador, historico_tipos)


def processarRpn(no, tabela, contador, historico_tipos):
    filhos = no.filhos
    if not filhos:
        return
    primeiro = filhos[0]

    # rpn -> ID
    if primeiro.tipo == 'ID' and primeiro.token:
        nome = lexema(primeiro.token)
        if nome:
            tabela.registrarUso(nome, primeiro.token.linha)
        return
    # rpn -> num rpn_tail_num
    if primeiro.tipo == 'num' and len(filhos) > 1:
        processarRpnTailNum(primeiro, filhos[1], tabela, contador, historico_tipos)
        return
    # rpn -> stmt rpn_tail_stmt
    if primeiro.tipo == 'stmt' and len(filhos) > 1:
        percorrerArvore(primeiro, tabela, contador, historico_tipos)
        processarRpnTailStmt(primeiro, filhos[1], tabela, contador, historico_tipos)
        return

    # fallback
    for filho in filhos:
        percorrerArvore(filho, tabela, contador, historico_tipos)


def processarRpnTailNum(no_num, no_tail, tabela, contador, historico_tipos):
    # rpn_tail_num -> KEYWORD_RES | ID | num op_bin | stmt op_stmt_num
    if not no_tail.filhos:
        return

    tail_filho = no_tail.filhos[0]
    # ID
    if tail_filho.tipo == 'ID' and tail_filho.token:
        nome  = lexema(tail_filho.token)
        linha = tail_filho.token.linha
        tipo  = inferirTipoNum(no_num)
        if nome:
            tabela.declarar(nome, tipo, linha)
        return

    # KEYWORD_RES
    if tail_filho.tipo == 'KEYWORD_RES':
        token_n = encontrarTokenInt(no_num)
        linha   = tail_filho.token.linha if tail_filho.token else '?'
        if token_n:
            n     = int(lexema(token_n) or '0')
            if any(f.tipo == 'MINUS' for f in no_num.filhos):
                n = -n
            total = contador[0]
            if n < 0:
                tabela.erros.append(
                    f"Erro semântico (linha {linha}): "
                    f"RES requer inteiro não negativo, recebeu {n}"
                )
            elif n > total:
                tabela.erros.append(
                    f"Erro semântico (linha {linha}): "
                    f"RES({n}) inválido — só há {total} resultado(s) anteriores"
                )
        return

    # num op_bin  / stmt op_stmt_num - ver se leituras
    for filho in no_tail.filhos:
        percorrerArvore(filho, tabela, contador, historico_tipos)


def processarRpnTailStmt(no_stmt, no_tail, tabela, contador, historico_tipos):
    # rpn_tail_stmt -> ID | num op_bin | stmt op_stmt_stmt
    if not no_tail.filhos:
        return
    tail_filho = no_tail.filhos[0]

    # ID
    if tail_filho.tipo == 'ID' and tail_filho.token:
        nome  = lexema(tail_filho.token)
        linha = tail_filho.token.linha
        tipo  = inferirTipoStmt(no_stmt, tabela, historico_tipos)
        if nome:
            tabela.declarar(nome, tipo, linha)
        return
    
    # num op_bin /stmt op_stmt_stmt - le var
    for filho in no_tail.filhos:
        percorrerArvore(filho, tabela, contador, historico_tipos)


# funcao do aluno

def construirTabelaSimbolos(arvore):
    tabela = TabelaSimbolos()

    if arvore is None:
        tabela.erros.append("Tabela de símbolos não construída: árvore sintática não disponível.")
        return tabela.tabela, tabela.erros

    contador        = [0]  # resultados feitos ate agora
    historico_tipos = []   # tipo de cada resultado
    percorrerArvore(arvore, tabela, contador, historico_tipos)

    tabela.salvarJSON()
    tabela.salvarMD()

    return tabela.tabela, tabela.erros
