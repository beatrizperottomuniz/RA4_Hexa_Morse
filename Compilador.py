'''
Integrantes do grupo (ordem alfabética):
Beatriz Perotto Muniz - @beatrizperottomuniz

Nome do grupo no Canvas: RA3 6
'''
import sys
import globalVars
from prepararEntradaSemantica import prepararEntradaSemantica
from construirTabelaSimbolos import construirTabelaSimbolos
from verificarTipos import verificarTipos
from gerarArvoreAtribuida import gerarArvoreAtribuida
from gerarAssembly import gerarAssembly
from gerarHex import traduzir
from executaExpressao import executarExpressao
from exibeResultados import exibirResultados
from AnalisadorSintatico import extrairInstrucoes


arquivo_erros = 'saida_erros_semanticos.md'


def _salvarErrosMD(erros):
    linhas = ["# Relatório de Erros Semânticos\n"]
    if erros:
        for e in erros:
            linhas.append(f"- {e}")
    else:
        linhas.append("Nenhum erro semântico encontrado.")
    with open(arquivo_erros, 'w', encoding='utf-8') as f:
        f.write('\n'.join(linhas))


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 Compilador.py <arquivo.txt>")
        sys.exit(1)

    arquivo = sys.argv[1]

    # lexico e sintatico
    resultado = prepararEntradaSemantica(arquivo)
    arvore = resultado['arvore']
    tokens = resultado['tokens']

    # tabela de simbolos
    print("\n------ Análise semântica ------")

    tabela, erros_decl = construirTabelaSimbolos(arvore)

    # ver tipos
    erros_tipos, tipos_nos = verificarTipos(arvore, tabela)

    erros_semanticos = erros_decl + erros_tipos
    _salvarErrosMD(erros_semanticos)

    if erros_semanticos:
        print("Resultado da análise semântica: ERRO")
        for erro in erros_semanticos:
            print(f"  {erro}")
    else:
        print("Resultado da análise semântica: OK")

    print("------------------------------")

    # arvore atribuida + assembly + hex (se sem erros em todas as fases)
    ha_erros = (globalVars.erro_lexico_global
                or bool(globalVars.erros_sintaticos_global)
                or bool(erros_semanticos))

    if ha_erros:
        print("Árvore atribuída não gerada: há erros léxicos, sintáticos ou semânticos.")
        print("Assembly não gerado: há erros léxicos, sintáticos ou semânticos.")
        print("Hex não gerado: há erros léxicos, sintáticos ou semânticos.")
    else:
        arvore_atribuida = gerarArvoreAtribuida(arvore, tabela, tipos_nos)
        if arvore_atribuida is not None:
            print("Árvore atribuída: saida_arvore_atribuida.json / .txt / .md / .png")

        arquivo_asm = gerarAssembly(arvore_atribuida)
        if arquivo_asm:
            print(f"Assembly: {arquivo_asm}")
            try:
                traduzir(arquivo_asm, "saida_final.hex")
                print("Hex: saida_final.hex")
            except RuntimeError as e:
                print(f"Hex não gerado: {e}")

            instrucoes = extrairInstrucoes(tokens)
            resultados = []
            memoria    = {}
            for instrucao in instrucoes:
                executarExpressao(instrucao, resultados, memoria)
            exibirResultados(resultados)

if __name__ == '__main__':
    main()
