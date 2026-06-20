'''
Integrantes do grupo (ordem alfabética):
Beatriz Perotto Muniz - @beatrizperottomuniz

Nome do grupo no Canvas: RA3 6
'''
from decimal import Decimal, ROUND_HALF_EVEN
import math
import struct

def floatParaHex(valor):
    bytes_ = struct.pack('>d', valor)
    return bytes_.hex()


def exibirResultados(resultados: list) -> None:
    print("\n------ Resultados esperados ------")
    for i, valor in enumerate(resultados):
        print(f"Linha {i + 1} - em decimal : {formatar(valor)} ; e em hexadecimal : {floatParaHex(valor)}")
    print("-----------------------------------")

# para IEEE754 -> roundTiesToEven
def formatar(valor):
    if math.isclose(valor, round(valor)):
        return str(int(round(valor)))
    return str(
        Decimal(str(valor)).quantize(
            Decimal("1.0"),
            rounding=ROUND_HALF_EVEN
        )
    )