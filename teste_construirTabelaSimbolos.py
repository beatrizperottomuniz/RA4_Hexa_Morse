'''
Integrantes do grupo (ordem alfabética):
Beatriz Perotto Muniz - @beatrizperottomuniz

Nome do grupo no Canvas: RA3 6
'''
import unittest
import os
import json
import tempfile
import globalVars
from AnalisadorSintatico import arquivo_tokens
from gerarArvore import arqv_json, arqv_txt, arqv_png, arqv_md
from prepararEntradaSemantica import prepararEntradaSemantica
from construirTabelaSimbolos import construirTabelaSimbolos


class _BaseComBackup(unittest.TestCase):
    _ARQUIVOS_TEXTO = [
        arquivo_tokens, arqv_json, arqv_txt, arqv_md,
        'saida_tabela_simbolos.json', 'saida_tabela_simbolos.md',
    ]

    def setUp(self):
        self._backups_texto = {}
        self._backup_png = None
        for arq in self._ARQUIVOS_TEXTO:
            if os.path.exists(arq):
                with open(arq, 'r', encoding='utf-8') as f:
                    self._backups_texto[arq] = f.read()
        if os.path.exists(arqv_png):
            with open(arqv_png, 'rb') as f:
                self._backup_png = f.read()

    def tearDown(self):
        for arq in self._ARQUIVOS_TEXTO:
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
        globalVars.string_pool_global.pool.clear()
        globalVars.string_pool_global.strings.clear()
        globalVars.contador_linha_global   = 1
        globalVars.total_linhas_global     = 0
        globalVars.em_comentario_global    = False
        globalVars.erro_lexico_global      = False
        globalVars.erros_sintaticos_global = []


class _Resultado:
    def __init__(self, tabela_dict, erros):
        self.tabela = tabela_dict
        self.erros  = erros


def analisar(linhas):
    # roda lexico + sintatico + tabela de simbolos. retorna wrapper
    conteudo = '\n'.join(linhas)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt',
                                     delete=False, encoding='utf-8') as f:
        f.write(conteudo)
        caminho = f.name
    try:
        resultado = prepararEntradaSemantica(caminho)
        tabela_dict, erros = construirTabelaSimbolos(resultado['arvore'])
        return _Resultado(tabela_dict, erros)
    finally:
        os.unlink(caminho)


def programa(expressoes):
    return ['(START)'] + expressoes + ['(END)']


class TestDeclaracaoVariaveis(_BaseComBackup):

    def test_declaracao_int(self):
        tabela = analisar(programa(['(5 X)']))
        self.assertIn('X', tabela.tabela)
        self.assertEqual(tabela.tabela['X'].tipo, 'int')
        self.assertIsNotNone(tabela.tabela['X'].linha_def)

    def test_declaracao_float(self):
        tabela = analisar(programa(['(3.14 Y)']))
        self.assertIn('Y', tabela.tabela)
        self.assertEqual(tabela.tabela['Y'].tipo, 'float')

    def test_atribuicao_bool_registra_tipo(self):
        # bool e registrado na tabela — erro de tipo e responsabilidade de verificarTipos
        tabela = analisar(programa(['((5 5 ==) FLAG)']))
        self.assertIn('FLAG', tabela.tabela)
        self.assertEqual(tabela.tabela['FLAG'].tipo, 'bool')
        self.assertEqual(tabela.erros, [])

    def test_multiplas_variaveis(self):
        tabela = analisar(programa(['(5 X)', '(3.14 Y)', '(10 Z)']))
        self.assertIn('X', tabela.tabela)
        self.assertIn('Y', tabela.tabela)
        self.assertIn('Z', tabela.tabela)

    def test_negativo_int(self):
        tabela = analisar(programa(['(-3 X)']))
        self.assertIn('X', tabela.tabela)
        self.assertEqual(tabela.tabela['X'].tipo, 'int')

    def test_negativo_float(self):
        tabela = analisar(programa(['(-1.5 X)']))
        self.assertIn('X', tabela.tabela)
        self.assertEqual(tabela.tabela['X'].tipo, 'float')


class TestLeituraVariaveis(_BaseComBackup):

    def test_leitura_registra_uso(self):
        tabela = analisar(programa(['(5 X)', '(X)']))
        self.assertEqual(len(tabela.tabela['X'].linhas_uso), 1)
        self.assertEqual(tabela.erros, [])

    def test_multiplas_leituras(self):
        tabela = analisar(programa(['(5 X)', '(X)', '(X)']))
        self.assertEqual(len(tabela.tabela['X'].linhas_uso), 2)

    def test_uso_antes_da_definicao(self):
        tabela = analisar(programa(['(Z)', '(5 Z)']))
        self.assertTrue(any('usada antes de ser definida' in e for e in tabela.erros))

    def test_variavel_nao_declarada(self):
        tabela = analisar(programa(['(W)']))
        self.assertTrue(any("'W'" in e for e in tabela.erros))

    def test_uso_apos_definicao_sem_erro(self):
        tabela = analisar(programa(['(10 X)', '(X)']))
        self.assertEqual(tabela.erros, [])


class TestReatribuicao(_BaseComBackup):

    def test_reatribuicao_mesmo_tipo_sem_erro(self):
        tabela = analisar(programa(['(5 X)', '(10 X)']))
        self.assertEqual(tabela.erros, [])

    def test_reatribuicao_registra_linha_uso(self):
        tabela = analisar(programa(['(5 X)', '(10 X)']))
        self.assertEqual(len(tabela.tabela['X'].linhas_uso), 1)

    def test_reatribuicao_tipo_incompativel_gera_erro(self):
        tabela = analisar(programa(['(5 X)', '(3.14 X)']))
        self.assertTrue(any('redefinir' in e for e in tabela.erros))

    def test_reatribuicao_tipo_incompativel_mantem_tipo_original(self):
        tabela = analisar(programa(['(5 X)', '(3.14 X)']))
        self.assertEqual(tabela.tabela['X'].tipo, 'int')


class TestRes(_BaseComBackup):

    def test_res_valido(self):
        tabela = analisar(programa(['(3 4 +)', '(1 RES)']))
        self.assertEqual(tabela.erros, [])

    def test_res_sem_resultado_anterior(self):
        tabela = analisar(programa(['(1 RES)']))
        self.assertTrue(any('RES(1)' in e for e in tabela.erros))

    def test_res_indice_maior_que_resultados(self):
        tabela = analisar(programa(['(3 4 +)', '(5 RES)']))
        self.assertTrue(any('RES(5)' in e for e in tabela.erros))

    def test_res_multiplos_resultados(self):
        tabela = analisar(programa(['(1 2 +)', '(3 4 +)', '(2 RES)']))
        self.assertEqual(tabela.erros, [])

    def test_res_linha_indicada_no_erro(self):
        tabela = analisar(programa(['(1 RES)']))
        self.assertTrue(any('linha' in e.lower() for e in tabela.erros))


class TestEstruturas(_BaseComBackup):

    def test_if_nao_gera_erro(self):
        tabela = analisar(programa(['((5 5 ==) (1 2 +) IF)']))
        self.assertEqual(tabela.erros, [])

    def test_for_nao_gera_erro(self):
        tabela = analisar(programa(['(3 (1 2 +) FOR)']))
        self.assertEqual(tabela.erros, [])

    def test_variavel_em_condicao_if(self):
        tabela = analisar(programa(['(5 X)', '((X) (1 2 +) IF)']))
        self.assertEqual(len(tabela.tabela['X'].linhas_uso), 1)
        self.assertEqual(tabela.erros, [])

    def test_variavel_nao_declarada_em_if(self):
        tabela = analisar(programa(['((W) (1 2 +) IF)']))
        self.assertTrue(any("'W'" in e for e in tabela.erros))


class TestSaidas(_BaseComBackup):

    def test_salva_json(self):
        analisar(programa(['(5 X)']))
        self.assertTrue(os.path.exists('saida_tabela_simbolos.json'))

    def test_json_contem_variavel(self):
        analisar(programa(['(5 X)']))
        with open('saida_tabela_simbolos.json', encoding='utf-8') as f:
            dados = json.load(f)
        self.assertIn('X', dados)
        self.assertEqual(dados['X']['tipo'], 'int')

    def test_salva_md(self):
        analisar(programa(['(5 X)']))
        self.assertTrue(os.path.exists('saida_tabela_simbolos.md'))

    def test_md_contem_variavel(self):
        analisar(programa(['(5 X)']))
        with open('saida_tabela_simbolos.md', encoding='utf-8') as f:
            conteudo = f.read()
        self.assertIn('X', conteudo)
        self.assertIn('int', conteudo)

    def test_arvore_none_retorna_erro(self):
        from construirTabelaSimbolos import construirTabelaSimbolos
        _, erros = construirTabelaSimbolos(None)
        self.assertTrue(len(erros) > 0)


if __name__ == '__main__':
    unittest.main()
