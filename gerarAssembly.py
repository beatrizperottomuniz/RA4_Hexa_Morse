'''
Integrantes do grupo (ordem alfabética):
Beatriz Perotto Muniz - @beatrizperottomuniz

Nome do grupo no Canvas: RA3 6
'''
import struct
from globalVars import string_pool_global

constantes       = {}
variaveis        = set()
resultados_linha = []
for_ctrs         = []
contador_label   = 0
morse_usado      = False

# calibracao do tempo morse ----
# altere p/ajustar a velocidade do morse
# calibrado no CPUlator ARMv7 DE1-SoC: 0x000F0000 (983040 iterações) =(prox) 150ms
morse_unidade_ms = 150

def calcArmImm(ms):
    # retorna o ARM immediate (inteiro) valido mais prox para ms
    alvo = int(ms * (983040 / 150))
    melhor_val  = 0x000F0000
    melhor_diff = abs(melhor_val - alvo)
    for imm8 in range(1, 256):
        for rot in range(16):
            shift = 2 * rot
            if shift == 0:
                cand = imm8
            else:
                cand = ((imm8 >> shift) | (imm8 << (32 - shift))) & 0xFFFFFFFF
            diff = abs(cand - alvo)
            if diff < melhor_diff:
                melhor_diff = diff
                melhor_val  = cand
    return melhor_val


morse_tabela = {
    'A': '.-',   'B': '-...',  'C': '-.-.',  'D': '-..',
    'E': '.',    'F': '..-.',  'G': '--.',   'H': '....',
    'I': '..',   'J': '.---',  'K': '-.-',   'L': '.-..',
    'M': '--',   'N': '-.',    'O': '---',   'P': '.--.',
    'Q': '--.-', 'R': '.-.',   'S': '...',   'T': '-',
    'U': '..-',  'V': '...-',  'W': '.--',   'X': '-..-',
    'Y': '-.--', 'Z': '--..',
    '0': '-----', '1': '.----', '2': '..---', '3': '...--',
    '4': '....-', '5': '.....', '6': '-....', '7': '--...',
    '8': '---..', '9': '----.'
}


# aux

def novoLabel(prefixo):
    global contador_label
    contador_label += 1
    return f"{prefixo}_{contador_label}"


def doubleParaBits(valor):
    packed     = struct.pack('<d', float(valor))
    word_baixo = struct.unpack('<I', packed[0:4])[0]
    word_alto  = struct.unpack('<I', packed[4:8])[0]
    return word_baixo, word_alto


def lexemaTerminal(no):
    t = no.token
    if t is None:
        return ""
    return string_pool_global.obterString(t.simbolo_id)


def encontrarTerminal(no):
    if no.token is not None:
        return no
    for filho in no.filhos:
        resultado = encontrarTerminal(filho)
        if resultado:
            return resultado
    return None


def pushConst(asm, val_str):
    val = str(float(val_str))
    if val not in constantes:
        constantes[val] = novoLabel('CONST')
    lbl = constantes[val]
    asm.append(f"    LDR r0, ={lbl}")
    asm.append(f"    VLDR d0, [r0]")
    asm.append(f"    VSTMDB sp!, {{d0}}")
    return val


# morse

def gerarMorse(texto, asm):
    global morse_usado
    morse_usado = True
    chars = list(texto.upper())
    ultimo_letra = -1
    for i, char in enumerate(chars):
        if char in morse_tabela:
            ultimo_letra = i
    pendente_gap_letra = False
    for i, char in enumerate(chars):
        if char == ' ':
            pendente_gap_letra = False
            asm.append("    BL MORSE_GAP_WORD")
        elif char in morse_tabela:
            if pendente_gap_letra:
                asm.append("    BL MORSE_GAP_LETTER")
            simbolos = morse_tabela[char]
            for j, simb in enumerate(simbolos):
                if simb == '.':
                    asm.append("    BL MORSE_DOT")
                else:
                    asm.append("    BL MORSE_DASH")
                if j < len(simbolos) - 1:
                    asm.append("    BL MORSE_GAP_INTRA")
            pendente_gap_letra = (i < ultimo_letra)
    asm.append("    BL MORSE_GAP_WORD")
    pushConst(asm, "0.0")  # void, igual FOR/IF


# ops aritm

def gerarOpArit(tipo, asm):
    asm.append(f"    VLDMIA sp!, {{d1}}")
    asm.append(f"    VLDMIA sp!, {{d0}}")

    if tipo == 'PLUS':
        asm.append("    VADD.F64 d0, d0, d1")
    elif tipo == 'MINUS':
        asm.append("    VSUB.F64 d0, d0, d1")
    elif tipo == 'MULT':
        asm.append("    VMUL.F64 d0, d0, d1")
    elif tipo == 'DIV':
        asm.append("    VDIV.F64 d0, d0, d1")
    elif tipo == 'INT_DIV':
        asm.append("    VDIV.F64 d2, d0, d1")
        asm.append("    VCVT.S32.F64 s4, d2")
        asm.append("    VCVT.F64.S32 d0, s4")
    elif tipo == 'MOD':
        asm.append("    VDIV.F64 d2, d0, d1")
        asm.append("    VCVT.S32.F64 s4, d2")
        asm.append("    VCVT.F64.S32 d2, s4")
        asm.append("    VMUL.F64 d2, d2, d1")
        asm.append("    VSUB.F64 d0, d0, d2")
    elif tipo == 'POW':
        lbl_loop = novoLabel('POW_LOOP')
        lbl_fim  = novoLabel('POW_FIM')
        asm.append("    VMOV.F64 d2, d0")
        asm.append("    VCVT.S32.F64 s0, d1")
        asm.append("    VMOV r2, s0")
        if "1.0" not in constantes:
            constantes["1.0"] = novoLabel('CONST')
        asm.append(f"    LDR r0, ={constantes['1.0']}")
        asm.append("    VLDR d0, [r0]")
        asm.append(f"{lbl_loop}:")
        asm.append("    CMP r2, #0")
        asm.append(f"    BLE {lbl_fim}")
        asm.append("    VMUL.F64 d0, d0, d2")
        asm.append("    SUB r2, r2, #1")
        asm.append(f"    B {lbl_loop}")
        asm.append(f"{lbl_fim}:")

    asm.append("    VSTMDB sp!, {d0}")


# ops rel

def gerarOpRel(tipo, asm):
    asm.append(f"    VLDMIA sp!, {{d1}}")
    asm.append(f"    VLDMIA sp!, {{d0}}")
    asm.append("    VCMP.F64 d0, d1")
    asm.append("    VMRS APSR_nzcv, FPSCR")
    asm.append("    MOV r0, #0")

    cond = {'EQ': 'EQ', 'NEQ': 'NE', 'GT': 'GT',
            'LT': 'LT', 'GTE': 'GE', 'LTE': 'LE'}[tipo]
    asm.append(f"    MOV{cond} r0, #1")

    asm.append("    VMOV s0, r0")
    asm.append("    VCVT.F64.S32 d0, s0")
    asm.append("    VSTMDB sp!, {d0}")


def gerarOpBinTerminal(tipo, asm):
    ops_arit = {'PLUS', 'MINUS', 'MULT', 'DIV', 'INT_DIV', 'MOD', 'POW'}
    if tipo in ops_arit:
        gerarOpArit(tipo, asm)
    else:
        gerarOpRel(tipo, asm)


# estrut controle

def gerarIf(corpo_no, asm):
    lbl_falso = novoLabel('IF_FALSE')
    lbl_fim   = novoLabel('IF_FIM')

    asm.append(f"    VLDMIA sp!, {{d0}}")
    asm.append(f"    VCMP.F64 d0, #0.0")
    asm.append(f"    VMRS APSR_nzcv, FPSCR")
    asm.append(f"    BEQ {lbl_falso}")

    gerarStmt(corpo_no, asm)
    asm.append(f"    VLDMIA sp!, {{d0}}")  # descarta resultado do corpo
    asm.append(f"    B {lbl_fim}")

    asm.append(f"{lbl_falso}:")
    asm.append(f"{lbl_fim}:")
    pushConst(asm, "0.0")# julgamento ok — empilha 0


def gerarFor(corpo_no, asm):
    lbl_ctr  = novoLabel('FOR_CTR')
    lbl_loop = novoLabel('FOR_LOOP')
    lbl_fim  = novoLabel('FOR_FIM')
    for_ctrs.append(lbl_ctr)

    asm.append(f"    VLDMIA sp!, {{d0}}")
    asm.append(f"    VCVT.S32.F64 s0, d0")
    asm.append(f"    VMOV r2, s0")
    asm.append(f"    LDR r1, ={lbl_ctr}")
    asm.append(f"    STR r2, [r1]")

    if "0.0" not in constantes:
        constantes["0.0"] = novoLabel('CONST')
    asm.append(f"    LDR r0, ={constantes['0.0']}")
    asm.append(f"    VLDR d3, [r0]")

    asm.append(f"{lbl_loop}:")
    asm.append(f"    LDR r1, ={lbl_ctr}")
    asm.append(f"    LDR r2, [r1]")
    asm.append(f"    CMP r2, #0")
    asm.append(f"    BLE {lbl_fim}")

    gerarStmt(corpo_no, asm)
    asm.append(f"    VLDMIA sp!, {{d0}}")  # descarta resultado do corpo

    asm.append(f"    LDR r1, ={lbl_ctr}")
    asm.append(f"    LDR r2, [r1]")
    asm.append(f"    SUB r2, r2, #1")
    asm.append(f"    STR r2, [r1]")
    asm.append(f"    B {lbl_loop}")

    asm.append(f"{lbl_fim}:")
    pushConst(asm, "0.0")# julgamento ok


def gerarStmt(no, asm):
    gerarRpn(no.filhos[1], asm)


# lit num

def gerarNum(no, asm):
    filho0 = no.filhos[0]
    if filho0.tipo == 'MINUS':
        terminal = no.filhos[1].filhos[0]
        lex      = lexemaTerminal(terminal)
        val_str  = str(float('-' + lex))
    else:
        lex     = lexemaTerminal(filho0)
        val_str = str(float(lex))
    return pushConst(asm, val_str)


def gerarRpnTailNum(no, asm, ultimo_num):
    filho0 = no.filhos[0]

    if filho0.tipo == 'KEYWORD_RES':
        n           = int(float(ultimo_num))
        linha_atual = len(resultados_linha) + 1
        indice      = (linha_atual - 1) - n
        asm.append(f"    ADD sp, sp, #8")
        if n == 0 or indice < 0 or indice >= len(resultados_linha):
            pushConst(asm, "0.0")
        else:
            lbl_res = resultados_linha[indice]
            asm.append(f"    LDR r0, ={lbl_res}")
            asm.append(f"    VLDR d0, [r0]")
            asm.append(f"    VSTMDB sp!, {{d0}}")

    elif filho0.tipo == 'ID':
        lex = lexemaTerminal(filho0)
        variaveis.add(lex)
        asm.append(f"    VLDMIA sp!, {{d0}}")
        asm.append(f"    LDR r1, ={lex}_MEM")
        asm.append(f"    VSTR d0, [r1]")
        asm.append(f"    VSTMDB sp!, {{d0}}")

    elif filho0.tipo == 'num':
        gerarNum(filho0, asm)
        terminal = encontrarTerminal(no.filhos[1])
        gerarOpBinTerminal(terminal.tipo, asm)

    else:  # stmt
        op_terminal = encontrarTerminal(no.filhos[1])
        tipo_op     = op_terminal.tipo if op_terminal else None
        if tipo_op == 'KEYWORD_FOR':
            gerarFor(filho0, asm)
        else:
            gerarStmt(filho0, asm)
            gerarOpBinTerminal(tipo_op, asm)


def gerarRpnTailStmt(no, asm):
    filho0 = no.filhos[0]

    if filho0.tipo == 'ID':
        lex = lexemaTerminal(filho0)
        variaveis.add(lex)
        asm.append(f"    VLDMIA sp!, {{d0}}")
        asm.append(f"    LDR r1, ={lex}_MEM")
        asm.append(f"    VSTR d0, [r1]")
        asm.append(f"    VSTMDB sp!, {{d0}}")

    elif filho0.tipo == 'num':
        gerarNum(filho0, asm)
        terminal = encontrarTerminal(no.filhos[1])
        gerarOpBinTerminal(terminal.tipo, asm)

    else:
        op_terminal = encontrarTerminal(no.filhos[1])
        tipo_op     = op_terminal.tipo if op_terminal else None
        if tipo_op == 'KEYWORD_IF':
            gerarIf(filho0, asm)
        else:
            gerarStmt(filho0, asm)
            gerarOpBinTerminal(tipo_op, asm)


def gerarRpn(no, asm):
    filho0 = no.filhos[0]

    if filho0.tipo == 'STRING':
        texto = lexemaTerminal(filho0)
        gerarMorse(texto, asm)

    elif filho0.tipo == 'num':
        ultimo_num = gerarNum(filho0, asm)
        gerarRpnTailNum(no.filhos[1], asm, ultimo_num)

    elif filho0.tipo == 'stmt':
        gerarStmt(filho0, asm)
        gerarRpnTailStmt(no.filhos[1], asm)

    else:
        lex = lexemaTerminal(filho0)
        variaveis.add(lex)
        asm.append(f"    LDR r0, ={lex}_MEM")
        asm.append(f"    VLDR d0, [r0]")
        asm.append(f"    VSTMDB sp!, {{d0}}")


def gerarListItem(no, asm):
    if no.filhos[0].tipo == 'KEYWORD_END':
        return

    linha_atual = len(resultados_linha) + 1
    no_rpn      = no.filhos[0]
    categoria   = getattr(no_rpn, 'categoria_semantica', None)
    tipo_inf    = getattr(no_rpn, 'tipo_inferido', None)

    comentario = f"\n    @ linha {linha_atual}"
    if categoria:
        comentario += f"  [{categoria}]"
    if tipo_inf:
        comentario += f"  : {tipo_inf}"
    comentario += "  --------"
    asm.append(comentario)

    gerarRpn(no_rpn, asm)

    lbl_linha = f"RES_LINHA_{linha_atual}"
    resultados_linha.append(lbl_linha)
    asm.append(f"    VLDMIA sp!, {{d0}}")
    asm.append(f"    LDR r3, ={lbl_linha}")
    asm.append(f"    VSTR d0, [r3]")
    asm.append(f"    LDR r0, ={lbl_linha}")
    asm.append(f"    BL PRINT_RES_HEX")

    if len(no.filhos) > 2:
        gerarListStmts(no.filhos[2], asm)


def gerarListStmts(no, asm):
    gerarListItem(no.filhos[1], asm)


# fim arquivo

def finalizarAssembly(codigo, arquivo):
    out = [
        "    .syntax unified",
        "    .arch armv7-a",
        "    .fpu vfpv3-d16",
        "",
        "    .data"
    ]

    for v in variaveis:
        out.append(f"{v}_MEM: .space 8")
    for res in resultados_linha:
        out.append(f"{res}: .space 8")
    for ctr in for_ctrs:
        out.append(f"{ctr}: .space 4")

    for val, lbl in constantes.items():
        wb, wa = doubleParaBits(val)
        out.append(f"{lbl}: .word 0x{wb:08X}, 0x{wa:08X} @ valor: {val}")

    out.extend([
        "",
        "    .text",
        """
  @ UART_PUTCHAR - envia r0 (1 byte) por UART
  UART_PUTCHAR:
      PUSH {r1, r2, lr}
      LDR r2, =0xFF201000
  _UART_WAIT:
      LDR r1, [r2, #4]
      LSR r1, r1, #16
      CMP r1, #0
      BEQ _UART_WAIT
      STRB r0, [r2]
      POP {r1, r2, pc}

  @ PRINT_NIBBLES_32 - imprime r8 como 8 digitos hex
  PRINT_NIBBLES_32:
      PUSH {r6, r8, lr}
      MOV r6, #8
  _LOOP_NIB:
      MOV r0, r8, LSR #28
      AND r0, r0, #0xF
      CMP r0, #10
      ADDLT r0, r0, #48       @ 0-9 : '0' = 48
      ADDGE r0, r0, #55       @ A-F : 'A'-10 = 55
      BL UART_PUTCHAR
      LSL r8, r8, #4
      SUBS r6, r6, #1
      BNE _LOOP_NIB
      POP {r6, r8, pc}

  @ PRINT_RES_HEX - imprime double de 64 bits em hex
  @ r0 = endereco do valor
  PRINT_RES_HEX:
      PUSH {r4, r5, r8, lr}
      LDR r4, [r0]            @ word baixo
      LDR r5, [r0, #4]        @ word alto
      MOV r0, #48             @ '0'
      BL UART_PUTCHAR
      MOV r0, #120            @ 'x'
      BL UART_PUTCHAR
      MOV r8, r5              @ word alto primeiro
      BL PRINT_NIBBLES_32
      MOV r8, r4              @ word baixo
      BL PRINT_NIBBLES_32
      MOV r0, #13             @ \\r
      BL UART_PUTCHAR
      MOV r0, #10             @ \\n
      BL UART_PUTCHAR
      POP {r4, r5, r8, pc}
        """,
    ])

# DOT= 2 unidades =  300ms
# DASH= 4 unidades =  600ms
# GAP_INTRA= 3 unidades =  450ms (entre simbolos da mesma letra)
# GAP_LETTER=6 unidades =  900ms (entre letras)
# GAP_WORD =13 unidades = ~1950ms (apos string completa)
# LED LEDR0: endereco 0xFF200000 (DE1-SoC, CPUlator v16.1)

    if morse_usado:
        out.append(f"""
@ ---- MORSE subroutines ----
MORSE_UNIT_DELAY:
    PUSH {{R3, LR}}
    MOV  R3, #{hex(calcArmImm(morse_unidade_ms))}
MORSE_UNIT_LOOP:
    SUBS R3, R3, #1
    BNE  MORSE_UNIT_LOOP
    POP  {{R3, PC}}

MORSE_DOT:
    PUSH {{R1, R4, LR}}
    MOV  R4, #0xFF000000
    ORR  R4, R4, #0x00200000
    MOV  R1, #1
    STR  R1, [R4]
    BL   MORSE_UNIT_DELAY
    BL   MORSE_UNIT_DELAY
    MOV  R1, #0
    STR  R1, [R4]
    POP  {{R1, R4, PC}}

MORSE_DASH:
    PUSH {{R1, R4, LR}}
    MOV  R4, #0xFF000000
    ORR  R4, R4, #0x00200000
    MOV  R1, #1
    STR  R1, [R4]
    BL   MORSE_UNIT_DELAY
    BL   MORSE_UNIT_DELAY
    BL   MORSE_UNIT_DELAY
    BL   MORSE_UNIT_DELAY
    MOV  R1, #0
    STR  R1, [R4]
    POP  {{R1, R4, PC}}

MORSE_GAP_INTRA:
    PUSH {{LR}}
    BL   MORSE_UNIT_DELAY
    BL   MORSE_UNIT_DELAY
    BL   MORSE_UNIT_DELAY
    POP  {{PC}}

MORSE_GAP_LETTER:
    PUSH {{LR}}
    BL   MORSE_UNIT_DELAY
    BL   MORSE_UNIT_DELAY
    BL   MORSE_UNIT_DELAY
    BL   MORSE_UNIT_DELAY
    BL   MORSE_UNIT_DELAY
    BL   MORSE_UNIT_DELAY
    POP  {{PC}}

MORSE_GAP_WORD:
    PUSH {{LR}}
    BL   MORSE_UNIT_DELAY
    BL   MORSE_UNIT_DELAY
    BL   MORSE_UNIT_DELAY
    BL   MORSE_UNIT_DELAY
    BL   MORSE_UNIT_DELAY
    BL   MORSE_UNIT_DELAY
    BL   MORSE_UNIT_DELAY
    BL   MORSE_UNIT_DELAY
    BL   MORSE_UNIT_DELAY
    BL   MORSE_UNIT_DELAY
    BL   MORSE_UNIT_DELAY
    BL   MORSE_UNIT_DELAY
    BL   MORSE_UNIT_DELAY
    POP  {{PC}}
""")

    out.extend([
        "    .global _start",
        "_start:",
        "    MRC p15, 0, r1, c1, c0, 2",
        "    ORR r1, r1, #(0xF << 20)",
        "    MCR p15, 0, r1, c1, c0, 2",
        "    MOV r1, #0x40000000",
        "    FMXR FPEXC, r1"
    ])

    out.extend(codigo)

    out.extend([
        "",
        "_end:",
        "    B _end"
    ])

    texto_final = "\n".join(out)
    with open(arquivo, "w", encoding="utf-8") as f:
        f.write(texto_final)


# func aluno

def gerarAssembly(arvoreAtribuida):
    arquivo = "saida_assembly.s"
    global constantes, variaveis, resultados_linha, for_ctrs, contador_label, morse_usado

    if arvoreAtribuida is None:
        print("[gerarAssembly] árvore não disponível — Assembly não gerado.")
        return None

    constantes       = {}
    variaveis        = set()
    resultados_linha = []
    for_ctrs         = []
    contador_label   = 0
    morse_usado      = False

    asm = []

    list_stmts_no = next((f for f in arvoreAtribuida.filhos if f.tipo == 'list_stmts'), None)
    if list_stmts_no:
        gerarListStmts(list_stmts_no, asm)

    finalizarAssembly(asm, arquivo)
    #print(f"[gerarAssembly] Assembly gerado em '{arquivo}'")
    return arquivo
