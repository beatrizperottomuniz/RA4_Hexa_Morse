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
from gerarAssembly import gerarAssembly
from prepararEntradaSemantica import prepararEntradaSemantica
from construirTabelaSimbolos import construirTabelaSimbolos
from verificarTipos import verificarTipos

_ARQUIVO_ASM = 'saida_assembly.s'


class _BaseComBackup(unittest.TestCase):
    arquivos_texto = [
        arquivo_tokens, arqv_json, arqv_txt, arqv_md,
        arqv_atrib_json, arqv_atrib_txt, arqv_atrib_md,
        'saida_tabela_simbolos.json', 'saida_tabela_simbolos.md',
        'saida_erros_semanticos.md', _ARQUIVO_ASM,
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


def _rodar(linhas):
    # Retorna dict com chaves: erros_semanticos, arquivo_asm, arvore_atribuida.
    conteudo = '\n'.join(linhas)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt',
                                     delete=False, encoding='utf-8') as f:
        f.write(conteudo)
        caminho = f.name
    try:
        resultado  = prepararEntradaSemantica(caminho)
        arvore     = resultado['arvore']
        tabela, erros_decl     = construirTabelaSimbolos(arvore)
        erros_tipos, tipos_nos = verificarTipos(arvore, tabela)
        erros = erros_decl + erros_tipos

        ha_erros = (globalVars.erro_lexico_global
                    or bool(globalVars.erros_sintaticos_global)
                    or bool(erros))

        if ha_erros or arvore is None:
            return {'erros_semanticos': erros, 'arquivo_asm': None, 'arvore_atribuida': None}

        atribuida   = gerarArvoreAtribuida(arvore, tabela, tipos_nos)
        arquivo_asm = gerarAssembly(atribuida)
        return {'erros_semanticos': erros, 'arquivo_asm': arquivo_asm, 'arvore_atribuida': atribuida}
    finally:
        os.unlink(caminho)


def programa(expressoes):
    return ['(START)'] + expressoes + ['(END)']


# - prog valido pipeline completo 

class TestPipelineValido(_BaseComBackup):

    def test_programa_simples_sem_erros(self):
        r = _rodar(programa(['(3 4 +)']))
        self.assertEqual(r['erros_semanticos'], [])
        self.assertIsNotNone(r['arvore_atribuida'])
        self.assertIsNotNone(r['arquivo_asm'])

    def test_programa_com_todos_os_tipos(self):
        # int, float, bool, MEM, RES
        r = _rodar(programa([
            '(10 X)',
            '(3.14 Y)',
            '((X) 2 +)',
            '((Y) 1.0 *)',
            '((1 RES) (1 RES) +)',
            '((X) 5 ==)',
        ]))
        self.assertEqual(r['erros_semanticos'], [])
        self.assertIsNotNone(r['arquivo_asm'])

    def test_programa_com_comentarios(self):
        r = _rodar(programa([
            '*{ comentario de linha inteira }*',
            '(3 4 +) *{ comentario no fim da linha }*',
            '*{ entre expressoes }*',
            '(5 2 -)',
        ]))
        self.assertEqual(r['erros_semanticos'], [])
        self.assertIsNotNone(r['arquivo_asm'])

    def test_programa_com_if(self):
        r = _rodar(programa([
            '((3 3 ==) (1 2 +) IF)',
        ]))
        self.assertEqual(r['erros_semanticos'], [])
        self.assertIsNotNone(r['arquivo_asm'])

    def test_programa_com_for(self):
        r = _rodar(programa([
            '(3 (1 2 +) FOR)',
        ]))
        self.assertEqual(r['erros_semanticos'], [])
        self.assertIsNotNone(r['arquivo_asm'])


# ─ prog com erros pipeline para antes do assembly

class TestPipelineComErros(_BaseComBackup):

    def test_erro_semantico_impede_assembly(self):
        # int + float = erro
        r = _rodar(programa(['(3 4.0 +)']))
        self.assertTrue(len(r['erros_semanticos']) > 0)
        self.assertIsNone(r['arquivo_asm'])
        self.assertIsNone(r['arvore_atribuida'])

    def test_variavel_nao_declarada_impede_assembly(self):
        r = _rodar(programa(['((Z) 2 +)']))
        self.assertTrue(len(r['erros_semanticos']) > 0)
        self.assertIsNone(r['arquivo_asm'])

    def test_mod_com_float_impede_assembly(self):
        r = _rodar(programa(['(3.0 2.0 %)']))
        self.assertTrue(len(r['erros_semanticos']) > 0)
        self.assertIsNone(r['arquivo_asm'])

    def test_if_sem_condicao_bool_impede_assembly(self):
        # condição int (stmt que retorna int), não bool
        r = _rodar(programa(['((3 5 +) (1 2 +) IF)']))
        self.assertTrue(len(r['erros_semanticos']) > 0)
        self.assertIsNone(r['arquivo_asm'])


if __name__ == '__main__':
    unittest.main()
