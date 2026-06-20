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
from gerarArvoreAtribuida import gerarArvoreAtribuida,arqv_atrib_json, arqv_atrib_txt, arqv_atrib_md, arqv_atrib_png
from prepararEntradaSemantica import prepararEntradaSemantica
from construirTabelaSimbolos import construirTabelaSimbolos
from verificarTipos import verificarTipos


class _BaseComBackup(unittest.TestCase):
    arquivos_texto = [
        arquivo_tokens, arqv_json, arqv_txt, arqv_md,
        arqv_atrib_json, arqv_atrib_txt, arqv_atrib_md,
        'saida_tabela_simbolos.json', 'saida_tabela_simbolos.md',
        'saida_erros_semanticos.md',
    ]
    arquivos_bin = [arqv_png, arqv_atrib_png]

    def setUp(self):
        self._backups_texto = {}
        self._backups_bin   = {}
        for arq in self.arquivos_texto:
            if os.path.exists(arq):
                with open(arq, 'r', encoding='utf-8') as f:
                    self._backups_texto[arq] = f.read()
        for arq in self.arquivos_bin:
            if os.path.exists(arq):
                with open(arq, 'rb') as f:
                    self._backups_bin[arq] = f.read()

    def tearDown(self):
        for arq in self.arquivos_texto:
            if arq in self._backups_texto:
                with open(arq, 'w', encoding='utf-8') as f:
                    f.write(self._backups_texto[arq])
            elif os.path.exists(arq):
                os.remove(arq)
        for arq in self.arquivos_bin:
            if arq in self._backups_bin:
                with open(arq, 'wb') as f:
                    f.write(self._backups_bin[arq])
            elif os.path.exists(arq):
                os.remove(arq)
        globalVars.string_pool_global.pool.clear()
        globalVars.string_pool_global.strings.clear()
        globalVars.contador_linha_global   = 1
        globalVars.total_linhas_global     = 0
        globalVars.em_comentario_global    = False
        globalVars.erro_lexico_global      = False
        globalVars.erros_sintaticos_global = []


def _pipeline_ate_atribuida(linhas):
    #ret (arvore_atribuida, erros_semanticos)
    conteudo = '\n'.join(linhas)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt',
                                     delete=False, encoding='utf-8') as f:
        f.write(conteudo)
        caminho = f.name
    try:
        resultado = prepararEntradaSemantica(caminho)
        arvore    = resultado['arvore']
        tabela, erros_decl  = construirTabelaSimbolos(arvore)
        erros_tipos, tipos_nos = verificarTipos(arvore, tabela)
        erros = erros_decl + erros_tipos
        if erros or arvore is None:
            return None, erros
        atribuida = gerarArvoreAtribuida(arvore, tabela, tipos_nos)
        return atribuida, erros
    finally:
        os.unlink(caminho)


def _buscar_nos(raiz, tipo_no):
    # BFS para encontrar todos os nos de um tipo
    resultado, fila = [], [raiz]
    while fila:
        no = fila.pop(0)
        if no.tipo == tipo_no:
            resultado.append(no)
        fila.extend(no.filhos)
    return resultado


def programa(expressoes):
    return ['(START)'] + expressoes + ['(END)']


# estrutura basica da arv atribuida

class TestEstruturaAtribuida(_BaseComBackup):

    def test_programa_valido_retorna_arvore(self):
        atribuida, erros = _pipeline_ate_atribuida(programa(['(3 4 +)']))
        self.assertEqual(erros, [])
        self.assertIsNotNone(atribuida)

    def test_arvore_nula_retorna_none(self):
        resultado = gerarArvoreAtribuida(None, {}, {})
        self.assertIsNone(resultado)

    def test_nos_tem_tipo_inferido(self):
        atribuida, erros = _pipeline_ate_atribuida(programa(['(3 4 +)']))
        self.assertEqual(erros, [])
        # todo nó deve ter o atributo tipo_inferido após anotação
        self.assertTrue(hasattr(atribuida, 'tipo_inferido'))

    def test_nos_tem_categoria_semantica(self):
        atribuida, erros = _pipeline_ate_atribuida(programa(['(3 4 +)']))
        self.assertEqual(erros, [])
        self.assertTrue(hasattr(atribuida, 'categoria_semantica'))


# tipo inferido em nos de exp

class TestTipoInferidoNos(_BaseComBackup):

    def test_expressao_int_tem_tipo_int(self):
        atribuida, erros = _pipeline_ate_atribuida(programa(['(3 4 +)']))
        self.assertEqual(erros, [])
        nos_rpn = _buscar_nos(atribuida, 'rpn')
        tipos = [n.tipo_inferido for n in nos_rpn if n.tipo_inferido is not None]
        self.assertIn('int', tipos)

    def test_expressao_float_tem_tipo_float(self):
        atribuida, erros = _pipeline_ate_atribuida(programa(['(3.0 4.0 +)']))
        self.assertEqual(erros, [])
        nos_rpn = _buscar_nos(atribuida, 'rpn')
        tipos = [n.tipo_inferido for n in nos_rpn if n.tipo_inferido is not None]
        self.assertIn('float', tipos)

    def test_expressao_relacional_tem_tipo_bool(self):
        atribuida, erros = _pipeline_ate_atribuida(programa(['(3 4 ==)']))
        self.assertEqual(erros, [])
        nos_rpn = _buscar_nos(atribuida, 'rpn')
        tipos = [n.tipo_inferido for n in nos_rpn if n.tipo_inferido is not None]
        self.assertIn('bool', tipos)

    def test_divisao_real_tem_tipo_float(self):
        atribuida, erros = _pipeline_ate_atribuida(programa(['(4 2 |)']))
        self.assertEqual(erros, [])
        nos_rpn = _buscar_nos(atribuida, 'rpn')
        tipos = [n.tipo_inferido for n in nos_rpn if n.tipo_inferido is not None]
        self.assertIn('float', tipos)


# prog com erros nao gera arv atrib

class TestErrosNaoGeram(_BaseComBackup):

    def test_tipo_incompativel_nao_gera_arvore(self):
        # int + float = erro semântico
        atribuida, erros = _pipeline_ate_atribuida(programa(['(3 4.0 +)']))
        self.assertTrue(len(erros) > 0)
        self.assertIsNone(atribuida)

    def test_variavel_nao_declarada_nao_gera_arvore(self):
        atribuida, erros = _pipeline_ate_atribuida(programa(['((X) 2 +)']))
        self.assertTrue(len(erros) > 0)
        self.assertIsNone(atribuida)


if __name__ == '__main__':
    unittest.main()
