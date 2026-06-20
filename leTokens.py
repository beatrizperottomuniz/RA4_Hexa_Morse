'''
Integrantes do grupo (ordem alfabética):
Beatriz Perotto Muniz - @beatrizperottomuniz

Nome do grupo no Canvas: RA3 6
'''
import json
from globalVars import string_pool_global
from Token import Token, TokenType

def lerTokens(arquivo):
    try:
        with open(arquivo, 'r', encoding='utf-8') as file:
            dados = json.load(file)
    except FileNotFoundError:
        print(f"Arquivo não encontrado: {arquivo}")
        return []
    except Exception as e:
        print(f"Erro ao ler o arquivo: {e}")
        return []

    if "string_pool" not in dados or "tokens" not in dados:
        print(f"Formato inválido: campo 'string_pool' ou 'tokens' ausente.")
        return []

    campos_obrigatorios = ("tipo", "linha", "coluna", "simbolo_id")
    tipos_validos = set(vars(TokenType).values())

    for i, token in enumerate(dados["tokens"]):
        campos_faltando = [c for c in campos_obrigatorios if c not in token]
        if campos_faltando:
            print(f"Token {i} com campos faltando: {campos_faltando}")
            return []

        if token["tipo"] not in tipos_validos:
            print(f"Token {i} com tipo desconhecido: '{token['tipo']}'")
            return []

    # coloca dados na string pool
    for lexema in dados["string_pool"]:
        string_pool_global.buscarOuAdicionar(lexema)

    # faz a lista de tokens
    lista_tokens = []
    for t in dados["tokens"]:
        token = Token(t["tipo"], t["linha"], t["coluna"], t["simbolo_id"])
        lista_tokens.append(token)

    return lista_tokens
