'''
Integrantes do grupo (ordem alfabética):
Beatriz Perotto Muniz - @beatrizperottomuniz

Nome do grupo no Canvas: RA3 6
'''
class TokenType:
    # keyword
    KEYWORD_RES = "KEYWORD_RES"
    KEYWORD_START = "KEYWORD_START"
    KEYWORD_END = "KEYWORD_END"
    KEYWORD_IF = "KEYWORD_IF"
    KEYWORD_FOR = "KEYWORD_FOR"
    KEYWORD_MORSE = "KEYWORD_MORSE"
    # id (variaveis) e tipos literais
    ID = "ID"
    NUM_INT = "NUM_INT"
    NUM_FLOAT = "NUM_FLOAT"
    STRING = "STRING"
    # operadores
    PLUS = "PLUS"
    MINUS = "MINUS"
    MULT = "MULT"
    DIV = "DIV"
    INT_DIV = "INT_DIV"
    MOD = "MOD"
    POW = "POW"
    #operadores para comparacao
    GT  = "GT"  # >
    LT  = "LT"  # <
    GTE = "GTE"  # >=
    LTE = "LTE"  # <=
    EQ  = "EQ"  # ==
    NEQ = "NEQ"  # !=
    # divisor de operacoes
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    # outros
    EOF = "EOF"
    UNKNOWN = "UNKNOWN"
    COMMENT = "COMMENT"

# classe do token com tipo,linha, coluna, id do simbolo na string pool
class Token:
    def __init__(self, token_tipo: str, linha: int, coluna: int, simbolo_id : int):
        self.tipo = token_tipo
        self.linha = linha
        self.coluna = coluna
        self.simbolo_id = simbolo_id

    def __repr__(self):
        return f"Token({self.tipo}, {self.simbolo_id}, {self.linha}, {self.coluna})"

