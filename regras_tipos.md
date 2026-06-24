# Regras de Tipos em Cálculo de Sequentes

Sistema de tipos da linguagem RPN implementada nas Fases 1–3.
Notação: `Γ ⊢ e : τ` significa "no ambiente de tipos Γ, a expressão e tem tipo τ".

- `Γ` — ambiente de tipos
- `τ` — tipo: `int` | `float` | `bool`
- `⊥` — expressão sem tipo definido (bottom)
- `⊕` — operador aritmético genérico
- `⊗` — operador relacional genérico

---

## 1. Literais

```
──────────────────────── [T-Int]
Γ ⊢ NUM_INT : int


──────────────────────── [T-Float]
Γ ⊢ NUM_FLOAT : float


──────────────────────── [T-String]
Γ ⊢ "s" : string
```

O tipo `string` é exclusivo de literais entre aspas duplas. Não pode ser atribuído a variáveis nem usado como operando em operações aritméticas ou relacionais.
Não existem literais lógicos na linguagem. O tipo `bool` é exclusivamente inferido a partir de expressões relacionais (ver Seção 4).

---

## 2. Negação numérica

```
Γ ⊢ n : int
──────────────────────── [T-NegInt]
Γ ⊢ (- n) : int


Γ ⊢ n : float
──────────────────────── [T-NegFloat]
Γ ⊢ (- n) : float
```

---

## 3. Variáveis

### 3.1 Declaração — comando `(V MEM)`

```
Γ ⊢ v : τ    τ ∈ {int, float}
──────────────────────────────── [T-Assign]
Γ, x : τ ⊢ (v x) : τ
```

Uma variável `x` é declarada com o tipo do valor `v` que lhe é atribuído.
Após a declaração, `x : τ` é adicionado ao ambiente Γ.
Somente valores numéricos (`int` ou `float`) podem ser armazenados — vide enunciado: *"(V MEM): Armazena o valor real V"*. Armazenar resultado de expressão relacional (tipo `bool`) é erro semântico.

```
Γ ⊢ v : bool
──────────────────────────────── [T-AssignBoolErro]
Γ ⊢ (v x) : ⊥
```

### 3.2 Redeclaração com mesmo tipo

```
Γ(x) = τ    Γ ⊢ v : τ    τ ∈ {int, float}
──────────────────────────────────────────── [T-Reassign]
Γ ⊢ (v x) : τ
```

Reatribuição com o mesmo tipo é válida. O tipo de `x` em Γ não se altera.

### 3.3 Redeclaração com tipo diferente — erro semântico

```
Γ(x) = τ₁    Γ ⊢ v : τ₂    τ₁ ≠ τ₂
──────────────────────────────────────── [T-TypeMismatch]
Γ ⊢ (v x) : ⊥
```

### 3.4 Leitura — comando `(MEM)`

```
Γ(x) = τ
──────────────────────── [T-Read]
Γ ⊢ (x) : τ
```

### 3.5 Uso antes da declaração — erro semântico

```
x ∉ dom(Γ)
──────────────────────── [T-Undeclared]
Γ ⊢ (x) : ⊥
```

---

## 4. Operadores aritméticos

`⊕ ∈ { +, -, * }`

```
Γ ⊢ e₁ : int    Γ ⊢ e₂ : int
──────────────────────────────── [T-AritInt]
Γ ⊢ (e₁ e₂ ⊕) : int


Γ ⊢ e₁ : float    Γ ⊢ e₂ : float
──────────────────────────────────── [T-AritFloat]
Γ ⊢ (e₁ e₂ ⊕) : float
```

A linguagem usa tipagem estática e forte — operações mistas entre `int` e `float` resultam em erro semântico. Não temos promoção implícita.

```
Γ ⊢ e₁ : τ₁    Γ ⊢ e₂ : τ₂    ¬(τ₁ = τ₂  ∧  τ₁ ∈{int, float})
────────────────────────────────────────────────────────────────── [T-AritErro]
Γ ⊢ (e₁ e₂ ⊕) : ⊥
```

### 4.1 Divisão real `|`

```
Γ ⊢ e₁ : τ    Γ ⊢ e₂ : τ    τ ∈ {int, float}
────────────────────────────────────────────── [T-Div]
Γ ⊢ (e₁ e₂ |) : float
```

Ambos os operandos devem ter o mesmo tipo (`int` ou `float`). Sempre retorna `float`. Ex : 5 | 2 = 2.5
Tipos diferentes ou não numéricos resultam em erro semântico:

```
Γ ⊢ e₁ : τ₁    Γ ⊢ e₂ : τ₂    ¬(τ₁ = τ₂  ∧  τ₁ ∈{int, float})
────────────────────────────────────────────────────────────────── [T-DivErro]
Γ ⊢ (e₁ e₂ |) : ⊥
```

### 4.2 Divisão inteira `/`

```
Γ ⊢ e₁ : int    Γ ⊢ e₂ : int
──────────────────────────────── [T-IntDiv]
Γ ⊢ (e₁ e₂ /) : int
```

Operandos não inteiros resultam em erro semântico:

```
Γ ⊢ e₁ : τ₁    Γ ⊢ e₂ : τ₂    (τ₁ ≠ int ∨ τ₂ ≠ int)
──────────────────────────────────────────────────────── [T-IntDivErro]
Γ ⊢ (e₁ e₂ /) : ⊥
```

### 4.3 Módulo `%`

```
Γ ⊢ e₁ : int    Γ ⊢ e₂ : int
──────────────────────────────── [T-Mod]
Γ ⊢ (e₁ e₂ %) : int
```

Operandos não inteiros resultam em erro semântico:

```
Γ ⊢ e₁ : τ₁    Γ ⊢ e₂ : τ₂    (τ₁ ≠ int ∨ τ₂ ≠ int)
──────────────────────────────────────────────────────── [T-ModErro]
Γ ⊢ (e₁ e₂ %) : ⊥
```

### 4.4 Potenciação `^`

`^` é assimétrico: o expoente é sempre restrito a `int`, mas a base pode ser `int` ou `float`.

```
Γ ⊢ e₁ : int    Γ ⊢ e₂ : int    e₂ > 0
─────────────────────────────────────────── [T-PowInt]
Γ ⊢ (e₁ e₂ ^) : int


Γ ⊢ e₁ : float    Γ ⊢ e₂ : int    e₂ > 0
──────────────────────────────────────────── [T-PowFloat]
Γ ⊢ (e₁ e₂ ^) : float
```

Expoente não inteiro, não positivo, ou base não numérica resultam em erro semântico:

```
Γ ⊢ e₂ : τ    (τ ≠ int ∨ e₂ ≤ 0)
──────────────────────────────────── [T-PowErroExp]
Γ ⊢ (e₁ e₂ ^) : ⊥


Γ ⊢ e₁ : τ    τ ∉ {int, float}
──────────────────────────────── [T-PowErroBase]
Γ ⊢ (e₁ e₂ ^) : ⊥
```

---

## 5. Operadores relacionais

`⊗ ∈ { >, <, >=, <=, ==, != }`

```
Γ ⊢ e₁ : τ    Γ ⊢ e₂ : τ    τ ∈ {int, float}
──────────────────────────────────────────────── [T-Rel]
Γ ⊢ (e₁ e₂ ⊗) : bool
```

Operandos devem ter o mesmo tipo numérico. Operandos com tipo `bool` ou de tipos diferentes não são permitidos:

```
Γ ⊢ e₁ : τ₁    Γ ⊢ e₂ : τ₂    (τ₁ ≠ τ₂ ∨ τ₁ = bool ∨ τ₂ = bool)
──────────────────────────────────────────────────────────────────── [T-RelErro]
Γ ⊢ (e₁ e₂ ⊗) : ⊥
```

---

## 6. Estruturas de controle

Estruturas de controle usam o julgamento `Γ ⊢ s ok` — indicam que `s` é um comando que **não produz valor**. Este julgamento é distinto de `Γ ⊢ e : τ`, que se aplica a expressões com tipo. Como IF e FOR possuem apenas julgamento de comando (`ok`) e não julgamento de expressão (`: τ`), não podem ser atribuídos a variáveis.

### 6.1 Decisão — `IF`

```
Γ ⊢ cond : bool    Γ ⊢ corpo ok
──────────────────────────────────── [T-IF]
Γ ⊢ (cond corpo IF) ok
```

A condição deve ter tipo `bool` (resultado de um operador relacional).
Condição com tipo diferente de `bool` resulta em erro semântico:

```
Γ ⊢ cond : τ    τ ≠ bool
──────────────────────────── [T-IFErro]
Γ ⊢ (cond corpo IF) : ⊥
```

Armazenar o resultado de IF em variável é erro semântico — IF possui apenas julgamento de comando (`ok`), não de expressão (`: τ`):

```
Γ ⊢ (cond corpo IF) ok
────────────────────────────────────── [T-IFAssignErro]
Γ ⊢ ((cond corpo IF) x) : ⊥
```

### 6.2 Repetição — `FOR`

```
Γ ⊢ n : int    n > 0    Γ ⊢ corpo ok
──────────────────────────────────────── [T-FOR]
Γ ⊢ (n corpo FOR) ok
```

O contador deve ser um literal inteiro positivo.
Contador não inteiro ou não positivo resulta em erro semântico:

```
Γ ⊢ n : τ    (τ ≠ int ∨ n ≤ 0)
──────────────────────────────── [T-FORErro]
Γ ⊢ (n corpo FOR) : ⊥
```

Armazenar o resultado de FOR em variável é erro semântico — FOR possui apenas julgamento de comando (`ok`), não de expressão (`: τ`):

```
Γ ⊢ (n corpo FOR) ok
────────────────────────────────────── [T-FORAssignErro]
Γ ⊢ ((n corpo FOR) x) : ⊥
```

Usar o resultado de IF ou FOR como operando em operação aritmética ou relacional também é erro semântico — um comando `ok` não possui valor tipado para operar:

```
Γ ⊢ s ok    op ∈ {⊕, ⊗}
──────────────────────────────────────────── [T-ControleOperandoErro]
Γ ⊢ (s e op) : ⊥


Γ ⊢ s ok    op ∈ {⊕, ⊗}
──────────────────────────────────────────── [T-ControleOperandoDirErro]
Γ ⊢ (e s op) : ⊥
```

---

## 7. Instrução MORSE

### 7.1 Instrução `("s" MORSE)`

```
Γ ⊢ "s" : string    ∀c ∈ upper("s") : c ∈ {A–Z, 0–9, ' '}
──────────────────────────────────────────────────────── [T-MORSE]
Γ ⊢ ("s" MORSE) ok
```

A instrução MORSE exibe a string em código Morse via LED no simulador. Retorna julgamento de comando (`ok`), sem valor tipado — igual a IF e FOR.

Caractere fora do conjunto `{A–Z, 0–9, ' '}` após `upper` resulta em erro semântico:

```
Γ ⊢ "s" : string    ∃c ∈ upper("s") : c ∉ {A–Z, 0–9, ' '}
──────────────────────────────────────────────────────── [T-MORSECaractereErro]
Γ ⊢ ("s" MORSE) : ⊥
```

### 7.2 MORSE não aceita não-string

```
Γ ⊢ e : τ    τ ≠ string
──────────────────────────── [T-MORSETipoErro]
Γ ⊢ (e MORSE) : ⊥
```

### 7.3 MORSE não produz valor

Armazenar o resultado de MORSE em variável é erro semântico — MORSE possui apenas julgamento de comando (`ok`), não de expressão (`: τ`):

```
Γ ⊢ ("s" MORSE) ok
────────────────────────────────────── [T-MORSEAssignErro]
Γ ⊢ (("s" MORSE) x) : ⊥
```

Usar o resultado de MORSE como operando em operação aritmética ou relacional é coberto pela regra geral `T-ControleOperandoErro` (Seção 6), que se aplica a qualquer julgamento `ok`.

---

## 8. Comando especial RES

```
n > 0    n ≤ |H|    H[|H| - n] = τ
──────────────────────────────────────────────── [T-RES]
Γ, H ⊢ (n RES) : τ


n > 0    n ≤ |H|    H[|H| - n] = None
──────────────────────────────────────────────── [T-RESControle]
Γ, H ⊢ (n RES) : ⊥


n = 0
──────────────────────────────────────────────── [T-RESZero]
Γ, H ⊢ (0 RES) : ⊥


n < 0  ∨  n > |H|
──────────────────────────────────────────────── [T-RESInvalido]
Γ, H ⊢ (n RES) : ⊥
```

`H` é o histórico de tipos dos resultados produzidos até o ponto atual (lista acumulada durante a análise). `H[|H| - n]` recupera o tipo da instrução `n` posições atrás. O analisador semântico percorre o programa de cima para baixo, acumulando o tipo de cada instrução em `H`, e resolve o tipo de `(n RES)` durante a própria análise — sem necessidade de execução.

**Sobre `n = 0`:** o enunciado define N como "inteiro não negativo", portanto `n = 0` é sintaticamente permitido e não é rejeitado pela tabela de símbolos. Porém é semanticamente impossível: `(0 RES)` referenciaria o resultado da própria linha ainda em processamento, que não existe em `H`. O `verificarTipos` detecta esse caso e emite erro explícito — [T-RESZero].

**Sobre `H[|H| - n] = None`:** linhas de IF e FOR têm julgamento de comando (`ok`) e não produzem valor tipado. Na implementação, `None` em `H` representa esse julgamento. Referenciar tal linha via RES é erro semântico — [T-RESControle].

A validação de `n < 0` e `n > |H|` — [T-RESInvalido] — é feita em `construirTabelaSimbolos`. A validação de `n = 0` — [T-RESZero] — e `H[idx] = None` — [T-RESControle] — é feita em `verificarTipos`.

---

## 9. Resumo das combinações de tipos

### Operadores aritméticos `+` `-` `*`

| τ(e₁) | τ(e₂) | τ(resultado) | Regra |
|---|---|---|---|
| int | int | int | T-AritInt |
| float | float | float | T-AritFloat |
| int | float | ⊥ | T-AritErro |
| float | int | ⊥ | T-AritErro |
| bool | qualquer | ⊥ | T-AritErro |
| qualquer | bool | ⊥ | T-AritErro |

### Potenciação `^`

| τ(base e₁) | τ(exp e₂) | e₂ > 0 | τ(resultado) | Regra |
|---|---|---|---|---|
| int | int | sim | int | T-PowInt |
| float | int | sim | float | T-PowFloat |
| qualquer | int | não | ⊥ | T-PowErroExp |
| qualquer | float/bool | — | ⊥ | T-PowErroExp |
| bool | qualquer | — | ⊥ | T-PowErroBase |

### Operadores `/` e `%`

| τ(e₁) | τ(e₂) | τ(resultado) | Regra |
|---|---|---|---|
| int | int | int | T-IntDiv / T-Mod |
| qualquer outro | qualquer | ⊥ | T-IntDivErro / T-ModErro |

### Operador `|` (divisão real)

| τ(e₁) | τ(e₂) | τ(resultado) | Regra |
|---|---|---|---|
| int | int | float | T-Div |
| float | float | float | T-Div |
| int | float | ⊥ | T-DivErro |
| float | int | ⊥ | T-DivErro |
| bool | qualquer | ⊥ | T-DivErro |
| qualquer | bool | ⊥ | T-DivErro |

### Operadores relacionais `>` `<` `>=` `<=` `==` `!=`

| τ(e₁) | τ(e₂) | τ(resultado) | Regra |
|---|---|---|---|
| int | int | bool | T-Rel |
| float | float | bool | T-Rel |
| int | float | ⊥ | T-RelErro |
| float | int | ⊥ | T-RelErro |
| bool | qualquer | ⊥ | T-RelErro |
| qualquer | bool | ⊥ | T-RelErro |

---

## 10. Nota de implementação — `null` na tabela de símbolos

Os tipos da linguagem são exclusivamente `int`, `float` e `bool`. O valor `null` (Python `None`) **não é um tipo da linguagem** — é um marcador de implementação que aparece na tabela de símbolos apenas quando uma declaração é semanticamente inválida segundo T-IFAssignErro ou T-FORAssignErro.

Nesses casos, a variável é registrada com `tipo: null` para evitar erros falsos em cascata do tipo "usada antes de ser definida" — a variável existe no escopo, mas não possui tipo válido. O erro semântico correspondente é sempre reportado por `verificarTipos`.

Variáveis com `tipo: null` na tabela indicam declarações inválidas e nunca chegam à geração de assembly.
