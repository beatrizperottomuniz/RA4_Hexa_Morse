'''
Integrantes do grupo (ordem alfabética):
Beatriz Perotto Muniz - @beatrizperottomuniz

Nome do grupo no Canvas: RA3 6
'''

# TO-DO : erro lexico de comentario nao fechado   if globalVars.em_comentario_global: print("Erro léxico: comentário *{ não fechado") erro = True 
import sys
import os
import json
from Token import Token, TokenType
import globalVars
# lexico
from leituraArquivo import lerArquivo
from analisadorLexico import parseExpressao
# sintatico
from leTokens import lerTokens
from construirGramatica import construirGramatica
from parsear import parsear
from gerarArvore import gerarArvore
from gerarAssembly import gerarAssembly
from executaExpressao import executarExpressao
from exibeResultados import exibirResultados

arquivo_tokens = "saida_tokens_2.txt"


# funcs lexico


def exportarTokens(lista_tokens, caminho=arquivo_tokens):
    tokens_serializados = []
    for token in lista_tokens:
        tokens_serializados.append({
            "tipo": token.tipo,
            "linha": token.linha,
            "coluna": token.coluna,
            "simbolo_id": token.simbolo_id
        })
    dados = {
        "string_pool": globalVars.string_pool_global.strings,
        "tokens": tokens_serializados
    }
    try:
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)
        print(f"Tokens exportados para '{caminho}'")
    except Exception as e:
        print(f"Erro ao salvar tokens: {e}")


def rodarLexico(caminho_fonte):
    linhas = []
    lerArquivo(caminho_fonte, linhas)
    globalVars.total_linhas_global = len(linhas)

    tokens_lista = []
    erro = False

    for linha in linhas:
        tokens_linha = []
        parseExpressao(linha, tokens_linha)
        tokens_lista.extend(tokens_linha)

        if any(t.tipo == TokenType.UNKNOWN for t in tokens_linha):
            print(f"Erro léxico na linha {globalVars.contador_linha_global}: token desconhecido")
            erro = True

        globalVars.contador_linha_global += 1

    exportarTokens(tokens_lista)

    return not erro


# divide tokens por instrucao

def extrairInstrucoes(tokens):
#   divide a lista plana de tokens em grupos por instrução, ignorando (START), (END) e EOF
    instrucoes = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t.tipo == TokenType.EOF:
            break
        if t.tipo == TokenType.LPAREN:
            proximo = tokens[i + 1].tipo if i + 1 < len(tokens) else None
            if proximo in (TokenType.KEYWORD_START, TokenType.KEYWORD_END):
                while i < len(tokens) and tokens[i].tipo != TokenType.RPAREN:
                    i += 1
                i += 1
                continue
            grupo = []
            depth = 0
            while i < len(tokens):
                grupo.append(tokens[i])
                if tokens[i].tipo == TokenType.LPAREN:
                    depth += 1
                elif tokens[i].tipo == TokenType.RPAREN:
                    depth -= 1
                    if depth == 0:
                        i += 1
                        break
                i += 1
            instrucoes.append(grupo)
        else:
            i += 1
    return instrucoes


# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 AnalisadorSintatico.py <arquivo>.txt")
        sys.exit(1)

    caminho = sys.argv[1]

    erro_lexico = not rodarLexico(caminho)
    if erro_lexico:
        print("\nAVISO: erros léxicos encontrados — continuando análise sintática.")

    tokens = lerTokens(arquivo_tokens)

    resultado_gramatica = construirGramatica()
    tabela = resultado_gramatica['tabela']

    resultado_parser = parsear(tokens, tabela)

    if erro_lexico or resultado_parser['erros']:
        if resultado_parser['erros']:
            print("\n------ Erros sintáticos ------")
            for erro in resultado_parser['erros']:
                print(f"  {erro}")
            print("------------------------------")
        print("\nERROS encontrados — assembly não gerado.")
        sys.exit(1)

    print("Análise sintática: OK")

    arvore = gerarArvore(resultado_parser['estrutura_derivacao'])
    print("Árvore gerada: saida_arvore_json.txt / saida_arvore.txt / saida_arvore.png / saida_arvore.md")

    gerarAssembly(arvore)
    print("Assembly gerado: saida2.s")

    instrucoes = extrairInstrucoes(tokens)
    resultados = []
    memoria    = {}
    for instrucao in instrucoes:
        executarExpressao(instrucao, resultados, memoria)

    exibirResultados(resultados)
