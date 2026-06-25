# Encoders para instrucoes VFP (precisao dupla, D0-D15 / S0-S31).
# cond e sempre AL (1110) nas instrucoes usadas no projeto.

from .encode_utils import packBits, toHex32, splitVfpDouble, splitVfpSingle, vfpRegNum

cond_al = 0b1110


def encodeVldrVstr(mnem, operandos, ctx):
    # VLDR/VSTR Dd, [Rn]   (offset 0)
    mnem_up = mnem.upper()
    if mnem_up == "VLDR":
        l = 1
    elif mnem_up == "VSTR":
        l = 0
    else:
        raise ValueError(f"Mnemonico VFP load/store desconhecido: {mnem!r}")

    if len(operandos) != 2:
        raise ValueError(f"{mnem} espera 2 operandos: {operandos}")

    dd = vfpRegNum(operandos[0])
    vd4, d = splitVfpDouble(dd)

    endereco = operandos[1].strip()
    if not (endereco.startswith("[") and endereco.endswith("]")):
        raise ValueError(f"{mnem} operando de endereco mal formado: {endereco!r}")
    partes = [p.strip() for p in endereco[1:-1].split(",")]
    rn = int(partes[0].lower().lstrip("r"))

    if len(partes) > 1:
        raise ValueError(f"{mnem} com offset != 0 nao suportado: {endereco!r}")

    instr = packBits([
        (cond_al, 4), (0b1101, 4),
        (1, 1), (d, 1), (0, 1), (l, 1),
        (rn, 4), (vd4, 4), (0b1011, 4), (0, 8),
    ])
    return [instr]


def encodeVstmdbVldmia(mnem, operandos, ctx):
    # VSTMDB sp!, {Dd} (VPUSH) / VLDMIA sp!, {Dd} (VPOP)
    mnem_up = mnem.upper()
    if len(operandos) != 2:
        raise ValueError(f"{mnem} espera 2 operandos (sp!, {{Dd}}): {operandos}")

    base = operandos[0].strip().lower()
    if base not in ("sp!",):
        raise ValueError(f"{mnem} so suporta 'sp!' como base: {operandos}")

    reglist = operandos[1].strip()
    if not (reglist.startswith("{") and reglist.endswith("}")):
        raise ValueError(f"{mnem} lista de registradores mal formada: {reglist!r}")
    nomes = [n.strip() for n in reglist[1:-1].split(",")]
    if len(nomes) != 1:
        raise ValueError(f"{mnem} so suporta 1 registrador (Dd) no projeto: {reglist!r}")

    dd = vfpRegNum(nomes[0])
    vd4, d = splitVfpDouble(dd)

    if mnem_up == "VSTMDB":
        instr = packBits([
            (cond_al, 4), (0b1101, 4), (0b0, 1), (d, 1),
            (0b101101, 6), (vd4, 4), (0b1011, 4), (0b0000001, 7), (0, 1),
        ])
    elif mnem_up == "VLDMIA":
        instr = packBits([
            (cond_al, 4), (0b1100, 4), (0b1, 1), (d, 1),
            (0b111101, 6), (vd4, 4), (0b1011, 4), (0b0000001, 7), (0, 1),
        ])
    else:
        raise ValueError(f"Mnemonico desconhecido: {mnem!r}")
    return [instr]


# opcodes e bit opc3 para operacoes aritmeticas VFP
vfp_arith_opcode = {
    "VADD": (0b0011, 0),
    "VSUB": (0b0011, 1),
    "VMUL": (0b0010, 0),
    "VDIV": (0b1000, 0),
}


def encodeVfpArith(mnem, operandos, ctx):
    # VADD/VSUB/VMUL/VDIV .F64 Dd, Dn, Dm
    mnem_up = mnem.upper()
    if mnem_up not in vfp_arith_opcode:
        raise ValueError(f"Mnemonico aritmetico VFP desconhecido: {mnem!r}")
    opcode4, opc3 = vfp_arith_opcode[mnem_up]

    if len(operandos) != 3:
        raise ValueError(f"{mnem}.F64 espera 3 operandos (Dd,Dn,Dm): {operandos}")

    dd = vfpRegNum(operandos[0])
    dn = vfpRegNum(operandos[1])
    dm = vfpRegNum(operandos[2])
    vd4, d = splitVfpDouble(dd)
    vn4, n = splitVfpDouble(dn)
    vm4, m = splitVfpDouble(dm)

    instr = packBits([
        (cond_al, 4), (0b1110, 4), (opcode4, 4), (vn4, 4),
        (vd4, 4), (0b101, 3), (1, 1), (n, 1), (opc3, 1), (m, 1), (0, 1), (vm4, 4),
    ])
    return [instr]


def encodeVmovF64(mnem, operandos, ctx):
    # VMOV.F64 Dd, Dm
    if len(operandos) != 2:
        raise ValueError(f"VMOV.F64 espera 2 operandos (Dd,Dm): {operandos}")
    dd = vfpRegNum(operandos[0])
    dm = vfpRegNum(operandos[1])
    vd4, d = splitVfpDouble(dd)
    vm4, m = splitVfpDouble(dm)
    instr = packBits([
        (cond_al, 4), (0b1110, 4), (0b1011, 4), (0b0000, 4),
        (vd4, 4), (0b101101, 6), (m, 1), (0, 1), (vm4, 4),
    ])
    return [instr]


def encodeVcvtS32F64(mnem, operandos, ctx):
    # VCVT.S32.F64 Sd, Dm (double -> int, truncamento)
    if len(operandos) != 2:
        raise ValueError(f"VCVT.S32.F64 espera 2 operandos (Sd,Dm): {operandos}")
    sd = vfpRegNum(operandos[0])
    dm = vfpRegNum(operandos[1])
    vd4, d = splitVfpSingle(sd)
    vm4, m = splitVfpDouble(dm)
    instr = packBits([
        (cond_al, 4), (0b1110, 4), (0b1011, 4), (0b1101, 4),
        (vd4, 4), (0b101111, 6), (m, 1), (0, 1), (vm4, 4),
    ])
    return [instr]


def encodeVcvtF64S32(mnem, operandos, ctx):
    # VCVT.F64.S32 Dd, Sm (int -> double)
    if len(operandos) != 2:
        raise ValueError(f"VCVT.F64.S32 espera 2 operandos (Dd,Sm): {operandos}")
    dd = vfpRegNum(operandos[0])
    sm = vfpRegNum(operandos[1])
    vd4, d = splitVfpDouble(dd)
    vm4, m = splitVfpSingle(sm)
    instr = packBits([
        (cond_al, 4), (0b1110, 4), (0b1011, 4), (0b1000, 4),
        (vd4, 4), (0b101111, 6), (m, 1), (0, 1), (vm4, 4),
    ])
    return [instr]


def encodeVmovCoreVfp(mnem, operandos, ctx):
    # VMOV Rt, Sn (VFP->core) ou VMOV Sn, Rt (core->VFP)
    if len(operandos) != 2:
        raise ValueError(f"VMOV espera 2 operandos: {operandos}")
    op0 = operandos[0].strip().lower()
    op1 = operandos[1].strip().lower()

    if op0.startswith("r"):
        to_arm = True
        rt = int(op0.lstrip("r"))
        sn = vfpRegNum(op1)
    elif op0.startswith("s"):
        to_arm = False
        sn = vfpRegNum(op0)
        rt = int(op1.lstrip("r"))
    else:
        raise ValueError(f"VMOV operandos nao reconhecidos: {operandos}")

    vn4, n = splitVfpSingle(sn)
    op_bit = 1 if to_arm else 0
    instr = packBits([
        (cond_al, 4), (0b1110, 4), (0b000, 3), (op_bit, 1),
        (vn4, 4), (rt, 4), (0b1010, 4), (n, 1), (0b001, 3), (0, 4),
    ])
    return [instr]


def encodeVcmpF64(mnem, operandos, ctx):
    # VCMP.F64 Dd, Dm  ou  VCMP.F64 Dd, #0.0
    if len(operandos) != 2:
        raise ValueError(f"VCMP.F64 espera 2 operandos: {operandos}")
    dd = vfpRegNum(operandos[0])
    vd4, d = splitVfpDouble(dd)
    op1 = operandos[1].strip()

    if op1 == "#0.0":
        instr = packBits([
            (cond_al, 4), (0b1110, 4), (0b1011, 4), (0b0101, 4),
            (vd4, 4), (0b101101, 6), (0, 1), (0, 1), (0, 4),
        ])
    else:
        dm = vfpRegNum(op1)
        vm4, m = splitVfpDouble(dm)
        instr = packBits([
            (cond_al, 4), (0b1110, 4), (0b1011, 4), (0b0100, 4),
            (vd4, 4), (0b101101, 6), (m, 1), (0, 1), (vm4, 4),
        ])
    return [instr]


def encodeVmrs(mnem, operandos, ctx):
    # VMRS APSR_nzcv, FPSCR (instrucao fixa)
    instr = packBits([
        (cond_al, 4), (0b1110, 4), (0b1111, 4), (0b0001, 4),
        (0b1111, 4), (0b1010, 4), (0b0001, 4), (0b0000, 4),
    ])
    return [instr]


# registradores de sistema VFP
fpsys_reg = {"FPSID": 0b0000, "FPSCR": 0b0001, "FPEXC": 0b1000}


def encodeFmxr(mnem, operandos, ctx):
    # FMXR FPEXC, Rt  (move ARM core -> registrador sistema VFP)
    if len(operandos) != 2:
        raise ValueError(f"FMXR espera 2 operandos: {operandos}")
    sysreg_str = operandos[0].strip().upper()
    if sysreg_str not in fpsys_reg:
        raise ValueError(f"Registrador de sistema VFP desconhecido: {sysreg_str!r}")
    sysreg = fpsys_reg[sysreg_str]
    rt = int(operandos[1].strip().lower().lstrip("r"))
    instr = packBits([
        (cond_al, 4), (0b1110, 4), (0b1110, 4), (sysreg, 4),
        (rt, 4), (0b1010, 4), (0b0001, 4), (0b0000, 4),
    ])
    return [instr]
