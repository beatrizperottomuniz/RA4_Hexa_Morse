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


def _pipeline_completo(linhas):
    # retorna (arquivo_asm, erros_semanticos)
    conteudo = '\n'.join(linhas)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt',
                                     delete=False, encoding='utf-8') as f:
        f.write(conteudo)
        caminho = f.name
    try:
        resultado = prepararEntradaSemantica(caminho)
        arvore    = resultado['arvore']
        tabela, erros_decl     = construirTabelaSimbolos(arvore)
        erros_tipos, tipos_nos = verificarTipos(arvore, tabela)
        erros = erros_decl + erros_tipos
        if erros or arvore is None:
            return None, erros
        atribuida   = gerarArvoreAtribuida(arvore, tabela, tipos_nos)
        arquivo_asm = gerarAssembly(atribuida)
        return arquivo_asm, erros
    finally:
        os.unlink(caminho)


def programa(expressoes):
    return ['(START)'] + expressoes + ['(END)']


class TestAssemblyValido(_BaseComBackup):

    def test_expressao_simples_gera_assembly(self):
        arquivo_asm, erros = _pipeline_completo(programa(['(3 4 +)']))
        self.assertEqual(erros, [])
        self.assertIsNotNone(arquivo_asm)

    def test_arquivo_assembly_existe_e_nao_vazio(self):
        arquivo_asm, erros = _pipeline_completo(programa(['(3 4 +)']))
        self.assertEqual(erros, [])
        self.assertTrue(os.path.exists(arquivo_asm))
        self.assertGreater(os.path.getsize(arquivo_asm), 0)

    def test_assembly_com_variavel(self):
        arquivo_asm, erros = _pipeline_completo(programa([
            '(10 X)',
            '((X) 2 +)',
        ]))
        self.assertEqual(erros, [])
        self.assertIsNotNone(arquivo_asm)

    def test_assembly_com_if(self):
        arquivo_asm, erros = _pipeline_completo(programa([
            '((3 3 ==) (1 2 +) IF)',
        ]))
        self.assertEqual(erros, [])
        self.assertIsNotNone(arquivo_asm)

    def test_assembly_com_for(self):
        arquivo_asm, erros = _pipeline_completo(programa([
            '(3 (1 2 +) FOR)',
        ]))
        self.assertEqual(erros, [])
        self.assertIsNotNone(arquivo_asm)

class TestAssemblyNaoGerado(_BaseComBackup):

    def test_arvore_nula_retorna_none(self):
        resultado = gerarAssembly(None)
        self.assertIsNone(resultado)

    def test_erro_semantico_nao_gera_assembly(self):
        # int + float = erro semântico
        arquivo_asm, erros = _pipeline_completo(programa(['(3 4.0 +)']))
        self.assertTrue(len(erros) > 0)
        self.assertIsNone(arquivo_asm)

    def test_variavel_nao_declarada_nao_gera_assembly(self):
        arquivo_asm, erros = _pipeline_completo(programa(['((X) 2 +)']))
        self.assertTrue(len(erros) > 0)
        self.assertIsNone(arquivo_asm)


if __name__ == '__main__':
    unittest.main()
