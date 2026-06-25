# Encoders para instrucoes inteiras ARMv7 (nao-VFP):
# MOV, ADD, SUB, CMP, AND, ORR, B, BL, LDR, STR, PUSH, POP, MRC, MCR

from .encode_utils import (
    regNum, condCode, splitMnemonicCond, encodeDpImmediate,
    packBits, toHex32,
)

# opcodes data-processing (bits 24-21), Tabela A5-2
dp_opcode = {
    "AND": 0b0000, "EOR": 0b0001, "SUB": 0b0010, "RSB": 0b0011,
    "ADD": 0b0100, "ADC": 0b0101, "SBC": 0b0110, "RSC": 0b0111,
    "TST": 0b1000, "TEQ": 0b1001, "CMP": 0b1010, "CMN": 0b1011,
    "ORR": 0b1100, "MOV": 0b1101, "BIC": 0b1110, "MVN": 0b1111,
}

# nao escrevem em Rd (Rd=0, S forcado a 1)
somente_teste = {"TST", "TEQ", "CMP", "CMN"}

# nao usam Rn (instrucoes unarias)
unarias = {"MOV", "MVN"}


def _parseImm(operando):
    # converte '#123', '#0xFF', '#(0xF << 20)' para inteiro
    operando = operando.strip()
    if not operando.startswith("#"):
        raise ValueError(f"Esperava operando imediato (com '#'): {operando!r}")
    expr = operando[1:].strip()
    if expr.startswith("(") and expr.endswith(")"):
        expr = expr[1:-1]
    permitido = set("0123456789abcdefABCDEFxX<> ()+-")
    if not set(expr) <= permitido:
        raise ValueError(f"Expressao imediata nao suportada: {operando!r}")
    return int(eval(expr, {"__builtins__": {}}, {})) & 0xFFFFFFFF


def encodeDataProcessing(mnem, operandos, ctx):
    mnem_up = mnem.upper()
    set_flags = False
    base, suf = splitMnemonicCond(mnem_up, set(dp_opcode.keys()))
    if base not in dp_opcode and mnem_up.endswith("S"):
        candidato = mnem_up[:-1]
        cand_base, cand_suf = splitMnemonicCond(candidato, set(dp_opcode.keys()))
        if cand_base in dp_opcode:
            base, suf = cand_base, cand_suf
            set_flags = True

    if base not in dp_opcode:
        raise ValueError(f"Mnemonico data-processing desconhecido: {mnem!r}")

    cond = condCode(suf)
    opcode = dp_opcode[base]

    if base in somente_teste:
        s, rd = 1, 0
        if len(operandos) != 2:
            raise ValueError(f"{mnem} espera 2 operandos (Rn, #imm/Rm): {operandos}")
        rn = regNum(operandos[0])
        op2_str = operandos[1]
    elif base in unarias:
        s = 1 if set_flags else 0
        rn = 0
        if len(operandos) == 2:
            rd = regNum(operandos[0])
            op2_str = operandos[1]
        elif len(operandos) == 3:
            rd = regNum(operandos[0])
            op2_str = operandos[1] + ", " + operandos[2]
        else:
            raise ValueError(f"{mnem} numero de operandos inesperado: {operandos}")
    else:
        s = 1 if set_flags else 0
        if len(operandos) == 3:
            rd = regNum(operandos[0])
            rn = regNum(operandos[1])
            op2_str = operandos[2]
        elif len(operandos) == 2:
            rd = regNum(operandos[0])
            rn = rd
            op2_str = operandos[1]
        else:
            raise ValueError(f"{mnem} numero de operandos inesperado: {operandos}")

    op2_str = op2_str.strip()

    if op2_str.startswith("#"):
        valor = _parseImm(op2_str)
        imm12 = encodeDpImmediate(valor)
        instr = packBits([
            (cond, 4), (0b001, 3), (opcode, 4), (s, 1),
            (rn, 4), (rd, 4), (imm12, 12),
        ])
        return [instr]

    return _encodeDpRegisterForm(cond, opcode, s, rn, rd, op2_str, operandos)


# tipos de shift (bits 6-5 do operando registrador)
shift_type = {"LSL": 0b00, "LSR": 0b01, "ASR": 0b10, "ROR": 0b11}


def _encodeDpRegisterForm(cond, opcode, s, rn, rd, op2_str, operandos):
    # operando2 = registrador com shift opcional
    if "," in op2_str:
        partes = [p.strip() for p in op2_str.split(",")]
        rm_str, shift_str = partes[0], partes[1]
    elif len(operandos) >= 2 and operandos[-1].upper().startswith(("LSL", "LSR", "ASR", "ROR")):
        rm_str, shift_str = op2_str, operandos[-1]
    else:
        rm_str, shift_str = op2_str, None

    rm = regNum(rm_str)

    if shift_str is None:
        tipo_shift, qtd_shift = 0b00, 0
    else:
        partes_shift = shift_str.split()
        tipo = partes_shift[0].upper()
        if tipo not in shift_type:
            raise ValueError(f"Tipo de shift desconhecido: {shift_str!r}")
        tipo_shift = shift_type[tipo]
        qtd_shift = _parseImm(partes_shift[1])
        if not (0 <= qtd_shift <= 31):
            raise ValueError(f"Shift fora do intervalo 0-31: {qtd_shift}")

    operando2 = (qtd_shift << 7) | (tipo_shift << 5) | rm
    instr = packBits([
        (cond, 4), (0b000, 3), (opcode, 4), (s, 1),
        (rn, 4), (rd, 4), (operando2, 12),
    ])
    return [instr]


def encodeBranch(mnem, operandos, ctx):
    # B / BL / B<cond>: cond(4)|101(3)|L(1)|imm24(24)
    mnem_up = mnem.upper()
    if mnem_up == "BL":
        base, suf = "BL", ""
    elif mnem_up == "B":
        base, suf = "B", ""
    else:
        base, suf = splitMnemonicCond(mnem_up, {"B"})
        if base != "B":
            raise ValueError(f"Mnemonico de branch desconhecido: {mnem!r}")

    cond = condCode(suf)
    l = 1 if base == "BL" else 0

    if len(operandos) != 1:
        raise ValueError(f"{mnem} espera 1 operando (label): {operandos}")
    label = operandos[0].strip()

    if label not in ctx["labels"]:
        raise ValueError(f"Label nao encontrado: {label!r}")

    offset = ctx["labels"][label] - (ctx["endereco"] + 8)
    if offset % 4 != 0:
        raise ValueError(f"Offset de branch nao multiplo de 4: {offset}")

    imm24 = (offset // 4) & 0xFFFFFF
    instr = packBits([(cond, 4), (0b101, 3), (l, 1), (imm24, 24)])
    return [instr]


def encodeLoadStore(mnem, operandos, ctx):
    # LDR/STR/STRB Rt, [Rn{,#imm}]
    mnem_up = mnem.upper()
    if mnem_up == "LDR":
        l, b = 1, 0
    elif mnem_up == "STR":
        l, b = 0, 0
    elif mnem_up == "STRB":
        l, b = 0, 1
    else:
        raise ValueError(f"Mnemonico load/store desconhecido: {mnem!r}")

    if len(operandos) != 2:
        raise ValueError(f"{mnem} espera 2 operandos (Rt, [Rn{{,#imm}}]): {operandos}")

    rt = regNum(operandos[0])
    endereco = operandos[1].strip()
    if not (endereco.startswith("[") and endereco.endswith("]")):
        raise ValueError(f"{mnem} operando de endereco mal formado: {endereco!r}")

    partes = [p.strip() for p in endereco[1:-1].split(",")]
    rn = regNum(partes[0])

    if len(partes) == 1:
        imm = 0
    elif len(partes) == 2:
        if not partes[1].startswith("#"):
            raise ValueError(f"Offset deve ser imediato '#n': {partes[1]!r}")
        imm = _parseImm(partes[1])
    else:
        raise ValueError(f"Forma de endereco nao suportada: {endereco!r}")

    u = 1 if imm >= 0 else 0
    imm_abs = abs(imm)
    if imm_abs > 0xFFF:
        raise ValueError(f"Offset fora do intervalo +-4095: {imm}")

    cond = condCode("")
    instr = packBits([
        (cond, 4), (0b01, 2), (0, 1), (1, 1),  # I=0 (imm), P=1 (pre-index)
        (u, 1), (b, 1), (0, 1), (l, 1),
        (rn, 4), (rt, 4), (imm_abs, 12),
    ])
    return [instr]


def _parseReglist(operando):
    operando = operando.strip()
    if not (operando.startswith("{") and operando.endswith("}")):
        raise ValueError(f"Lista de registradores mal formada: {operando!r}")
    return [regNum(n.strip()) for n in operando[1:-1].split(",")]


def encodePush(mnem, operandos, ctx):
    # PUSH == STMDB sp!: P=1 U=0 W=1 L=0 Rn=13
    if len(operandos) != 1:
        raise ValueError(f"PUSH espera 1 operando (reglist): {operandos}")
    reg_list = 0
    for r in _parseReglist(operandos[0]):
        reg_list |= (1 << r)
    cond = condCode("")
    instr = packBits([
        (cond, 4), (0b100, 3),
        (1, 1), (0, 1), (0, 1), (1, 1), (0, 1),
        (13, 4), (reg_list, 16),
    ])
    return [instr]


def encodePop(mnem, operandos, ctx):
    # POP == LDMIA sp!: P=0 U=1 W=1 L=1 Rn=13
    if len(operandos) != 1:
        raise ValueError(f"POP espera 1 operando (reglist): {operandos}")
    reg_list = 0
    for r in _parseReglist(operandos[0]):
        reg_list |= (1 << r)
    cond = condCode("")
    instr = packBits([
        (cond, 4), (0b100, 3),
        (0, 1), (1, 1), (0, 1), (1, 1), (1, 1),
        (13, 4), (reg_list, 16),
    ])
    return [instr]


def _encodeMovwMovt(rd, valor16, is_movt):
    # MOVW (is_movt=False) ou MOVT (is_movt=True) com valor de 16 bits
    cond = condCode("")
    topo = 0b00110100 if is_movt else 0b00110000
    imm4 = (valor16 >> 12) & 0xF
    imm12 = valor16 & 0xFFF
    return packBits([(cond, 4), (topo, 8), (imm4, 4), (rd, 4), (imm12, 12)])


def encodeLdrPseudo(mnem, operandos, ctx):
    # LDR Rx, =VALOR -> MOVW Rx,#low16 + MOVT Rx,#high16
    if len(operandos) != 2:
        raise ValueError(f"LDR pseudo espera 2 operandos: {operandos}")
    rd = regNum(operandos[0])
    expr = operandos[1].strip()
    if not expr.startswith("="):
        raise ValueError(f"Esperava pseudo-LDR '=...': {expr!r}")
    valor = resolverSimboloOuNumero(expr[1:].strip(), ctx)
    return [
        _encodeMovwMovt(rd, valor & 0xFFFF, False),
        _encodeMovwMovt(rd, (valor >> 16) & 0xFFFF, True),
    ]


def resolverSimboloOuNumero(alvo, ctx):
    alvo = alvo.strip()
    try:
        return (int(alvo, 16) if alvo.lower().startswith("0x") else int(alvo)) & 0xFFFFFFFF
    except ValueError:
        pass
    if alvo in ctx["labels"]:
        return ctx["labels"][alvo] & 0xFFFFFFFF
    raise ValueError(f"Simbolo nao encontrado: {alvo!r}")


def encodeMrcMcr(mnem, operandos, ctx):
    # MRC/MCR p15,opc1,Rt,CRn,CRm,opc2
    mnem_up = mnem.upper()
    if mnem_up == "MRC":
        l = 1
    elif mnem_up == "MCR":
        l = 0
    else:
        raise ValueError(f"Mnemonico coprocessador desconhecido: {mnem!r}")

    if len(operandos) != 6:
        raise ValueError(f"{mnem} espera 6 operandos: {operandos}")

    coproc_str, opc1_str, rt_str, crn_str, crm_str, opc2_str = operandos
    coproc = int(coproc_str.strip().lstrip("pP"))
    opc1   = _parseSimpleInt(opc1_str)
    rt     = regNum(rt_str)
    crn    = int(crn_str.strip().lstrip("cC"))
    crm    = int(crm_str.strip().lstrip("cC"))
    opc2   = _parseSimpleInt(opc2_str)

    cond = condCode("")
    instr = packBits([
        (cond, 4), (0b1110, 4), (opc1, 3), (l, 1),
        (crn, 4), (rt, 4), (coproc, 4), (opc2, 3), (1, 1), (crm, 4),
    ])
    return [instr]


def _parseSimpleInt(s):
    s = s.strip()
    return int(s, 16) if s.lower().startswith("0x") else int(s)
