# Gramática Atribuída (Aumentada)

Gramática da Fase 2 aumentada com regras semânticas para a Fase 3.
Ações semânticas são escritas entre chaves `{ }` após cada produção,
seguindo a convenção do Dragon Book (Aho, Lam, Sethi, Ullman).

Letras minúsculas = não-terminais · MAIÚSCULAS = terminais · `↑` = atributo sintetizado · `↓` = atributo herdado.

---

## Atributos por não-terminal

| Não-terminal | Atributos sintetizados (↑) | Atributos herdados (↓) |
|---|---|---|
| `prog` | — | — |
| `list_stmts` | — | `contador↓` (resultados produzidos até agora), `tabela↓` |
| `list_item` | — | `contador↓`, `tabela↓` |
| `stmt` | `tipo↑` (expressões aritméticas/relacionais) ou julgamento `ok` (IF/FOR) | `contador↓`, `tabela↓` |
| `rpn` | `tipo↑` | `contador↓`, `tabela↓` |
| `num` | `tipo↑`, `val↑` | — |
| `num_tipo` | `tipo↑`, `val↑` | — |
| `rpn_tail_num` | `é_atrib↑`, `nome↑`, `tipo↑` | `num↓` (nó irmão), `contador↓`, `tabela↓` |
| `rpn_tail_stmt` | `é_atrib↑`, `nome↑`, `tipo↑` | `stmt↓` (nó irmão), `tabela↓`, `contador↓` |
| `op_stmt_num` | — | — |
| `op_stmt_stmt` | — | — |
| `op_bin` | `tipo_resultado↑` | — |
| `op_arit` | — | — |
| `op_rel` | — | — |

---

## Regras de produção com ações semânticas

```
prog ::= LPAREN KEYWORD_START RPAREN list_stmts EOF
         { list_stmts.contador↓ := 0
           list_stmts.tabela↓   := nova TabelaSimbolos() }


list_stmts ::= LPAREN list_item
               { list_item.contador↓ := list_stmts.contador↓
                 list_item.tabela↓   := list_stmts.tabela↓ }


list_item ::= KEYWORD_END RPAREN
              { -- fim do programa, nada a fazer -- }

           | rpn RPAREN list_stmts
             { rpn.contador↓        := list_item.contador↓
               rpn.tabela↓          := list_item.tabela↓
               list_stmts.contador↓ := list_item.contador↓ + 1   -- toda instrução (inclusive atribuições) produz resultado referenciável por RES
               list_stmts.tabela↓   := list_item.tabela↓
               -- Nota: (V MEM) mapeia para rpn ::= num rpn_tail_num com rpn_tail_num ::= ID.
               --       A ação semântica declarar() na produção rpn é o mecanismo de declaração de variável.
               --       (MEM) mapeia para rpn ::= ID, onde registrarUso() valida que MEM foi declarado. }


stmt ::= LPAREN rpn RPAREN
         { rpn.contador↓ := stmt.contador↓   -- herdado do contexto externo (necessário para RES dentro de stmt)
           rpn.tabela↓   := stmt.tabela↓
           stmt.tipo↑    := rpn.tipo↑ }


rpn ::= num rpn_tail_num
        { rpn_tail_num.num↓      := num
          rpn_tail_num.contador↓ := rpn.contador↓
          rpn_tail_num.tabela↓   := rpn.tabela↓
          se rpn_tail_num.é_atrib↑:
              tabela.declarar(rpn_tail_num.nome↑, rpn_tail_num.tipo↑, rpn_tail_num.linha↑)
          rpn.tipo↑ := rpn_tail_num.tipo↑ }

      | stmt rpn_tail_stmt
        { rpn_tail_stmt.stmt↓      := stmt
          rpn_tail_stmt.tabela↓    := rpn.tabela↓
          rpn_tail_stmt.contador↓  := rpn.contador↓
          se rpn_tail_stmt.é_atrib↑:
              tabela.declarar(rpn_tail_stmt.nome↑, rpn_tail_stmt.tipo↑, rpn_tail_stmt.linha↑)
          rpn.tipo↑ := rpn_tail_stmt.tipo↑ }

      | ID
        { tabela.registrarUso(ID.lexema, ID.linha)
          rpn.tipo↑ := tabela.buscar(ID.lexema).tipo
          -- erro semântico se ID não declarado -- }


num ::= NUM_INT
        { num.tipo↑ := 'int'
          num.val↑  := int(NUM_INT.lexema) }

      | NUM_FLOAT
        { num.tipo↑ := 'float'
          num.val↑  := float(NUM_FLOAT.lexema) }

      | MINUS num_tipo
        { num.tipo↑ := num_tipo.tipo↑
          num.val↑  := -num_tipo.val↑ }


num_tipo ::= NUM_INT
             { num_tipo.tipo↑ := 'int'
               num_tipo.val↑  := int(NUM_INT.lexema) }

           | NUM_FLOAT
             { num_tipo.tipo↑ := 'float'
               num_tipo.val↑  := float(NUM_FLOAT.lexema) }


rpn_tail_num ::= KEYWORD_RES
                 { n     := num↓.val↑
                   total := contador↓
                   -- validações estruturais em construirTabelaSimbolos:
                   se n < 0:              erro(); rpn_tail_num.tipo↑ := ⊥; retornar   -- [T-RESInvalido]
                   se n > total:          erro(); rpn_tail_num.tipo↑ := ⊥; retornar   -- [T-RESInvalido]
                   -- validação semântica em verificarTipos:
                   se n = 0:              erro(); rpn_tail_num.tipo↑ := ⊥; retornar   -- [T-RESZero]
                   se H[|H| - n] = None: erro(); rpn_tail_num.tipo↑ := ⊥; retornar   -- [T-RESControle]
                   rpn_tail_num.é_atrib↑ := False
                   rpn_tail_num.tipo↑    := H[|H| - n]   -- tipo resolvido estaticamente via histórico H,
                                                           -- acumulado durante a análise (não em tempo de execução) }

               | ID
                 { rpn_tail_num.é_atrib↑ := True
                   rpn_tail_num.nome↑     := ID.lexema
                   rpn_tail_num.linha↑    := ID.linha
                   rpn_tail_num.tipo↑     := num↓.tipo↑   -- tipo herdado do operando esquerdo (ex: em (5 X), X recebe 'int') }

               | num op_bin
                 { verificar_compatibilidade(num↓.tipo↑, num.tipo↑, op_bin)
                   rpn_tail_num.é_atrib↑ := False
                   rpn_tail_num.tipo↑    := inferir_tipo_bin(num↓.tipo↑, num.tipo↑, op_bin) }

               | stmt op_stmt_num
                 { se op_stmt_num = KEYWORD_FOR:
                       verificarFOR(num↓.tipo↑, num↓.val↑, linha)
                       rpn_tail_num.tipo↑ := ok   -- FOR tem julgamento de comando, não produz valor tipado
                   senão:
                       verificar_compatibilidade(num↓.tipo↑, stmt.tipo↑, op_stmt_num)
                       rpn_tail_num.tipo↑ := inferir_tipo_bin(num↓.tipo↑, stmt.tipo↑, op_stmt_num)
                   rpn_tail_num.é_atrib↑ := False }


rpn_tail_stmt ::= ID
                  { rpn_tail_stmt.é_atrib↑ := True
                    rpn_tail_stmt.nome↑     := ID.lexema
                    rpn_tail_stmt.linha↑    := ID.linha
                    rpn_tail_stmt.tipo↑     := stmt↓.tipo↑   -- tipo herdado do operando esquerdo (ex: em ((1 2 +) X), X recebe 'int')
                    -- erro semântico se stmt↓ tem julgamento ok (FOR/IF) ou tipo bool:
                    --   ok → "estrutura de controle não produz valor armazenável"
                    --   bool → "resultado relacional não pode ser armazenado em variável" }

                | num op_bin
                  { verificar_compatibilidade(stmt↓.tipo↑, num.tipo↑, op_bin)
                    rpn_tail_stmt.é_atrib↑ := False
                    rpn_tail_stmt.tipo↑    := inferir_tipo_bin(stmt↓.tipo↑, num.tipo↑, op_bin) }

                | stmt op_stmt_stmt
                  { stmt.contador↓ := rpn_tail_stmt.contador↓
                    se op_stmt_stmt = KEYWORD_IF:
                        verificarIF(stmt↓.tipo↑, linha)
                        rpn_tail_stmt.tipo↑ := ok   -- IF tem julgamento de comando, não produz valor tipado
                    senão:
                        verificar_compatibilidade(stmt↓.tipo↑, stmt.tipo↑, op_stmt_stmt)
                        rpn_tail_stmt.tipo↑ := inferir_tipo_bin(stmt↓.tipo↑, stmt.tipo↑, op_stmt_stmt)
                    rpn_tail_stmt.é_atrib↑ := False }


op_stmt_num ::= KEYWORD_FOR
              | op_arit
              | op_rel


op_stmt_stmt ::= KEYWORD_IF
               | op_arit
               | op_rel


op_bin  ::= op_arit | op_rel

op_arit ::= PLUS | MINUS | MULT | DIV | INT_DIV | MOD | POW

op_rel  ::= GT | LT | GTE | LTE | EQ | NEQ
```

---

## Regras de inferência de tipo

### Operadores aritméticos

| Operador | Operandos | Tipo resultado | Restrição |
|---|---|---|---|
| `+` `-` `*` | int, int | int | — |
| `+` `-` `*` | float, float | float | — |
| `+` `-` `*` | int, float ou float, int | ⊥ | tipos incompatíveis — sem promoção |
| `^` | int, int (exp > 0) | int | expoente sempre int positivo |
| `^` | float, int (exp > 0) | float | base pode ser int ou float |
| `^` | qualquer, float/bool | ⊥ | expoente deve ser int |
| `^` | bool, qualquer | ⊥ | base deve ser numérica |
| `\|` (divisão real) | int, int ou float, float | float | tipos devem ser iguais |
| `/` (divisão inteira) | int, int | int | ambos obrigatoriamente int |
| `%` (módulo) | int, int | int | ambos obrigatoriamente int |

### Operadores relacionais

| Operador | Operandos | Tipo resultado | Restrição |
|---|---|---|---|
| `>` `<` `>=` `<=` `==` `!=` | τ, τ com τ ∈ {int, float} | bool | tipos compatíveis |

### Estruturas de controle

| Estrutura | Tipo exigido no operando | Tipo exigido no corpo |
|---|---|---|
| `IF` | bool (resultado de op_rel) | qualquer |
| `FOR` | int positivo | qualquer |

---

## Funções semânticas auxiliares

```
verificar_compatibilidade(τ₁, τ₂, op):
    -- caso especial: operando com julgamento ok (IF/FOR) — não produz valor tipado
    se τ₁ = ok  ou  τ₂ = ok:
        erro()       -- [T-ControleOperandoErro] / [T-ControleOperandoDirErro]
        retornar ⊥
    se op = POW:
        -- POW é assimétrico: expoente deve ser int, base pode ser int ou float
        se τ₂ ≠ 'int':          erro()   -- [T-PowErroExp]
        se τ₁ ∉ {int, float}:   erro()   -- [T-PowErroBase]
        -- verificação de valor (e₂ > 0) é feita via val↑ na produção rpn_tail_num
    senão:
        se ¬(τ₁ = τ₂  ∧  τ₁ ∈ {int, float}):   erro()   -- [T-AritErro] / [T-DivErro]
        se op ∈ {INT_DIV, MOD}  e  τ₁ ≠ 'int':  erro()   -- [T-IntDivErro] / [T-ModErro]
        se op ∈ op_rel  e  τ₁ = 'bool':          erro()   -- [T-RelErro]

inferir_tipo_bin(τ₁, τ₂, op):
    se op = POW:       retornar τ₁     -- tipo da base (int ou float), expoente sempre int
    se τ₁ ≠ τ₂:       retornar ⊥     -- tipos incompatíveis, erro já reportado
    se op ∈ op_rel:    retornar 'bool'
    se op = DIV:       retornar 'float'
    retornar τ₁                        -- mesmo tipo nos dois lados
```

---

## Tratamento de comentários

Comentários iniciados por `*{` e encerrados por `}*` são descartados pelo **analisador léxico** antes da construção de tokens. Não há produção gramatical para comentários.

---

## Terminais

```
KEYWORD_RES   = RES
KEYWORD_START = START
KEYWORD_END   = END
KEYWORD_IF    = IF
KEYWORD_FOR   = FOR

ID        = variável em letras latinas maiúsculas (ex: X, CONTADOR, VAR)
NUM_INT   = literal inteiro (ex: 10)
NUM_FLOAT = literal real (ex: 3.14)

PLUS    = +       MINUS   = -       MULT  = *
DIV     = |       INT_DIV = /       MOD   = %       POW = ^

GT  = >    LT  = <    GTE = >=    LTE = <=    EQ = ==    NEQ = !=

LPAREN = (    RPAREN = )

EOF = fim do arquivo
```

_Gramática aumentada da Fase 3 — estende `gramatica.md` da Fase 2 com atributos e ações semânticas conforme Aho, Lam, Sethi, Ullman — "Compilers: Principles, Techniques, and Tools" (Dragon Book), Capítulo 5._
