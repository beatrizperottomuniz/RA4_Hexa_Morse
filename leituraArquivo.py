'''
Integrantes do grupo (ordem alfabética):
Beatriz Perotto Muniz - @beatrizperottomuniz

Nome do grupo no Canvas: RA3 6
'''
import sys

def lerArquivo(nomeArquivo: str, linhas: list) -> None:
    try:
        with open(nomeArquivo, encoding='utf-8') as arquivo:
            for linha in arquivo:
                linhas.append(linha.rstrip('\n'))
    except FileNotFoundError:
        print(f"Arquivo não encontrado: {nomeArquivo}")
        sys.exit(1)
    except Exception as e:
        print(f"Erro ao ler o arquivo: {e}")
        sys.exit(1)
