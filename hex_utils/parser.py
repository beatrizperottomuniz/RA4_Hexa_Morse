# Parser de linhas de assembly ARM (sintaxe GNU unified).
# Separa label, mnemonico, operandos e diretivas de cada linha do .s

import re


class LinhaParseada:
    def __init__(self, label=None, mnemonico=None, operandos=None,
                 diretiva=None, diretiva_args=None, vazia=False,
                 linha_original="", numero_linha=0):
        self.label = label
        self.mnemonico = mnemonico
        self.operandos = operandos or []
        self.diretiva = diretiva
        self.diretiva_args = diretiva_args or []
        self.vazia = vazia
        self.linha_original = linha_original
        self.numero_linha = numero_linha

    def __repr__(self):
        return (f"LinhaParseada(label={self.label!r}, mnemonico={self.mnemonico!r}, "
                f"operandos={self.operandos!r}, diretiva={self.diretiva!r}, "
                f"diretiva_args={self.diretiva_args!r}, vazia={self.vazia})")


def removerComentario(linha):
    # remove tudo apos '@' que nao esteja dentro de aspas simples
    dentro_aspas = False
    for i, ch in enumerate(linha):
        if ch == "'":
            dentro_aspas = not dentro_aspas
        elif ch == "@" and not dentro_aspas:
            return linha[:i]
    return linha


def splitOperandos(texto):
    # separa operandos por virgula, respeitando agrupadores [] {} ()
    texto = texto.strip()
    if not texto:
        return []
    operandos = []
    atual = []
    profundidade = 0
    for ch in texto:
        if ch in "[{(":
            profundidade += 1
            atual.append(ch)
        elif ch in "]})":
            profundidade -= 1
            atual.append(ch)
        elif ch == "," and profundidade == 0:
            operandos.append("".join(atual).strip())
            atual = []
        else:
            atual.append(ch)
    if atual:
        operandos.append("".join(atual).strip())
    return operandos


diretivas_conhecidas = {
    ".syntax", ".arch", ".fpu", ".data", ".text", ".global",
    ".space", ".word", ".end",
}


def parseLinha(linha, numero_linha=0):
    original = linha
    linha = removerComentario(linha).strip()

    if not linha:
        return LinhaParseada(vazia=True, linha_original=original, numero_linha=numero_linha)

    label = None
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$", linha)
    if m:
        label = m.group(1)
        resto = m.group(2).strip()
    else:
        resto = linha

    if not resto:
        return LinhaParseada(label=label, vazia=(label is None),
                              linha_original=original, numero_linha=numero_linha)

    if resto.startswith("."):
        partes = resto.split(None, 1)
        diretiva = partes[0]
        args_str = partes[1] if len(partes) > 1 else ""
        diretiva_args = splitOperandos(args_str)
        return LinhaParseada(label=label, diretiva=diretiva, diretiva_args=diretiva_args,
                              linha_original=original, numero_linha=numero_linha)

    partes = resto.split(None, 1)
    mnemonico = partes[0]
    operandos_str = partes[1] if len(partes) > 1 else ""
    operandos = splitOperandos(operandos_str)

    return LinhaParseada(label=label, mnemonico=mnemonico, operandos=operandos,
                          linha_original=original, numero_linha=numero_linha)


def lerArquivo(caminho):
    with open(caminho, encoding="utf-8") as f:
        linhas = f.readlines()
    return [parseLinha(l, i + 1) for i, l in enumerate(linhas)]
