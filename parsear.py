'''
Integrantes do grupo (ordem alfabética):
Beatriz Perotto Muniz - @beatrizperottomuniz

Nome do grupo no Canvas: RA3 6
'''
from construirGramatica import construirGramatica, simbolo_inicial_gramatica
from globalVars import string_pool_global

# arrumar parte de erros
maximo_de_erros = 10
tokens_sincronizacao = {'RPAREN','EOF'}

class Buffer: # buffer tem os tokens, pilha tem os nao terminais 
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def atual(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def lookahead(self):
        t = self.atual()
        return t.tipo if t else 'EOF'

    def consumir(self):
        token = self.atual()
        self.pos += 1
        return token

# funcao por nao terminal, buffer e pilha (vide slide)
# nao terminal + lookahead -> regras -> se match sai do buffer e da pilha, vai pro proximo nao terminal
# regras estao tem q ser colocadas ao contrario pra pop (na pilha)
# simbolo final é EOF

class Parser:
    def __init__(self, _tokens_, tabela_ll1):
        self.buffer = Buffer(_tokens_)
        self.tabela = tabela_ll1
        self.estrutura_derivacao = []
        self.erros = []
        self.pilha = [simbolo_inicial_gramatica]

    # pros erros -------------------
    def sincronizar(self):
        while self.buffer.lookahead() not in tokens_sincronizacao:
            self.buffer.consumir()

    def erro(self, msg):
        if len(self.erros) < maximo_de_erros:
            self.erros.append(msg)
        elif len(self.erros) == maximo_de_erros:
            self.erros.append("Muitos erros sintáticos — análise interrompida.")

    # pra pilha -------------------

    def match(self, tipo_esperado):
        token = self.buffer.atual()
        tipo  = self.buffer.lookahead()

        if self.pilha and self.pilha[-1] == tipo_esperado:
            self.pilha.pop()

        if tipo == tipo_esperado:
            t = self.buffer.consumir()
            self.estrutura_derivacao.append({'tipo': 'match', 'terminal': tipo_esperado, 'token': t})
            return t

        # erro
        linha  = token.linha  if token else '?'
        coluna = token.coluna if token else '?'
        lexema = ""
        if token and token.tipo in ('NUM_INT', 'NUM_FLOAT', 'ID'): 
            lexema = string_pool_global.obterString(token.simbolo_id)

        self.erro(
            f"Erro sintático (linha {linha}, col {coluna}): "
            f"esperado '{tipo_esperado}', encontrado '{tipo}'"
            + (f' ("{lexema}")' if lexema else "")
        )
        self.sincronizar()
        return None

    def expandir(self, nao_terminal): # nao terminal que estamos querendo achar regra
        # ret prod escolhida ou None se erro

        tipo = self.buffer.lookahead()
        # ver o token do buffer 

        if self.pilha and self.pilha[-1] == nao_terminal:
            self.pilha.pop()
        # tira da pilha o n terminal q estamos examinando

        # erro
        # se n tem uma regra pra combinacao de terminal e n terminal -> celula vazia -> erro sintatico
        if tipo not in self.tabela[nao_terminal]:
            token  = self.buffer.atual()
            linha  = token.linha  if token else '?'
            coluna = token.coluna if token else '?'
            esperados = sorted(self.tabela[nao_terminal].keys()) # tudo q podia pra aquele n terminal
            lexema = ""
            if token and token.tipo in ('NUM_INT', 'NUM_FLOAT', 'ID'): 
                lexema = string_pool_global.obterString(token.simbolo_id)
            if tipo == 'UNKNOWN':
                self.erro(
                    f"Erro léxico (linha {linha}, col {coluna}): "
                    f"token inválido encontrado durante análise sintática"
                )
            else:
                self.erro(
                    f"Erro sintático (linha {linha}, col {coluna}): "
                    f"em '{nao_terminal}', token '{tipo}' inesperado"
                    + (f' ("{lexema}")' if lexema else "")
                    + f". Esperados: {', '.join(esperados)}"
                )
            self.sincronizar()
            return None

        # regra da celula 
        producao = self.tabela[nao_terminal][tipo]

        if not producao:
            self.estrutura_derivacao.append({'tipo': 'epsilon', 'nao_terminal': nao_terminal})
        else:
            # pra return
            self.estrutura_derivacao.append({
                'tipo': 'expansao',
                'nao_terminal': nao_terminal,
                'producao': producao
            })
            for simbolo in reversed(producao):
                self.pilha.append(simbolo)

        return producao

    # funcao de cada nt -------------------

    def parseProg(self):
        #prog ::= LPAREN KEYWORD_START RPAREN list_stmts EOF
        if self.expandir('prog') is None:
            return
        self.match('LPAREN')
        self.match('KEYWORD_START')
        self.match('RPAREN')
        self.parseListStmts()
        self.match('EOF')

    def parseListStmts(self):
        #list_stmts ::= LPAREN list_item
        if self.expandir('list_stmts') is None:
            return
        self.match('LPAREN')
        self.parseListItem()

    def parseListItem(self):
        #list_item ::= KEYWORD_END RPAREN | rpn RPAREN list_stmts
        producao = self.expandir('list_item')
        if producao is None:
            return
        if producao[0] == 'KEYWORD_END':
            self.match('KEYWORD_END')
            self.match('RPAREN')
        else:
            self.parseRpn()
            self.match('RPAREN')
            self.parseListStmts()

    def parseStmt(self):
        #stmt ::= LPAREN rpn RPAREN
        if self.expandir('stmt') is None:
            return
        self.match('LPAREN')
        self.parseRpn()
        self.match('RPAREN')

    def parseRpn(self):
        #rpn ::= num rpn_tail_num | stmt rpn_tail_stmt | ID | STRING KEYWORD_MORSE
        producao = self.expandir('rpn')
        if producao is None:
            return
        if producao[0] == 'num':
            self.parseNum()
            self.parseRpnTailNum()
        elif producao[0] == 'stmt':
            self.parseStmt()
            self.parseRpnTailStmt()
        elif producao[0] == 'STRING':
            self.match('STRING')
            self.match('KEYWORD_MORSE')
        else:
            self.match('ID')

    def parseNum(self):
        #num ::= NUM_INT | NUM_FLOAT | MINUS num_tipo
        producao = self.expandir('num')
        if producao is None:
            return
        if producao == ['NUM_INT']:
            self.match('NUM_INT')
        elif producao == ['NUM_FLOAT']:
            self.match('NUM_FLOAT')
        else:
            self.match('MINUS')
            self.parseNumTipo()

    def parseNumTipo(self):
        #num_tipo ::= NUM_INT | NUM_FLOAT
        producao = self.expandir('num_tipo')
        if producao is None:
            return
        self.match(producao[0])

    def parseRpnTailNum(self):
        #rpn_tail_num ::= KEYWORD_RES | ID | num op_bin | stmt op_stmt_num
        producao = self.expandir('rpn_tail_num')
        if producao is None:
            return
        if producao == ['KEYWORD_RES']:
            self.match('KEYWORD_RES')
        elif producao == ['ID']:
            self.match('ID')
        elif producao[0] == 'num':
            self.parseNum()
            self.parseOpBin()
        else:
            self.parseStmt()
            self.parseOpStmtNum()

    def parseRpnTailStmt(self):
        #rpn_tail_stmt ::= ID | num op_bin | stmt op_stmt_stmt
        producao = self.expandir('rpn_tail_stmt')
        if producao is None:
            return
        if producao == ['ID']:
            self.match('ID')
        elif producao[0] == 'num':
            self.parseNum()
            self.parseOpBin()
        else:
            self.parseStmt()
            self.parseOpStmtStmt()

    def parseOpStmtNum(self):
        #op_stmt_num ::= KEYWORD_FOR | op_arit | op_rel
        producao = self.expandir('op_stmt_num')
        if producao is None:
            return
        if producao == ['KEYWORD_FOR']:
            self.match('KEYWORD_FOR')
        elif producao == ['op_arit']:
            self.parseOpArit()
        else:
            self.parseOpRel()

    def parseOpStmtStmt(self):
        #op_stmt_stmt ::= KEYWORD_IF | op_arit | op_rel
        producao = self.expandir('op_stmt_stmt')
        if producao is None:
            return
        if producao == ['KEYWORD_IF']:
            self.match('KEYWORD_IF')
        elif producao == ['op_arit']:
            self.parseOpArit()
        else:
            self.parseOpRel()

    def parseOpBin(self):
        # op_bin ::= op_arit | op_rel
        producao = self.expandir('op_bin')
        if producao is None:
            return
        if producao == ['op_arit']:
            self.parseOpArit()
        else:
            self.parseOpRel()

    def parseOpArit(self):
        # op_arit ::= PLUS | MINUS | MULT | DIV | INT_DIV | MOD | POW
        producao = self.expandir('op_arit')
        if producao is None:
            return
        self.match(producao[0])

    def parseOpRel(self):
        # op_rel ::= GT | LT | GTE | LTE | EQ | NEQ
        producao = self.expandir('op_rel')
        if producao is None:
            return
        self.match(producao[0])


# func principal

def parsear(_tokens_, tabela_ll1):
    parser = Parser(_tokens_, tabela_ll1)
    parser.parseProg()

    token_rest = parser.buffer.atual()
    if token_rest and token_rest.tipo != 'EOF':
        parser.erro(
            f"Erro sintático (linha {token_rest.linha}): "
            f"tokens inesperados após fim do programa ('{token_rest.tipo}')"
        )

    '''
    formatos dos passos de estrutura_derivacao :
        {'tipo': 'expansao', 'nao_terminal': str, 'producao': list[str]}
        {'tipo': 'match',    'terminal': str,     'token': Token}
        {'tipo': 'epsilon',  'nao_terminal': str}
    '''
    return {
        'estrutura_derivacao': parser.estrutura_derivacao,
        'erros'    : parser.erros
    }