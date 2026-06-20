'''
Integrantes do grupo (ordem alfabética):
Beatriz Perotto Muniz - @beatrizperottomuniz

Nome do grupo no Canvas: RA3 6
'''
import unittest
import os
import json
import globalVars
from stringPool import StringPool
from Token import TokenType
from analisadorLexico import parseExpressao
from leTokens import lerTokens
from construirGramatica import construirGramatica
from parsear import parsear
from gerarArvore import gerarArvore, noParaDict, arqv_json, arqv_txt, arqv_png, arqv_md
from prepararEntradaSemantica import lerArvore

tabela = construirGramatica()['tabela']
arquivo_tks_temp = "_tokens_semantico_teste.txt"


def resetar():
    globalVars.string_pool_global.pool.clear()
    globalVars.string_pool_global.strings.clear()
    globalVars.contador_linha_global = 1
    globalVars.total_linhas_global = 1
    globalVars.em_comentario_global = False


def tokenizar(linhas_codigo):
    # roda o lexico em uma lista de strings e retorna (tokens, tem_erro_lexico, comentario_aberto)
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

    # erro de comentario nao fechado
    comentario_aberto = globalVars.em_comentario_global
    if comentario_aberto:
        tem_erro = True
        globalVars.em_comentario_global = False

    dados = {
        "string_pool": globalVars.string_pool_global.strings,
        "tokens": [{"tipo": t.tipo, "linha": t.linha,
                    "coluna": t.coluna, "simbolo_id": t.simbolo_id}
                   for t in tokens_lista]
    }
    with open(arquivo_tks_temp, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)
    return tokens_lista, tem_erro, comentario_aberto


def analisar(linhas_codigo):
    # roda lexico + parser. retorna (erro_lexico, erros_sintaticos)
    _, tem_erro_lexico, _ = tokenizar(linhas_codigo)
    resetar()
    tokens = lerTokens(arquivo_tks_temp)
    resultado = parsear(tokens, tabela)
    return tem_erro_lexico, resultado['erros']


def programa(expressoes):
    # expressoes + (START)...(END)
    return ["(START)"] + expressoes + ["(END)"]


class TestComentariosValidos(unittest.TestCase):

    def tearDown(self):
        if os.path.exists(arquivo_tks_temp):
            os.remove(arquivo_tks_temp)
        resetar()

    def test_comentario_linha_inteira(self):
        tokens, tem_erro, _ = tokenizar(["*{ isso é um comentário inteiro }*"])
        self.assertFalse(tem_erro)
        tokens_sem_eof = [t for t in tokens if t.tipo != TokenType.EOF]
        self.assertEqual(len(tokens_sem_eof), 0)

    def test_comentario_fim_de_linha(self):
        tokens, tem_erro, _ = tokenizar(["(3 4 +) *{ soma }*"])
        self.assertFalse(tem_erro)
        tipos = [t.tipo for t in tokens]
        self.assertIn(TokenType.LPAREN, tipos)
        self.assertIn(TokenType.PLUS, tipos)
        self.assertNotIn(TokenType.COMMENT, tipos)

    def test_comentario_entre_expressoes(self):
        erro_lex, erro_sin = analisar(programa([
            "(3 4 +)",
            "*{ comentário entre expressões }*",
            "(5 2 -)"
        ]))
        self.assertFalse(erro_lex)
        self.assertEqual(erro_sin, [])

    def test_comentario_multilinhas(self):
        erro_lex, erro_sin = analisar(programa([
            "(3 4 +) *{ abre aqui",
            "ainda comentario",
            "fecha aqui }* (5 2 -)"
        ]))
        self.assertFalse(erro_lex)
        self.assertEqual(erro_sin, [])

    def test_multiplos_comentarios(self):
        erro_lex, erro_sin = analisar(programa([
            "*{ primeiro }* (3 4 +) *{ segundo }*"
        ]))
        self.assertFalse(erro_lex)
        self.assertEqual(erro_sin, [])

    def test_comentario_nao_aninhado(self):
        # segundo *{ dentro do comentario é ignorado, fecha no primeiro }*
        tokens, tem_erro, _ = tokenizar(["*{ abre *{ outro }*"])
        self.assertFalse(tem_erro)

    def test_tokens_nao_gerados_para_comentario(self):
        tokens, _, _ = tokenizar(["*{ qualquer coisa }*"])
        tokens_sem_eof = [t for t in tokens if t.tipo != TokenType.EOF]
        self.assertEqual(len(tokens_sem_eof), 0)


class TestTokensInvalidos(unittest.TestCase):

    def tearDown(self):
        if os.path.exists(arquivo_tks_temp):
            os.remove(arquivo_tks_temp)
        resetar()

    def test_caractere_desconhecido(self):
        tokens, tem_erro, _ = tokenizar(["(3 @ 4 +)"])
        self.assertTrue(tem_erro)
        self.assertTrue(any(t.tipo == TokenType.UNKNOWN for t in tokens))

    def test_caractere_desconhecido_nao_interfere_nos_outros_tokens(self):
        tokens, tem_erro, _ = tokenizar(["(3 @ 4 +)"])
        self.assertTrue(tem_erro)
        tipos = [t.tipo for t in tokens]
        self.assertIn(TokenType.LPAREN, tipos)
        self.assertIn(TokenType.PLUS, tipos)


class TestComentariosInvalidos(unittest.TestCase):

    def tearDown(self):
        if os.path.exists(arquivo_tks_temp):
            os.remove(arquivo_tks_temp)
        resetar()

    def test_comentario_nao_fechado_antes_do_end(self):
        # *{ sem fechar engole o END — erro sintatico ou lexico
        _, tem_erro, comentario_aberto = tokenizar([
            "(START)",
            "(3 4 +)",
            "*{ nao fechei",
            "(END)"
        ])
        self.assertTrue(tem_erro or comentario_aberto)

    def test_comentario_nao_fechado_depois_do_end(self):
        # *{ sem fechar depois do END — detectado pelo check de em_comentario_global
        _, tem_erro, comentario_aberto = tokenizar([
            "(START)",
            "(3 4 +)",
            "(END)",
            "*{ nao fechei"
        ])
        self.assertTrue(comentario_aberto)
        self.assertTrue(tem_erro)

    def test_fechamento_sem_abertura(self):
        # }* sem *{ — gera UNKNOWN para }
        tokens, tem_erro, _ = tokenizar(["(3 4 +) }*"])
        self.assertTrue(tem_erro or any(t.tipo == TokenType.UNKNOWN for t in tokens))

    def test_duplo_fechamento(self):
        # *{ }* }* — segundo }* gera erro
        tokens, tem_erro, _ = tokenizar(["*{ comentario }* (3 4 +) }*"])
        self.assertTrue(tem_erro or any(t.tipo == TokenType.UNKNOWN for t in tokens))


class TestIntegracaoComComentarios(unittest.TestCase):

    def tearDown(self):
        if os.path.exists(arquivo_tks_temp):
            os.remove(arquivo_tks_temp)
        resetar()

    def test_programa_valido_com_comentarios(self):
        erro_lex, erro_sin = analisar([
            "*{ programa de teste }*",
            "(START)",
            "*{ operacoes basicas }*",
            "(3 4 +) *{ soma }*",
            "(10 2 -)",
            "*{ estrutura de controle }*",
            "((5 5 ==) (1 2 +) IF)",
            "(END)"
        ])
        self.assertFalse(erro_lex)
        self.assertEqual(erro_sin, [])

    def test_comentario_nao_interfere_em_tokens(self):
        # tokens gerados sao os mesmos com ou sem comentario
        tokens_sem, _, _ = tokenizar(["(3 4 +)"])
        resetar()
        tokens_com, _, _ = tokenizar(["(3 4 +) *{ comentario }*"])
        tipos_sem = [t.tipo for t in tokens_sem]
        tipos_com = [t.tipo for t in tokens_com]
        self.assertEqual(tipos_sem, tipos_com)

    def test_programa_valido_retorna_sem_erros(self):
        erro_lex, erro_sin = analisar(programa([
            "*{ comentario }*",
            "(5 3 +)",
            "(2 RES)"
        ]))
        self.assertFalse(erro_lex)
        self.assertEqual(erro_sin, [])

    def test_expressao_vazia_gera_erro_sintatico(self):                                                                             
        erro_lex, erro_sin = analisar(programa([                           
            "()"                                                           
        ]))                                        
        self.assertFalse(erro_lex)                                         
        self.assertTrue(len(erro_sin) > 0)    


class TestArvoreJSON(unittest.TestCase):

    arquivos_texto = [arquivo_tks_temp, arqv_json, arqv_txt, arqv_md]

    def setUp(self):
        self._backups_texto = {}
        self._backup_png = None
        for arq in self.arquivos_texto:
            if os.path.exists(arq):
                with open(arq, 'r', encoding='utf-8') as f:
                    self._backups_texto[arq] = f.read()
        if os.path.exists(arqv_png):
            with open(arqv_png, 'rb') as f:
                self._backup_png = f.read()

    def tearDown(self):
        for arq in self.arquivos_texto:
            if arq in self._backups_texto:
                with open(arq, 'w', encoding='utf-8') as f:
                    f.write(self._backups_texto[arq])
            elif os.path.exists(arq):
                os.remove(arq)
        if self._backup_png is not None:
            with open(arqv_png, 'wb') as f:
                f.write(self._backup_png)
        elif os.path.exists(arqv_png):
            os.remove(arqv_png)
        resetar()

    def test_arvore_gerada_igual_arvore_lida(self):
        linhas = programa(["(3 4 +)", "(5 2 -)"])
        tokenizar(linhas)
        resetar()
        tokens = lerTokens(arquivo_tks_temp)
        resultado = parsear(tokens, tabela)
        estrutura = resultado['estrutura_derivacao']
        self.assertIsNotNone(estrutura)

        arvore_gerada = gerarArvore(estrutura)
        arvore_lida = lerArvore()

        self.assertIsNotNone(arvore_lida)
        self.assertEqual(noParaDict(arvore_gerada), noParaDict(arvore_lida))



if __name__ == '__main__':
    unittest.main()
