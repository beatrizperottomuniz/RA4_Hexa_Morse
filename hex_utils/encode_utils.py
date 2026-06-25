# Utilitarios compartilhados para encoding ARMv7 A32.

# registradores ARM: r0-r12, sp=13, lr=14, pc=15
reg_map = {f"r{i}": i for i in range(13)}
reg_map.update({"sp": 13, "SP": 13, "lr": 14, "LR": 14, "pc": 15, "PC": 15})
reg_map.update({f"R{i}": i for i in range(13)})


def regNum(nome):
    nome = nome.strip()
    if nome not in reg_map:
        raise ValueError(f"Registrador desconhecido: {nome!r}")
    return reg_map[nome]


# condicoes ARM (4 bits, bits 31-28 de toda instrucao A32)
cond_map = {
    "EQ": 0b0000, "NE": 0b0001, "CS": 0b0010, "HS": 0b0010,
    "CC": 0b0011, "LO": 0b0011, "MI": 0b0100, "PL": 0b0101,
    "VS": 0b0110, "VC": 0b0111, "HI": 0b1000, "LS": 0b1001,
    "GE": 0b1010, "LT": 0b1011, "GT": 0b1100, "LE": 0b1101,
    "AL": 0b1110,
}


def condCode(sufixo):
    if sufixo == "":
        return cond_map["AL"]
    sufixo = sufixo.upper()
    if sufixo not in cond_map:
        raise ValueError(f"Condicao desconhecida: {sufixo!r}")
    return cond_map[sufixo]


# sufixos ordenados do mais longo para o mais curto (para split de mnem+cond)
cond_suffixes = sorted(cond_map.keys(), key=len, reverse=True)


def splitMnemonicCond(mnem, bases_validas):
    mnem_up = mnem.upper()
    if mnem_up in bases_validas:
        return mnem_up, ""
    for suf in cond_suffixes:
        if suf == "AL":
            continue
        if mnem_up.endswith(suf):
            base = mnem_up[: -len(suf)]
            if base in bases_validas:
                return base, suf
    return mnem_up, ""


def encodeDpImmediate(valor):
    # tenta codificar valor como imm12 (rotate4 + imm8) para data-processing
    valor &= 0xFFFFFFFF
    if valor <= 0xFF:
        return valor
    for rot in range(1, 16):
        shift = rot * 2
        rotated = ((valor << shift) | (valor >> (32 - shift))) & 0xFFFFFFFF
        if rotated <= 0xFF:
            return (rot << 8) | rotated
    raise ValueError(f"Valor 0x{valor:X} nao pode ser representado como immediate ARM.")


def splitVfpSingle(n):
    # Sn -> (4bits_principais, bit_extra); Sn = (4bits<<1)|bit_extra
    if not (0 <= n <= 31):
        raise ValueError(f"Registrador S{n} fora do intervalo 0-31")
    return (n >> 1) & 0xF, n & 1


def splitVfpDouble(n):
    # Dn -> (4bits_principais, bit_extra); bit_extra = bit4 de n
    if not (0 <= n <= 31):
        raise ValueError(f"Registrador D{n} fora do intervalo 0-31")
    return n & 0xF, (n >> 4) & 1


def vfpRegNum(nome):
    # 'd0' -> 0, 's12' -> 12
    nome = nome.strip().lower()
    if not (nome.startswith("d") or nome.startswith("s")):
        raise ValueError(f"Registrador VFP desconhecido: {nome!r}")
    return int(nome[1:])


def packBits(campos):
    # campos: lista de (valor, n_bits) do MSB para o LSB -> inteiro de 32 bits
    total_bits = sum(n for _, n in campos)
    if total_bits != 32:
        raise ValueError(f"Soma de bits = {total_bits}, esperado 32.")
    resultado = 0
    for valor, n in campos:
        if valor < 0 or valor >= (1 << n):
            raise ValueError(f"Valor {valor} nao cabe em {n} bits")
        resultado = (resultado << n) | valor
    return resultado & 0xFFFFFFFF


def toHex32(valor):
    return format(valor & 0xFFFFFFFF, "08x")
