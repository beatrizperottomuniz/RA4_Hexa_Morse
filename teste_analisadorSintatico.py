'''
Integrantes do grupo (ordem alfabética):
Beatriz Perotto Muniz - @beatrizperottomuniz

Nome do grupo no Canvas: RA3 6
'''
import unittest
import os
import json
import globalVars
from Token import TokenType
from analisadorLexico import parseExpressao
from leituraArquivo import lerArquivo
from leTokens import lerTokens
from construirGramatica import construirGramatica
from parsear import parsear

tabela = construirGramatica()['tabela']
arquivo_tks_temp = "_tokens_sintatico_teste.txt"


def resetar():
    globalVars.string_pool_global.pool.clear()
    globalVars.string_pool_global.strings.clear()
    globalVars.contador_linha_global = 1
    globalVars.total_linhas_global   = 1


def tokenizar(linhas_codigo):
    #Roda o léxico em uma lista de strings e retorna (tokens, tem_erro_lexico)
    resetar()
    tokens_lista = []
    tem_erro = False
    globalVars.total_linhas_global = len(linhas_codigo)
    for linha in linhas_codigo:
        tokens_linha = []
        parseExpressao(linha, tokens_linha)
        tokens_lista.extend(tokens_linha)
        if any(t.tipo == TokenType.UNKNOWN for t in tokens_linha):
            tem_erro = True
        globalVars.contador_linha_global += 1
    dados = {
        "string_pool": globalVars.string_pool_global.strings,
        "tokens": [{"tipo": t.tipo, "linha": t.linha,
                    "coluna": t.coluna, "simbolo_id": t.simbolo_id}
                   for t in tokens_lista]
    }
    with open(arquivo_tks_temp, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)
    return tokens_lista, tem_erro


def analisar(linhas_codigo):
    #Roda léxico + parser. Retorna (erros_lexicos, erros_sintaticos)
    _, tem_erro_lexico = tokenizar(linhas_codigo)
    resetar()
    tokens = lerTokens(arquivo_tks_temp)
    resultado = parsear(tokens, tabela)
    return tem_erro_lexico, resultado['erros']


def programa(expressoes):
    #Envolve expressões em (START)...(END)
    return ["(START)"] + expressoes + ["(END)"]


class TestErrosLexicos(unittest.TestCase):

    def tearDown(self):
        if os.path.exists(arquivo_tks_temp):
            os.remove(arquivo_tks_temp)
        resetar()

    def test_caractere_arroba(self):
        _, tem_erro = tokenizar(["(3 4 @)"])
        self.assertTrue(tem_erro)

    def test_caractere_ampersand(self):
        _, tem_erro = tokenizar(["(3 & 4)"])
        self.assertTrue(tem_erro)

    def test_float_invalido(self):
        tokens, tem_erro = tokenizar(["(3.5.2 2 +)"])
        self.assertTrue(tem_erro or any(t.tipo == TokenType.UNKNOWN for t in tokens))

    def test_expressao_valida_sem_erro_lexico(self):
        _, tem_erro = tokenizar(["(3 4 +)"])
        self.assertFalse(tem_erro)


class TestExpressoesSimples(unittest.TestCase):

    def tearDown(self):
        if os.path.exists(arquivo_tks_temp):
            os.remove(arquivo_tks_temp)
        resetar()

    def _ok(self, expr):
        erro_lex, erro_sin = analisar(programa([expr]))
        self.assertFalse(erro_lex, f"Erro léxico inesperado em: {expr}")
        self.assertEqual(erro_sin, [], f"Erro sintático inesperado em: {expr}")

    def test_adicao(self):
        self._ok("(3 4 +)")

    def test_subtracao(self):
        self._ok("(10 3 -)")

    def test_multiplicacao(self):
        self._ok("(2 5 *)")

    def test_divisao_real(self):
        self._ok("(8 2 |)")

    def test_divisao_inteira(self):
        self._ok("(9 3 /)")

    def test_modulo(self):
        self._ok("(10 3 %)")

    def test_potenciacao(self):
        self._ok("(2 3 ^)")

    def test_float(self):
        self._ok("(3.14 2.0 +)")

    def test_numero_negativo(self):
        self._ok("(-3 4 +)")

    def test_atribuicao(self):
        self._ok("(10 X)")

    def test_leitura(self):
        erro_lex, erro_sin = analisar(programa(["(10 X)", "(X)"]))
        self.assertFalse(erro_lex)
        self.assertEqual(erro_sin, [])

    def test_res(self):
        erro_lex, erro_sin = analisar(programa(["(3 4 +)", "(1 RES)"]))
        self.assertFalse(erro_lex)
        self.assertEqual(erro_sin, [])

    def test_programa_minimo(self):
        erro_lex, erro_sin = analisar(["(START)", "(END)"])
        self.assertFalse(erro_lex)
        self.assertEqual(erro_sin, [])


class TestExpressoesAninhadas(unittest.TestCase):

    def tearDown(self):
        if os.path.exists(arquivo_tks_temp):
            os.remove(arquivo_tks_temp)
        resetar()

    def _ok(self, expr):
        erro_lex, erro_sin = analisar(programa([expr]))
        self.assertFalse(erro_lex)
        self.assertEqual(erro_sin, [])

    def test_dois_niveis(self):
        self._ok("((3 2 +) 4 *)")

    def test_tres_niveis(self):
        self._ok("(((2 3 +) 4 *) 5 -)")

    def test_quatro_niveis(self):
        self._ok("((((2 3 +) 4 *) 5 -) 6 |)")

    def test_dois_stmts(self):
        self._ok("((3 2 +) (4 5 *) -)")

    def test_variavel_aninhada(self):
        erro_lex, erro_sin = analisar(programa(["(5 X)", "((X) 2 *)"]))
        self.assertFalse(erro_lex)
        self.assertEqual(erro_sin, [])

    def test_multiplas_linhas(self):
        erro_lex, erro_sin = analisar(programa(["(3 4 +)", "(5 2 -)", "((1 2 +) 3 *)"]))
        self.assertFalse(erro_lex)
        self.assertEqual(erro_sin, [])

class TestEstruturasControle(unittest.TestCase):

    def tearDown(self):
        if os.path.exists(arquivo_tks_temp):
            os.remove(arquivo_tks_temp)
        resetar()

    def _ok(self, expr):
        erro_lex, erro_sin = analisar(programa([expr]))
        self.assertFalse(erro_lex)
        self.assertEqual(erro_sin, [])

    def test_if_com_eq(self):
        self._ok("((5 5 ==) (1 2 +) IF)")

    def test_if_com_gt(self):
        self._ok("((10 5 >) (3 2 -) IF)")

    def test_if_com_lt(self):
        self._ok("((3 5 <) (1 1 +) IF)")

    def test_if_com_gte(self):
        self._ok("((5 5 >=) (2 2 *) IF)")

    def test_if_com_lte(self):
        self._ok("((3 5 <=) (4 4 +) IF)")

    def test_if_com_neq(self):
        self._ok("((3 5 !=) (1 2 +) IF)")

    def test_for_simples(self):
        self._ok("(3 (1 2 +) FOR)")

    def test_for_aninhado(self):
        self._ok("(2 ((3 4 +) 2 *) FOR)")

    def test_if_aninhado_em_for(self):
        self._ok("(3 ((5 5 ==) (1 2 +) IF) FOR)")

class TestEntradasInvalidas(unittest.TestCase):

    def tearDown(self):
        if os.path.exists(arquivo_tks_temp):
            os.remove(arquivo_tks_temp)
        resetar()

    def _tem_erro(self, linhas):
        erro_lex, erro_sin = analisar(linhas)
        return erro_lex or len(erro_sin) > 0

    def test_operador_no_inicio(self):
        self.assertTrue(self._tem_erro(programa(["(+ 3 4)"])))

    def test_expressao_vazia(self):
        self.assertTrue(self._tem_erro(programa(["()"])))

    def test_sem_start(self):
        self.assertTrue(self._tem_erro(["(3 4 +)", "(END)"]))

    def test_sem_end(self):
        self.assertTrue(self._tem_erro(["(START)", "(3 4 +)"]))

    def test_operandos_demais(self):
        self.assertTrue(self._tem_erro(programa(["(3 4 + 5)"])))

    def test_erro_indica_linha(self):
        _, erros = analisar(programa(["(+ 3 4)"]))
        self.assertTrue(any('linha' in e.lower() for e in erros))

class TestCasosExtremos(unittest.TestCase):

    def tearDown(self):
        if os.path.exists(arquivo_tks_temp):
            os.remove(arquivo_tks_temp)
        resetar()

    def test_aninhamento_profundo_5_niveis(self):
        expr = "(((((1 2 +) 3 *) 4 -) 5 |) 2 ^)"
        erro_lex, erro_sin = analisar(programa([expr]))
        self.assertFalse(erro_lex)
        self.assertEqual(erro_sin, [])

    def test_programa_minimo(self):
        erro_lex, erro_sin = analisar(["(START)", "(END)"])
        self.assertFalse(erro_lex)
        self.assertEqual(erro_sin, [])

    def test_muitas_linhas(self):
        exprs = ["(3 4 +)"] * 10
        erro_lex, erro_sin = analisar(programa(exprs))
        self.assertFalse(erro_lex)
        self.assertEqual(erro_sin, [])

    def test_for_dentro_de_for(self):
        expr = "(2 (3 (1 2 +) FOR) FOR)"
        erro_lex, erro_sin = analisar(programa([expr]))
        self.assertFalse(erro_lex)
        self.assertEqual(erro_sin, [])


if __name__ == '__main__':
    unittest.main()
