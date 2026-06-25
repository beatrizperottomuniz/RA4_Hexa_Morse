'''
Integrantes do grupo (ordem alfabética):
Beatriz Perotto Muniz - @beatrizperottomuniz

Nome do grupo no Canvas: RA3 6
'''
import sys
import os

from hex_utils.parser import lerArquivo
from hex_utils.encode_utils import toHex32
from hex_utils.encoders_core import (
    encodeDataProcessing,
    encodeBranch,
    encodeLoadStore,
    encodePush,
    encodePop,
    encodeLdrPseudo,
    encodeMrcMcr,
)
from hex_utils.encoders_vfp import (
    encodeVldrVstr,
    encodeVstmdbVldmia,
    encodeVfpArith,
    encodeVmovF64,
    encodeVcvtS32F64,
    encodeVcvtF64S32,
    encodeVmovCoreVfp,
    encodeVcmpF64,
    encodeVmrs,
    encodeFmxr,
)

# bases das instrucoes data-processing
dp_bases = {
    "MOV","MVN","ORR","AND","ADD","SUB","EOR","CMP",
    "CMN","TST","ADC","SBC","RSB","RSC","BIC",
}

cond_suffixes = [
    "EQ","NE","CS","HS","CC","LO","MI","PL","VS","VC","HI","LS",
    "GE","LT","GT","LE","AL",
]

# expande dp_bases com sufixos de condicao e flag S
all_dp = set()
for base in dp_bases:
    all_dp.add(base)
    all_dp.add(base + "S")
    for suf in cond_suffixes:
        all_dp.add(base + suf)
        all_dp.add(base + "S" + suf)

all_branch = {"B", "BL"}
for suf in cond_suffixes:
    all_branch.add("B" + suf)

vfp_arith_bases = {"VADD", "VSUB", "VMUL", "VDIV"}
shift_as_mov    = {"LSL", "LSR", "ASR", "ROR"}


def getEncoder(mnemonico):
    m = mnemonico.upper()
    if m in ("VLDR", "VSTR"):
        return encodeVldrVstr, m
    if m in ("VSTMDB", "VLDMIA"):
        return encodeVstmdbVldmia, m
    if m.split(".")[0] in vfp_arith_bases:
        return encodeVfpArith, m.split(".")[0]
    if m == "VMOV.F64":
        return encodeVmovF64, m
    if m == "VCVT.S32.F64":
        return encodeVcvtS32F64, m
    if m == "VCVT.F64.S32":
        return encodeVcvtF64S32, m
    if m == "VMRS":
        return encodeVmrs, m
    if m == "FMXR":
        return encodeFmxr, m
    if m == "VMOV":
        return _dispatchVmov, m
    if m == "VCMP.F64":
        return encodeVcmpF64, m
    if m in ("MRC", "MCR"):
        return encodeMrcMcr, m
    if m == "PUSH":
        return encodePush, m
    if m == "POP":
        return encodePop, m
    if m in all_branch:
        return encodeBranch, m
    if m in shift_as_mov:
        return _encodeShiftAsMov, m
    if m in ("LDR", "STR", "STRB"):
        return encodeLoadStore, m
    if m in all_dp:
        return encodeDataProcessing, m
    return None, None


def _dispatchVmov(mnem, operandos, ctx):
    # decide entre VMOV registrador-duplo ou VMOV core<->VFP
    op0 = operandos[0].strip().lower()
    if op0.startswith("d") or (len(operandos) > 1 and operandos[1].strip().lower().startswith("d")):
        return encodeVmovF64(mnem, operandos, ctx)
    return encodeVmovCoreVfp(mnem, operandos, ctx)


def _encodeShiftAsMov(mnem, operandos, ctx):
    # LSL/LSR/ASR/ROR Rd, Rm, #n -> MOV Rd, Rm, SHIFT #n
    if len(operandos) != 3:
        raise ValueError(f"{mnem} espera 3 operandos (Rd, Rm, #n): {operandos}")
    shift_str = f"{mnem.upper()} {operandos[2]}"
    return encodeDataProcessing("MOV", [operandos[0], operandos[1], shift_str], ctx)


def tamanhoLinha(linha):
    if linha.vazia:
        return 0
    if linha.diretiva:
        d = linha.diretiva.lower()
        if d == ".space":
            try:
                return int(linha.diretiva_args[0], 0)
            except Exception:
                return 0
        elif d == ".word":
            return 4 * len(linha.diretiva_args)
        return 0
    if linha.mnemonico is None:
        return 0
    m = linha.mnemonico.upper()
    if m == "LDR" and len(linha.operandos) == 2 and linha.operandos[1].strip().startswith("="):
        return 8  # pseudo-LDR expande para MOVW + MOVT
    return 4


def separarSecoes(linhas):
    em_data = em_text = False
    linhas_data, linhas_text = [], []
    for l in linhas:
        if l.diretiva and l.diretiva.lower() == ".data":
            em_data, em_text = True, False
            continue
        if l.diretiva and l.diretiva.lower() == ".text":
            em_text, em_data = True, False
            continue
        if em_data:
            linhas_data.append(l)
        elif em_text:
            linhas_text.append(l)
    return linhas_text, linhas_data


def primeiraPassada(linhas_text, linhas_data):
    # calcula o endereco de cada label sem gerar bytes
    labels = {}
    pc = 0x4  # 0x0 reservado para o branch inicial para _start
    for l in linhas_text:
        if l.label:
            labels[l.label] = pc
        pc += tamanhoLinha(l)
    inicio_data = pc
    for l in linhas_data:
        if l.label:
            labels[l.label] = pc
        pc += tamanhoLinha(l)
    return labels, inicio_data


def segundaPassada(linhas, labels, endereco_inicial):
    # gera os words de 32 bits para cada instrucao/diretiva
    resultados = []
    pc = endereco_inicial

    for linha in linhas:
        tam = tamanhoLinha(linha)
        ctx = {"endereco": pc, "labels": labels, "simbolos": labels}

        if linha.vazia or tam == 0:
            pc += tam
            continue

        if linha.diretiva:
            d = linha.diretiva.lower()
            if d == ".word":
                hex_vals = [toHex32(int(a, 0) & 0xFFFFFFFF) for a in linha.diretiva_args]
                resultados.append({"endereco": pc, "hex": hex_vals,
                                   "mnem": ".word", "linha": linha.numero_linha})
            elif d == ".space":
                words = (tam + 3) // 4
                resultados.append({"endereco": pc, "hex": ["00000000"] * words,
                                   "mnem": ".space", "linha": linha.numero_linha})
            pc += tam
            continue

        if linha.mnemonico is None:
            pc += tam
            continue

        m = linha.mnemonico.upper()

        if m == "LDR" and len(linha.operandos) == 2 and linha.operandos[1].strip().startswith("="):
            try:
                words = encodeLdrPseudo(m, linha.operandos, ctx)
            except Exception as e:
                raise RuntimeError(
                    f"Linha {linha.numero_linha}: {e}\n  -> {linha.linha_original.strip()}"
                ) from e
            resultados.append({"endereco": pc, "hex": [toHex32(w) for w in words],
                               "mnem": "LDR(pseudo)", "linha": linha.numero_linha})
            pc += 8
            continue

        encoder, mnem_norm = getEncoder(m)
        if encoder is None:
            raise RuntimeError(
                f"Linha {linha.numero_linha}: mnemonico nao suportado: {m!r}\n"
                f"  -> {linha.linha_original.strip()}"
            )

        try:
            words = encoder(mnem_norm, linha.operandos, ctx)
        except Exception as e:
            raise RuntimeError(
                f"Linha {linha.numero_linha}: {e}\n  -> {linha.linha_original.strip()}"
            ) from e

        resultados.append({"endereco": pc, "hex": [toHex32(w) for w in words],
                           "mnem": mnem_norm, "linha": linha.numero_linha})
        pc += tam

    return resultados


def traduzir(arquivo_asm, arquivo_saida="saida_final.hex"):
    linhas = lerArquivo(arquivo_asm)
    linhas_text, linhas_data = separarSecoes(linhas)

    labels, inicio_data = primeiraPassada(linhas_text, linhas_data)

    res_text = segundaPassada(linhas_text, labels, endereco_inicial=0x4)
    res_data = segundaPassada(linhas_data, labels, endereco_inicial=inicio_data)

    # branch inicial em 0x0 para _start (CPUlator comeca em 0x0)
    ctx_start = {"endereco": 0x0, "labels": labels, "simbolos": labels}
    branch_words = encodeBranch("B", ["_start"], ctx_start)
    branch_hex = toHex32(branch_words[0])

    with open(arquivo_saida, "w", encoding="utf-8") as f:
        val = int(branch_hex, 16)
        for i in range(4):
            f.write(f"{(val >> (i*8)) & 0xFF:02X}\n")
        for r in res_text + res_data:
            for wh in r["hex"]:
                val = int(wh, 16)
                for i in range(4):
                    f.write(f"{(val >> (i*8)) & 0xFF:02X}\n")

    total = 1 + sum(len(r["hex"]) for r in res_text + res_data)
    print(f"Hex: {arquivo_saida} ({total} words, {total*4} bytes)")
    return res_text, res_data, labels


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 gerarHex.py <arquivo.s> [saida.hex]")
        sys.exit(1)
    saida = sys.argv[2] if len(sys.argv) > 2 else "saida_final.hex"
    try:
        traduzir(sys.argv[1], saida)
    except RuntimeError as e:
        print(f"\nERRO: {e}")
        sys.exit(1)
