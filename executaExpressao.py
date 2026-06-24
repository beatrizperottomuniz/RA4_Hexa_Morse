'''
Integrantes do grupo (ordem alfabética):
Beatriz Perotto Muniz - @beatrizperottomuniz

Nome do grupo no Canvas: RA3 6
'''
from Token import TokenType
from globalVars import string_pool_global

def resgatarLexema(token) -> str:
    operadores = {TokenType.PLUS: "+", TokenType.MINUS: "-", TokenType.MULT: "*", 
                  TokenType.DIV: "/", TokenType.INT_DIV: "//", TokenType.MOD: "%", TokenType.POW: "^"}
    if token.tipo in operadores:
        return operadores[token.tipo]
    if token.simbolo_id is not None:
        return string_pool_global.obterString(token.simbolo_id)
    return "" 

class Interpretador:
    def __init__(self, tokens, resultados, memoria):
        # filtra
        self.tokens = [t for t in tokens
                       if t.tipo not in (TokenType.EOF,
                                        TokenType.KEYWORD_START,
                                        TokenType.KEYWORD_END)]
        self.pos = 0
        self.resultados = resultados
        self.memoria = memoria

    def atual(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consumir(self):
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def peekOpAposStmt(self):
        pos = self.pos
        if pos >= len(self.tokens) or self.tokens[pos].tipo != TokenType.LPAREN:
            return None
        pos += 1
        depth = 1
        while pos < len(self.tokens) and depth > 0:
            if self.tokens[pos].tipo == TokenType.LPAREN:
                depth += 1
            elif self.tokens[pos].tipo == TokenType.RPAREN:
                depth -= 1
            pos += 1
        return self.tokens[pos].tipo if pos < len(self.tokens) else None

    def pularStmt(self):
        self.pos += 1   # LPAREN
        depth = 1
        while self.pos < len(self.tokens) and depth > 0:
            if self.tokens[self.pos].tipo == TokenType.LPAREN:
                depth += 1
            elif self.tokens[self.pos].tipo == TokenType.RPAREN:
                depth -= 1
            self.pos += 1


    def avaliarStmt(self):
        self.consumir()            # LPAREN
        valor = self.avaliarRpn()
        self.consumir()            # RPAREN
        return valor

    def avaliarNum(self):
        t = self.atual()
        if t.tipo == TokenType.MINUS:
            self.consumir()
            return -float(resgatarLexema(self.consumir()))
        return float(resgatarLexema(self.consumir()))

    def avaliarRpn(self):
        t = self.atual()

        if t.tipo == TokenType.LPAREN:
            primeiro = self.avaliarStmt()
            return self.avaliarRpnTailStmt(primeiro)

        if t.tipo in (TokenType.NUM_INT, TokenType.NUM_FLOAT, TokenType.MINUS):
            num = self.avaliarNum()
            return self.avaliarRpnTailNum(num)

        if t.tipo == TokenType.ID:
            nome = resgatarLexema(self.consumir())
            return self.memoria.get(nome, 0.0)

        # ("texto" MORSE) retorno void
        if t.tipo == TokenType.STRING:
            self.consumir()  # consome STRING
            self.consumir()  # consome KEYWORD_MORSE
            return 0.0

        return 0.0

    def avaliarRpnTailNum(self, primeiro):
        t = self.atual()
        if t is None or t.tipo == TokenType.RPAREN:
            return primeiro

        # (N RES)
        if t.tipo == TokenType.KEYWORD_RES:
            self.consumir()
            n = int(primeiro)
            i = len(self.resultados) - n
            return self.resultados[i] if 0 <= i < len(self.resultados) else 0.0

        # (N VAR) — atrib
        if t.tipo == TokenType.ID:
            nome = resgatarLexema(self.consumir())
            self.memoria[nome] = primeiro
            return primeiro

        # (N num op) — op bin com terminal
        if t.tipo in (TokenType.NUM_INT, TokenType.NUM_FLOAT, TokenType.MINUS):
            segundo = self.avaliarNum()
            op = self.consumir()
            return self.aplicarOp(primeiro, segundo, op.tipo)

        # FOR ou op com sub expr
        if t.tipo == TokenType.LPAREN:
            op_tipo = self.peekOpAposStmt()

            if op_tipo == TokenType.KEYWORD_FOR:
                n      = int(primeiro)
                inicio = self.pos
                self.pularStmt()
                corpo  = self.tokens[inicio:self.pos]
                self.consumir()                        # FOR
                resultado = 0.0
                for _ in range(n):
                    sub = Interpretador(corpo, self.resultados, self.memoria)
                    resultado = sub.avaliarStmt()
                return 0.0

            segundo = self.avaliarStmt()
            op = self.consumir()
            return self.aplicarOp(primeiro, segundo, op.tipo)

        return primeiro

    def avaliarRpnTailStmt(self, primeiro):
        t = self.atual()
        if t is None or t.tipo == TokenType.RPAREN:
            return primeiro

        # ((stmt) VAR) — atrib
        if t.tipo == TokenType.ID:
            nome = resgatarLexema(self.consumir())
            self.memoria[nome] = primeiro
            return primeiro

        # ((stmt) num op) — operação bin com literal
        if t.tipo in (TokenType.NUM_INT, TokenType.NUM_FLOAT, TokenType.MINUS):
            segundo = self.avaliarNum()
            op = self.consumir()
            return self.aplicarOp(primeiro, segundo, op.tipo)

        # ((stmt) (stmt) op_stmt_stmt) — IF ou op
        if t.tipo == TokenType.LPAREN:
            op_tipo = self.peekOpAposStmt()

            # (cond corpo IF)
            if op_tipo == TokenType.KEYWORD_IF:
                condicao = primeiro
                if condicao != 0.0:
                    corpo = self.avaliarStmt()
                    self.consumir()                    # IF
                    return 0.0
                else:
                    self.pularStmt()
                    self.consumir()                    # IF
                    return 0.0

            segundo = self.avaliarStmt()
            op = self.consumir()
            return self.aplicarOp(primeiro, segundo, op.tipo)

        return primeiro

    # ops

    def aplicarOp(self, esq, dir, tipo):
        if tipo == TokenType.PLUS:    return esq + dir
        if tipo == TokenType.MINUS:   return esq - dir
        if tipo == TokenType.MULT:    return esq * dir
        if tipo == TokenType.DIV:     return esq / dir
        if tipo == TokenType.INT_DIV:
            return float(int(esq / dir))
        if tipo == TokenType.MOD:
            return esq - float(int(esq / dir)) * dir
        if tipo == TokenType.POW:
            acc = 1.0
            for _ in range(int(dir)):
                acc *= esq
            return acc
        if tipo == TokenType.EQ:  return 1.0 if esq == dir else 0.0
        if tipo == TokenType.NEQ: return 1.0 if esq != dir else 0.0
        if tipo == TokenType.GT:  return 1.0 if esq >  dir else 0.0
        if tipo == TokenType.LT:  return 1.0 if esq <  dir else 0.0
        if tipo == TokenType.GTE: return 1.0 if esq >= dir else 0.0
        if tipo == TokenType.LTE: return 1.0 if esq <= dir else 0.0
        return 0.0


# func principal

def executarExpressao(tokens: list, resultados: list, memoria: dict) -> None:
    interp    = Interpretador(tokens, resultados, memoria)
    resultado = interp.avaliarStmt()
    resultados.append(resultado)
