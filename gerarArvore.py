'''
Integrantes do grupo (ordem alfabética):
Beatriz Perotto Muniz - @beatrizperottomuniz

Nome do grupo no Canvas: RA3 6
'''
import json
from globalVars import string_pool_global

arqv_json = "saida_arvore_json.txt"
arqv_txt  = "saida_arvore.txt"
arqv_png  = "saida_arvore.png"
arqv_md = "saida_arvore.md"

# no arvore
class NoArvore:
    def __init__(self, tipo, token=None):
        self.tipo = tipo
        self.token = token # se terminal
        self.filhos = [] # no arvore

    def adicionar_filho(self, filho):
        self.filhos.append(filho)

    def __repr__(self):
        if self.token:
            return f"[{self.tipo} L{self.token.linha}:{self.token.coluna}]"
        return f"[{self.tipo}]"


def gerarArvore(derivacao):
    if not derivacao:
        return None

    raiz = NoArvore('prog')
    pendentes = [raiz]

    for passo in derivacao:
        if not pendentes:
            break

        tipo = passo['tipo']

        if tipo == 'expansao':
            no = pendentes.pop()
            filhos = []
            for simbolo in passo['producao']:
                filho = NoArvore(simbolo)
                no.adicionar_filho(filho)
                filhos.append(filho)
            for filho in reversed(filhos):
                pendentes.append(filho)

        elif tipo == 'match':
            no = pendentes.pop()
            no.token = passo['token']
        # pra se precisar na proxima fase
        elif tipo == 'epsilon':
            no = pendentes.pop()
            no.adicionar_filho(NoArvore('ε'))

    # doc
    salvarArvoreJSON(raiz)
    salvarArvoreTXT(raiz)
    gerarArvorePNG(raiz)
    salvarArvoreMD(raiz)
    return raiz

# json

def noParaDict(no):
    resultado = {
        'tipo': no.tipo,
        'token': None,
        'filhos': [noParaDict(f) for f in no.filhos]
    }
    if no.token:
        resultado['token'] = {
            'tipo': no.token.tipo,
            'linha': no.token.linha,
            'coluna': no.token.coluna,
            'simbolo_id': no.token.simbolo_id
        }
    return resultado

def salvarArvoreJSON(raiz, arquivo=arqv_json):
    dados = {                                                                                       
          "string_pool": string_pool_global.strings,                                                  
          "arvore": noParaDict(raiz)                                                               
      }                                                                                             
    with open(arquivo, 'w', encoding='utf-8') as f:                                                 
        json.dump(dados, f, ensure_ascii=False, indent=4)

# txt

def linhasArvores(no, prefixo, ultimo, linhas):
    conector = '└── ' if ultimo else '├── '
    label    = no.tipo
    if no.token:
        label += f'  [L{no.token.linha}:{no.token.coluna}]'
    linhas.append(prefixo + conector + label)

    extensao = '    ' if ultimo else '│   '
    for i, filho in enumerate(no.filhos):
        linhasArvores(filho, prefixo + extensao, i == len(no.filhos) - 1, linhas)

def salvarArvoreTXT(raiz, arquivo=arqv_txt):
    linhas = [raiz.tipo]   # raiz sem conector
    for i, filho in enumerate(raiz.filhos):
        linhasArvores(filho, '', i == len(raiz.filhos) - 1, linhas)

    texto = '\n'.join(linhas)
    #print(texto)
    with open(arquivo, 'w', encoding='utf-8') as f:
        f.write(texto)

# MD 

def linhasMD(no, nivel, linhas):
    indent = "  " * nivel
    label = f"`{no.tipo}`"
    if no.token:
        label += f" `[L{no.token.linha}:{no.token.coluna}]`"
    linhas.append(f"{indent}- {label}")
    for filho in no.filhos:
        linhasMD(filho, nivel + 1, linhas)

def salvarArvoreMD(raiz, arquivo=arqv_md):
    linhas = ["# Árvore sintática\n"]
    linhasMD(raiz, 0, linhas)
    texto = '\n'.join(linhas)
    with open(arquivo, 'w', encoding='utf-8') as f:
        f.write(texto)

# png

def calcularPos(no, profundidade, posicoes, contador_folha):
    if not no.filhos:
        x = contador_folha[0]
        contador_folha[0] += 1
    else:
        for filho in no.filhos:
            calcularPos(filho, profundidade + 1, posicoes, contador_folha)
        xs = [posicoes[id(f)][0] for f in no.filhos]
        x  = (xs[0] + xs[-1]) / 2
    posicoes[id(no)] = (x, profundidade)

def desenhar(no, posicoes, ax, BOX_W, BOX_H):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.patches as mpatches
    except ImportError:
        return
    
    x, y = posicoes[id(no)]
    y_plot = -y

    label = no.tipo
    if no.token:                                                                                      
        if no.token.tipo in ('NUM_INT', 'NUM_FLOAT', 'ID'):
            lexema = string_pool_global.obterString(no.token.simbolo_id)
            if lexema and lexema != "desconhecido":                                                     
                label += f'\n"{lexema}"'
        label += f'\nL{no.token.linha}:{no.token.coluna}'   
        
    cor = "#f6dafb" if (not no.token and no.tipo != 'ε') else "#dfcdfa"

    caixa = mpatches.FancyBboxPatch(
        (x - BOX_W / 2, y_plot - BOX_H / 2), BOX_W, BOX_H,
        boxstyle="round,pad=0.05", linewidth=0.8,
        edgecolor='#555555', facecolor=cor
    )
    ax.add_patch(caixa)
    ax.text(x, y_plot, label, ha='center', va='center',
            fontsize=7, fontfamily='monospace')

    for filho in no.filhos:
        fx, fy = posicoes[id(filho)]
        fy_plot = -fy
        ax.plot([x, fx], [y_plot - BOX_H / 2, fy_plot + BOX_H / 2],
                color="#555555", linewidth=0.7, zorder=0)
        desenhar(filho, posicoes, ax, BOX_W, BOX_H)

def gerarArvorePNG(raiz, arquivo=arqv_png):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print("[aviso] matplotlib não instalado —> PNG não gerado "
              "Execute: pip install matplotlib")
        return

    posicoes = {}          # no -> (x, y)
    contador_folha = [0]

    calcularPos(raiz, 0, posicoes, contador_folha)

    total_folhas = contador_folha[0]
    max_prof     = max(y for x, y in posicoes.values()) if posicoes else 1

    # desenho
    larg  = max(10, total_folhas * 1.4)
    alt   = max(6,  (max_prof + 1) * 1.6)
    fig, ax = plt.subplots(figsize=(larg, alt))
    ax.set_xlim(-1, total_folhas)
    ax.set_ylim(-(max_prof + 0.8), 0.8)
    ax.axis('off')
    ax.set_title('Árvore sintática LL(1)', fontsize=11, pad=10)

    BOX_W, BOX_H = 0.9, 0.45

    desenhar(raiz, posicoes, ax, BOX_W, BOX_H)

    nome_arquivo = arquivo
    plt.tight_layout()
    plt.savefig(nome_arquivo, dpi=150, bbox_inches='tight')
    plt.close()
