'''
Integrantes do grupo (ordem alfabética):
Beatriz Perotto Muniz - @beatrizperottomuniz

Nome do grupo no Canvas: RA3 6
'''
import unittest
import os
import tempfile
import globalVars
from AnalisadorSintatico import arquivo_tokens
from gerarArvore import arqv_json, arqv_txt, arqv_png, arqv_md
from prepararEntradaSemantica import prepararEntradaSemantica
from construirTabelaSimbolos import construirTabelaSimbolos
from verificarTipos import verificarTipos


class _BaseComBackup(unittest.TestCase):
    arquivos_texto = [
        arquivo_tokens, arqv_json, arqv_txt, arqv_md,
        'saida_erros_semanticos.md',
        'saida_tabela_simbolos.json',
        'saida_tabela_simbolos.md',
    ]

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
        globalVars.string_pool_global.pool.clear()
        globalVars.string_pool_global.strings.clear()
        globalVars.contador_linha_global   = 1
        globalVars.total_linhas_global     = 0
        globalVars.em_comentario_global    = False
        globalVars.erro_lexico_global      = False
        globalVars.erros_sintaticos_global = []


def analisar(linhas):
    # roda lexico + sintatico + tabela de simbolos + verificacao de tipos retorna lista de erros semanticos
    conteudo = '\n'.join(linhas)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt',
                                     delete=False, encoding='utf-8') as f:
        f.write(conteudo)
        caminho = f.name
    try:
        resultado = prepararEntradaSemantica(caminho)
        tabela, _ = construirTabelaSimbolos(resultado['arvore'])
        erros, _ = verificarTipos(resultado['arvore'], tabela)
        return erros
    finally:
        os.unlink(caminho)


def programa(expressoes):
    return ['(START)'] + expressoes + ['(END)']


def tem_erro(erros, trecho):
    return any(trecho in e for e in erros)


class TestOperacoesAritmeticas(_BaseComBackup):

    def test_soma_int_int_valida(self):
        erros = analisar(programa(['(3 4 +)']))
        self.assertEqual(erros, [])

    def test_soma_float_float_valida(self):
        erros = analisar(programa(['(3.0 4.0 +)']))
        self.assertEqual(erros, [])

    def test_soma_int_float_invalida(self):
        erros = analisar(programa(['(3 4.0 +)']))
        self.assertTrue(tem_erro(erros, "'+'"))

    def test_subtracao_float_float_valida(self):
        erros = analisar(programa(['(3.0 2.0 -)']))
        self.assertEqual(erros, [])

    def test_subtracao_int_float_invalida(self):
        erros = analisar(programa(['(3 2.0 -)']))
        self.assertTrue(tem_erro(erros, "'-'"))

    def test_multiplicacao_int_int_valida(self):
        erros = analisar(programa(['(3 2 *)']))
        self.assertEqual(erros, [])

    def test_multiplicacao_float_float_valida(self):
        erros = analisar(programa(['(3.0 2.0 *)']))
        self.assertEqual(erros, [])

    def test_multiplicacao_int_float_invalida(self):
        erros = analisar(programa(['(3 2.0 *)']))
        self.assertTrue(tem_erro(erros, "'*'"))


class TestDivisaoReal(_BaseComBackup):

    def test_int_div_real_int_valida(self):
        erros = analisar(programa(['(10 2 |)']))
        self.assertEqual(erros, [])

    def test_float_div_real_float_valida(self):
        erros = analisar(programa(['(10.0 2.0 |)']))
        self.assertEqual(erros, [])

    def test_div_real_tipos_diferentes_invalida(self):
        erros = analisar(programa(['(10 2.0 |)']))
        self.assertTrue(tem_erro(erros, "'|'"))


class TestDivisaoInteiraModulo(_BaseComBackup):

    def test_divisao_inteira_int_int_valida(self):
        erros = analisar(programa(['(10 2 /)']))
        self.assertEqual(erros, [])

    def test_divisao_inteira_float_int_invalida(self):
        erros = analisar(programa(['(10.0 2 /)']))
        self.assertTrue(tem_erro(erros, "'/'"))

    def test_divisao_inteira_int_float_invalida(self):
        erros = analisar(programa(['(10 2.0 /)']))
        self.assertTrue(tem_erro(erros, "'/'"))

    def test_modulo_int_int_valido(self):
        erros = analisar(programa(['(10 3 %)']))
        self.assertEqual(erros, [])

    def test_modulo_float_int_invalido(self):
        erros = analisar(programa(['(10.0 2 %)']))
        self.assertTrue(tem_erro(erros, "'%'"))

    def test_modulo_int_float_invalido(self):
        erros = analisar(programa(['(10 2.0 %)']))
        self.assertTrue(tem_erro(erros, "'%'"))


class TestPotenciacao(_BaseComBackup):

    def test_int_pow_int_valido(self):
        erros = analisar(programa(['(2 3 ^)']))
        self.assertEqual(erros, [])

    def test_float_pow_int_valido(self):
        erros = analisar(programa(['(2.0 3 ^)']))
        self.assertEqual(erros, [])

    def test_expoente_float_invalido(self):
        erros = analisar(programa(['(2 3.0 ^)']))
        self.assertTrue(tem_erro(erros, "expoente"))

    def test_expoente_zero_invalido(self):
        erros = analisar(programa(['(2 0 ^)']))
        self.assertTrue(tem_erro(erros, "positivo"))

    def test_expoente_negativo_invalido(self):
        erros = analisar(programa(['(2 -1 ^)']))
        self.assertTrue(tem_erro(erros, "positivo"))


class TestOperacoesRelacionais(_BaseComBackup):

    def test_int_eq_int_valido(self):
        erros = analisar(programa(['(5 5 ==)']))
        self.assertEqual(erros, [])

    def test_float_gt_float_valido(self):
        erros = analisar(programa(['(3.0 2.0 >)']))
        self.assertEqual(erros, [])

    def test_int_lt_float_invalido(self):
        erros = analisar(programa(['(5 5.0 <)']))
        self.assertTrue(tem_erro(erros, "'<'"))

    def test_int_neq_float_invalido(self):
        erros = analisar(programa(['(5 5.0 !=)']))
        self.assertTrue(tem_erro(erros, "'!='"))

    def test_int_lte_int_valido(self):
        erros = analisar(programa(['(3 5 <=)']))
        self.assertEqual(erros, [])

    def test_float_gte_float_valido(self):
        erros = analisar(programa(['(3.0 5.0 >=)']))
        self.assertEqual(erros, [])


class TestEstruturaIF(_BaseComBackup):

    def test_if_condicao_bool_valida(self):
        erros = analisar(programa(['((5 5 ==) (1 2 +) IF)']))
        self.assertEqual(erros, [])

    def test_if_condicao_int_invalida(self):
        erros = analisar(programa(['((3 4 +) (1 2 +) IF)']))
        self.assertTrue(tem_erro(erros, "IF"))

    def test_if_condicao_float_invalida(self):
        erros = analisar(programa(['((3.0 4.0 +) (1 2 +) IF)']))
        self.assertTrue(tem_erro(erros, "IF"))


class TestEstruturaFOR(_BaseComBackup):

    def test_for_contador_int_positivo_valido(self):
        erros = analisar(programa(['(3 (1 2 +) FOR)']))
        self.assertEqual(erros, [])

    def test_for_contador_float_invalido(self):
        erros = analisar(programa(['(3.0 (1 2 +) FOR)']))
        self.assertTrue(tem_erro(erros, "FOR"))

    def test_for_contador_zero_invalido(self):
        erros = analisar(programa(['(0 (1 2 +) FOR)']))
        self.assertTrue(tem_erro(erros, "positivo"))

    def test_for_contador_negativo_invalido(self):
        erros = analisar(programa(['(-1 (1 2 +) FOR)']))
        self.assertTrue(tem_erro(erros, "positivo"))


class TestRES(_BaseComBackup):

    def test_res_tipo_int_em_operacao_valida(self):
        erros = analisar(programa(['(3 4 +)', '((1 RES) 2 +)']))
        self.assertEqual(erros, [])

    def test_res_tipo_float_em_operacao_valida(self):
        erros = analisar(programa(['(3.0 4.0 +)', '((1 RES) 2.0 *)']))
        self.assertEqual(erros, [])

    def test_res_tipo_int_operando_float_invalido(self):
        erros = analisar(programa(['(3 4 +)', '((1 RES) 2.0 +)']))
        self.assertTrue(tem_erro(erros, "'+'"))

    def test_res_tipo_float_operando_int_invalido(self):
        erros = analisar(programa(['(3.0 4.0 +)', '((1 RES) 2 +)']))
        self.assertTrue(tem_erro(erros, "'+'"))

    def test_res_zero_rejeitado_por_tipos(self):
        # n=0 referencia o resultado corrente ainda nao disponivel — erro semantico
        erros = analisar(programa(['(3 4 +)', '(0 RES)']))
        self.assertTrue(any('RES(0)' in e for e in erros))


class TestAtribuicaoInvalida(_BaseComBackup):

    def test_atribuicao_bool_em_variavel_invalida(self):
        erros = analisar(programa(['((5 5 ==) FLAG)']))
        self.assertTrue(tem_erro(erros, 'relacional'))

    def test_atribuicao_if_em_variavel_invalida(self):
        erros = analisar(programa(['((5 5 ==) (1 2 +) IF)', '((1 RES) X)']))
        self.assertTrue(tem_erro(erros, 'controle'))


class TestLeituraVariavel(_BaseComBackup):

    def test_leitura_variavel_declarada(self):
        erros = analisar(programa(['(5 X)', '(X)']))
        self.assertEqual(erros, [])

    def test_leitura_variavel_float_declarada(self):
        erros = analisar(programa(['(3.14 Y)', '(Y)']))
        self.assertEqual(erros, [])


class TestAninhamento(_BaseComBackup):

    def test_aninhado_int_int_valido(self):
        erros = analisar(programa(['((1 2 +) (3 4 +) +)']))
        self.assertEqual(erros, [])

    def test_aninhado_float_float_valido(self):
        erros = analisar(programa(['((1.0 2.0 +) (3.0 4.0 +) *)']))
        self.assertEqual(erros, [])

    def test_aninhado_tipos_diferentes_invalido(self):
        erros = analisar(programa(['((1 2 +) (3.0 4.0 +) +)']))
        self.assertTrue(tem_erro(erros, "'+'"))

    def test_aninhado_profundo_valido(self):
        erros = analisar(programa(['(((1 2 +) (3 4 +) +) (5 6 +) *)']))
        self.assertEqual(erros, [])

    def test_if_aninhado_valido(self):
        erros = analisar(programa(['((5 3 >) ((1 2 +) (3 4 *) +) IF)']))
        self.assertEqual(erros, [])


if __name__ == '__main__':
    unittest.main()
