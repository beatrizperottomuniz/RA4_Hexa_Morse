'''
Integrantes do grupo (ordem alfabética):
Beatriz Perotto Muniz - @beatrizperottomuniz

Nome do grupo no Canvas: RA3 6
'''
# para ver se a string (variavel) ja esta na pool
class StringPool:
    def __init__(self):
        self.pool = {} # dicionario string = id
        self.strings = [] # lista de strings

    # retorna id se existe/ cria novo se não
    def buscarOuAdicionar(self, lexema: str):
        if lexema in self.pool:
            return self.pool[lexema]

        proximo_id = len(self.strings) # id é o índice na lista
        self.pool[lexema] = proximo_id
        self.strings.append(lexema)

        return proximo_id

    # retorna texto original de id
    def obterString(self, simbolo_id: int):
        if 0 <= simbolo_id < len(self.strings):
            return self.strings[simbolo_id]
        return "desconhecido"