'''
Integrantes do grupo (ordem alfabética):
Beatriz Perotto Muniz - @beatrizperottomuniz

Nome do grupo no Canvas: RA3 6
'''
import json
import globalVars
from leTokens import lerTokens
from construirGramatica import construirGramatica
from parsear import parsear
from gerarArvore import gerarArvore, NoArvore, arqv_json
from Token import Token
from AnalisadorSintatico import rodarLexico, arquivo_tokens

def lerArvore(arquivo=arqv_json):
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            dados = json.load(f)
    except FileNotFoundError:
        print(f"Arquivo de árvore não encontrado: {arquivo}")
        return None
    except Exception as e:
        print(f"Erro ao ler árvore: {e}")
        return None

    if "arvore" not in dados:
        print("Formato inválido: campo 'arvore' ausente.")
        return None

    for lexema in dados.get("string_pool", []):
        globalVars.string_pool_global.buscarOuAdicionar(lexema)

    def dictParaNo(d):
        no = NoArvore(d['tipo'])
        if d['token']:
            t = d['token']
            no.token = Token(t['tipo'], t['linha'], t['coluna'], t['simbolo_id'])
        for filho in d['filhos']:
            no.adicionar_filho(dictParaNo(filho))
        return no

    return dictParaNo(dados['arvore'])


def prepararEntradaSemantica(arquivo):
    print(f"\n----- Analisando arquivo: {arquivo} -----")

    # lexico
    erro_lexico = not rodarLexico(arquivo)
    globalVars.erro_lexico_global = erro_lexico

    # erro de comentario nao fechado
    if globalVars.em_comentario_global:
        print("Erro léxico: comentário '*{' não fechado")
        erro_lexico = True
        globalVars.em_comentario_global = False

    if erro_lexico:
        print("Resultado da análise léxica: ERRO — continuando análise sintática.")
    else:
        print("Resultado da análise léxica: OK")

    # ler tokens
    tokens = lerTokens(arquivo_tokens)

    # gramatica e tabela ll(1)
    resultado_gramatica = construirGramatica()
    tabela = resultado_gramatica['tabela']

    # parsing
    resultado_parser = parsear(tokens, tabela)

    erros_sintaticos = resultado_parser['erros']
    globalVars.erros_sintaticos_global = erros_sintaticos
    if erros_sintaticos:
        print("\n------ Erros sintáticos ------")
        for erro in erros_sintaticos:
            print(f"  {erro}")
        print("------------------------------")
        print("Resultado da análise sintática: ERRO")
    else:
        print("Resultado da análise sintática: OK")

    # arvore sintatica -> gerada se o sintatico passar, independente de erro lexico
    arvore = None
    estrutura = resultado_parser['estrutura_derivacao']
    if estrutura:
        gerarArvore(estrutura)
        arvore = lerArvore()
        print("Árvore gerada: saida_arvore_json.txt / saida_arvore.txt / saida_arvore.png / saida_arvore.md")
        if erros_sintaticos:
            print("Árvore sintática parcial gerada (erros sintáticos presentes).")
        else:
            print("Árvore sintática gerada.")

    return {
        'tokens': tokens,
        'arvore': arvore
    }
