'''
Integrantes do grupo (ordem alfabética):
Beatriz Perotto Muniz - @beatrizperottomuniz

Nome do grupo no Canvas: RA3 6
'''
import unittest
from Token import Token, TokenType
from construirGramatica import construirGramatica
from parsear import parsear

resultado_gramatica = construirGramatica()
tabela  = resultado_gramatica['tabela']
first   = resultado_gramatica['first']
follow  = resultado_gramatica['follow']


def tk(tipo, linha=1, coluna=1):
    return Token(tipo, linha, coluna, 0)

def programa(*linhas):
    #monta (START) + linhas + (END) + EOF
    tokens = [tk(TokenType.LPAREN), tk(TokenType.KEYWORD_START), tk(TokenType.RPAREN)]
    for l in linhas:
        tokens.extend(l)
    tokens += [tk(TokenType.LPAREN), tk(TokenType.KEYWORD_END), tk(TokenType.RPAREN),
               tk(TokenType.EOF)]
    return tokens

def valido(tokens):
    return parsear(tokens, tabela)['erros'] == []

def erros(tokens):
    return parsear(tokens, tabela)['erros']

def derivacao(tokens):
    return parsear(tokens, tabela)['estrutura_derivacao']

def tem_expansao(deriv, nt):
    return any(p['tipo'] == 'expansao' and p['nao_terminal'] == nt for p in deriv)

def tem_match(deriv, tipo_token):
    return any(p['tipo'] == 'match' and p['terminal'] == tipo_token for p in deriv)


class TestExpressoesValidas(unittest.TestCase):

    def test_3_14_2_0_mais(self):
        #(3.14 2.0 +)
        linha = [tk(TokenType.LPAREN, 2), tk(TokenType.NUM_FLOAT, 2),
                 tk(TokenType.NUM_FLOAT, 2), tk(TokenType.PLUS, 2),
                 tk(TokenType.RPAREN, 2)]
        self.assertTrue(valido(programa(linha)))

    def test_aninhado_soma_produto(self):
        #((A B +) (C D *) /)
        inner1 = [tk(TokenType.LPAREN, 2), tk(TokenType.NUM_INT, 2),
                  tk(TokenType.NUM_INT, 2), tk(TokenType.PLUS, 2), tk(TokenType.RPAREN, 2)]
        inner2 = [tk(TokenType.LPAREN, 2), tk(TokenType.NUM_INT, 2),
                  tk(TokenType.NUM_INT, 2), tk(TokenType.MULT, 2), tk(TokenType.RPAREN, 2)]
        linha = [tk(TokenType.LPAREN, 2)] + inner1 + inner2 + \
                [tk(TokenType.DIV, 2), tk(TokenType.RPAREN, 2)]
        self.assertTrue(valido(programa(linha)))

    def test_todas_operacoes_aritmeticas(self):
        #Cada operador aritmético deve ser aceito
        for op in [TokenType.PLUS, TokenType.MINUS, TokenType.MULT,
                   TokenType.DIV, TokenType.INT_DIV, TokenType.MOD, TokenType.POW]:
            with self.subTest(op=op):
                linha = [tk(TokenType.LPAREN, 2), tk(TokenType.NUM_INT, 2),
                         tk(TokenType.NUM_INT, 2), tk(op, 2), tk(TokenType.RPAREN, 2)]
                self.assertTrue(valido(programa(linha)))

    def test_todos_operadores_relacionais(self):
        #Cada operador relacional deve ser aceito
        for op in [TokenType.GT, TokenType.LT, TokenType.GTE,
                   TokenType.LTE, TokenType.EQ, TokenType.NEQ]:
            with self.subTest(op=op):
                linha = [tk(TokenType.LPAREN, 2), tk(TokenType.NUM_INT, 2),
                         tk(TokenType.NUM_INT, 2), tk(op, 2), tk(TokenType.RPAREN, 2)]
                self.assertTrue(valido(programa(linha)))

    def test_numero_negativo(self):
        #(-3 4 +) — número negativo válido
        linha = [tk(TokenType.LPAREN, 2), tk(TokenType.MINUS, 2),
                 tk(TokenType.NUM_INT, 2), tk(TokenType.NUM_INT, 2),
                 tk(TokenType.PLUS, 2), tk(TokenType.RPAREN, 2)]
        self.assertTrue(valido(programa(linha)))

    def test_atribuicao_variavel(self):
        #(5 X)
        linha = [tk(TokenType.LPAREN, 2), tk(TokenType.NUM_INT, 2),
                 tk(TokenType.ID, 2), tk(TokenType.RPAREN, 2)]
        self.assertTrue(valido(programa(linha)))

    def test_leitura_variavel(self):
        #(X)
        linha = [tk(TokenType.LPAREN, 2), tk(TokenType.ID, 2), tk(TokenType.RPAREN, 2)]
        self.assertTrue(valido(programa(linha)))

    def test_res(self):
        #(2 RES)
        linha = [tk(TokenType.LPAREN, 2), tk(TokenType.NUM_INT, 2),
                 tk(TokenType.KEYWORD_RES, 2), tk(TokenType.RPAREN, 2)]
        self.assertTrue(valido(programa(linha)))

    def test_if(self):
        #((5 5 ==) (1 2 +) IF)
        cond = [tk(TokenType.LPAREN, 2), tk(TokenType.NUM_INT, 2),
                tk(TokenType.NUM_INT, 2), tk(TokenType.EQ, 2), tk(TokenType.RPAREN, 2)]
        corpo = [tk(TokenType.LPAREN, 2), tk(TokenType.NUM_INT, 2),
                 tk(TokenType.NUM_INT, 2), tk(TokenType.PLUS, 2), tk(TokenType.RPAREN, 2)]
        linha = [tk(TokenType.LPAREN, 2)] + cond + corpo + \
                [tk(TokenType.KEYWORD_IF, 2), tk(TokenType.RPAREN, 2)]
        self.assertTrue(valido(programa(linha)))

    def test_for(self):
        #(3 (1 2 +) FOR)
        corpo = [tk(TokenType.LPAREN, 2), tk(TokenType.NUM_INT, 2),
                 tk(TokenType.NUM_INT, 2), tk(TokenType.PLUS, 2), tk(TokenType.RPAREN, 2)]
        linha = [tk(TokenType.LPAREN, 2), tk(TokenType.NUM_INT, 2)] + corpo + \
                [tk(TokenType.KEYWORD_FOR, 2), tk(TokenType.RPAREN, 2)]
        self.assertTrue(valido(programa(linha)))


class TestExpressoesInvalidas(unittest.TestCase):

    def test_a_b_mais_c_erro(self):
        #(A B + C)
        linha = [tk(TokenType.LPAREN, 2), tk(TokenType.NUM_INT, 2),
                 tk(TokenType.NUM_INT, 2), tk(TokenType.PLUS, 2),
                 tk(TokenType.NUM_INT, 2), tk(TokenType.RPAREN, 2)]
        self.assertTrue(len(erros(programa(linha))) > 0)

    def test_operador_no_inicio(self):
        #(+ 3 4)
        linha = [tk(TokenType.LPAREN, 2), tk(TokenType.PLUS, 2),
                 tk(TokenType.NUM_INT, 2), tk(TokenType.NUM_INT, 2),
                 tk(TokenType.RPAREN, 2)]
        self.assertTrue(len(erros(programa(linha))) > 0)

    def test_expressao_vazia(self):
        #()
        linha = [tk(TokenType.LPAREN, 2), tk(TokenType.RPAREN, 2)]
        self.assertTrue(len(erros(programa(linha))) > 0)

    def test_sem_start(self):
        #programa sem (START)
        tokens = [tk(TokenType.LPAREN), tk(TokenType.KEYWORD_END),
                  tk(TokenType.RPAREN), tk(TokenType.EOF)]
        self.assertTrue(len(erros(tokens)) > 0)

    def test_sem_end(self):
        #programa sem (END)
        tokens = [tk(TokenType.LPAREN), tk(TokenType.KEYWORD_START),
                  tk(TokenType.RPAREN), tk(TokenType.EOF)]
        self.assertTrue(len(erros(tokens)) > 0)

    def test_tokens_apos_end(self):
        #Tokens após (END) 
        tokens = [tk(TokenType.LPAREN), tk(TokenType.KEYWORD_START), tk(TokenType.RPAREN),
                  tk(TokenType.LPAREN), tk(TokenType.KEYWORD_END), tk(TokenType.RPAREN),
                  tk(TokenType.NUM_INT), tk(TokenType.EOF)]
        self.assertTrue(len(erros(tokens)) > 0)


class TestMensagensErro(unittest.TestCase):

    def test_erro_contem_linha(self):
        #número de linha
        linha = [tk(TokenType.LPAREN, 5), tk(TokenType.PLUS, 5), tk(TokenType.RPAREN, 5)]
        msgs = erros(programa(linha))
        self.assertTrue(any('5' in msg for msg in msgs))

    def test_erro_contem_token_encontrado(self):
        #token foi encontrado
        linha = [tk(TokenType.LPAREN, 2), tk(TokenType.PLUS, 2), tk(TokenType.RPAREN, 2)]
        msgs = erros(programa(linha))
        self.assertTrue(any('PLUS' in msg for msg in msgs))

    def test_erro_contem_esperados(self):
        #istar tokens esperados
        linha = [tk(TokenType.LPAREN, 2), tk(TokenType.PLUS, 2), tk(TokenType.RPAREN, 2)]
        msgs = erros(programa(linha))
        self.assertTrue(any('Esperados' in msg or 'esperado' in msg for msg in msgs))

    def test_multiplos_erros_reportados(self):
        #reportar mais de um erro quando possível
        linha1 = [tk(TokenType.LPAREN, 2), tk(TokenType.PLUS, 2), tk(TokenType.RPAREN, 2)]
        linha2 = [tk(TokenType.LPAREN, 3), tk(TokenType.PLUS, 3), tk(TokenType.RPAREN, 3)]
        self.assertTrue(len(erros(programa(linha1, linha2))) > 1)


class TestDerivacao(unittest.TestCase):

    def test_derivacao_nao_vazia(self):
        tokens = programa()
        self.assertTrue(len(derivacao(tokens)) > 0)

    def test_derivacao_tem_expansao_e_match(self):
        tokens = programa()
        d = derivacao(tokens)
        self.assertTrue(any(p['tipo'] == 'expansao' for p in d))
        self.assertTrue(any(p['tipo'] == 'match' for p in d))

    def test_derivacao_expande_prog(self):
        tokens = programa()
        self.assertTrue(tem_expansao(derivacao(tokens), 'prog'))

    def test_derivacao_expande_rpn(self):
        linha = [tk(TokenType.LPAREN, 2), tk(TokenType.NUM_INT, 2),
                 tk(TokenType.NUM_INT, 2), tk(TokenType.PLUS, 2), tk(TokenType.RPAREN, 2)]
        self.assertTrue(tem_expansao(derivacao(programa(linha)), 'rpn'))

    def test_derivacao_match_if(self):
        cond = [tk(TokenType.LPAREN, 2), tk(TokenType.NUM_INT, 2),
                tk(TokenType.NUM_INT, 2), tk(TokenType.EQ, 2), tk(TokenType.RPAREN, 2)]
        corpo = [tk(TokenType.LPAREN, 2), tk(TokenType.NUM_INT, 2),
                 tk(TokenType.NUM_INT, 2), tk(TokenType.PLUS, 2), tk(TokenType.RPAREN, 2)]
        linha = [tk(TokenType.LPAREN, 2)] + cond + corpo + \
                [tk(TokenType.KEYWORD_IF, 2), tk(TokenType.RPAREN, 2)]
        self.assertTrue(tem_match(derivacao(programa(linha)), 'KEYWORD_IF'))

    def test_derivacao_match_for(self):
        corpo = [tk(TokenType.LPAREN, 2), tk(TokenType.NUM_INT, 2),
                 tk(TokenType.NUM_INT, 2), tk(TokenType.PLUS, 2), tk(TokenType.RPAREN, 2)]
        linha = [tk(TokenType.LPAREN, 2), tk(TokenType.NUM_INT, 2)] + corpo + \
                [tk(TokenType.KEYWORD_FOR, 2), tk(TokenType.RPAREN, 2)]
        self.assertTrue(tem_match(derivacao(programa(linha)), 'KEYWORD_FOR'))

    def test_derivacao_com_erro_retorna_lista(self):
        #mesmo com erros, estrutura_derivacao deve ser uma lista
        linha = [tk(TokenType.LPAREN, 2), tk(TokenType.PLUS, 2), tk(TokenType.RPAREN, 2)]
        r = parsear(programa(linha), tabela)
        self.assertIsInstance(r['estrutura_derivacao'], list)


if __name__ == '__main__':
    unittest.main()
