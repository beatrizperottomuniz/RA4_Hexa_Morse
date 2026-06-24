# RA4
### Geração de código em hexa + Morse
**Instituição** : PUCPR - Pontifícia Universidade Católica do Paraná<br>
**Disciplina** : Linguagens Formais e Compiladores (Turma 9º U) - Engenharia de Computação (Noite) - 2026 / 1º Sem <br>
**Professor** : Frank Coelho de Alcantara/Valter Klein Junior <br>
**Aluna** : Beatriz Perotto Muniz [@beatrizperottomuniz](https://github.com/beatrizperottomuniz)<br>

---

## Descrição

Este projeto implementa um analisador semântico capaz de identificar tokens, fazer análise sintática e semântica, e gerar código assembly correspondente.

---

## Requisitos

Python 3.x instalado:
```
python3 --version
```

Matplotlib (para geração das árvores em PNG):
```
pip install matplotlib
```

---

## Como compilar 
Este projeto foi desenvolvido em Python, uma linguagem interpretada, portanto não há etapa de compilação explícita. <br>
A execução é feita diretamente pelo interpretador Python.<br>

---

## Como executar

```
python3 AnalisadorSemantico.py nome_do_arquivo.txt
```

O programa executa as três fases em sequência e exibe no terminal:
- Resultado da análise léxica
- Resultado da análise sintática
- Resultado da análise semântica
- Lista de erros encontrados (se houver)
- Caminhos dos arquivos de saída gerados

O assembly (`saida_assembly.s`) só é gerado se não houver nenhum erro léxico, sintático ou semântico.

_Obs: dependendo do sistema, `python3` pode ser substituído por `python`._

---

## Como testar

### Com os arquivos de teste fornecidos

```
python3 AnalisadorSemantico.py teste01.txt
python3 AnalisadorSemantico.py teste02.txt
python3 AnalisadorSemantico.py teste03.txt
```

Os arquivos `teste01_erros.txt`, `teste02_erros.txt` e `teste03_erros.txt` contêm erros intencionais (léxicos, sintáticos e semânticos) para validar o tratamento de erros.

Para usar o assembly gerado:
1. Abra o arquivo `saida_assembly.s` gerado
2. Copie o conteúdo e cole no simulador [Cpulator-ARMv7 DEC1-SOC(v16.1)](https://cpulator.01xz.net/?sys=arm-de1soc)
3. Clique em **Compile and Load** e aguarde "Compile succeeded" em Messages
4. Clique em **Continue** e verifique os resultados na JTAG UART
5. Opcional: em Settings mude Format para "Decimal signed" para visualizar os valores em tempo real
6. Opcional: use **Step Over** para executar instrução por instrução (resultados visíveis em `d0`)

### Com as funções de teste unitário

```
python3 teste_analisadorSintatico.py
python3 teste_construirTabelaSimbolos.py
python3 teste_end_to_end_fase3.py
python3 teste_gerarArvoreAtribuida.py
python3 teste_gerarAssemblyFase3.py
python3 teste_parsear.py
python3 teste_prepararEntradaSemantica.py
python3 teste_verificarTipos.py
```

---

## Como depurar

### Tokens gerados pelo léxico
O arquivo `saida_tokens_2.txt` contém todos os tokens reconhecidos em formato JSON, incluindo tipo, linha, coluna e índice na string pool.

### Árvore sintática
Gerada em quatro formatos após execução sem erros:
- `saida_arvore_json.txt` — JSON com string pool e `simbolo_id` por token
- `saida_arvore.txt` — texto com estrutura em árvore
- `saida_arvore.md` — Markdown
- `saida_arvore.png` — imagem

### Árvore sintática atribuída
Gerada após análise semântica sem erros, com anotações de tipo inferido e categoria semântica:
- `saida_arvore_atribuida.json` — JSON com string pool, `simbolo_id` e anotações semânticas
- `saida_arvore_atribuida.txt` — texto com tipos anotados
- `saida_arvore_atribuida.md` — Markdown
- `saida_arvore_atribuida.png` — imagem (nós com tipo anotado aparecem em verde)

### Tabela de símbolos
- `saida_tabela_simbolos.json` — JSON com todas as variáveis, seus tipos, linha de definição e linhas de uso
- `saida_tabela_simbolos.md` — Markdown formatado

### Erros semânticos
- `saida_erros_semanticos.md` — relatório com todos os erros semânticos encontrados (vazio se não houver)

### Erros léxicos e sintáticos
Impressos diretamente no terminal com número de linha e coluna.

---

## A linguagem

### Estrutura geral

Todo programa deve começar com `(START)` e terminar com `(END)`. As instruções ficam entre eles, uma por linha, sempre entre parênteses, em notação polonesa reversa: `(A B op)`.

### Comentários

Iniciados por `*{` e encerrados por `}*`. Podem aparecer em qualquer posição:

```
*{ comentário em linha própria }*
(4 2 +) *{ comentário no final da linha }*
(3 *{ comentário entre tokens }* 4 *)
```

### Operadores suportados

| Operador | Símbolo | Exemplo | Restrição de tipos |
|---|---|---|---|
| Adição | `+` | `(3 4 +)` | ambos `int` ou ambos `float` |
| Subtração | `-` | `(5 2 -)` | ambos `int` ou ambos `float` |
| Multiplicação | `*` | `(3 4 *)` | ambos `int` ou ambos `float` |
| Divisão real | `\|` | `(10 2 \|)` | ambos `int` ou ambos `float` — resultado sempre `float` |
| Divisão inteira | `/` | `(9 3 /)` | ambos `int` — resultado `int` |
| Módulo | `%` | `(10 3 %)` | ambos `int` — resultado `int` |
| Potenciação | `^` | `(2 3 ^)` | base `int` ou `float`, expoente obrigatoriamente `int` > 0 |

### Operadores relacionais

Produzem resultado do tipo `bool`. Ambos os operandos devem ser do mesmo tipo (`int` ou `float`).

| Operador | Símbolo | Exemplo |
|---|---|---|
| Igual | `==` | `(5 5 ==)` |
| Diferente | `!=` | `(3 4 !=)` |
| Maior | `>` | `(5 3 >)` |
| Menor | `<` | `(2 4 <)` |
| Maior ou igual | `>=` | `(5 5 >=)` |
| Menor ou igual | `<=` | `(3 5 <=)` |

### Comandos especiais

| Comando | Função | Exemplo |
|---|---|---|
| `(V MEM)` | Armazena o valor V na variável MEM | `(10 X)` |
| `(MEM)` | Lê o valor armazenado em MEM | `(X)` |
| `(N RES)` | Retorna o resultado de N instruções atrás | `(1 RES)` |

`MEM` pode ser qualquer sequência de letras latinas maiúsculas que não seja uma palavra reservada (`START`, `END`, `IF`, `FOR`, `RES`, `MORSE`).

### Estruturas de controle

**Decisão — IF**
```
(cond body IF)
```
Executa `body` se `cond` for verdadeiro. `cond` deve ser obrigatoriamente uma expressão relacional (tipo `bool`).

Exemplo: `((5 5 ==) (1 2 +) IF)`

**Repetição — FOR**
```
(N body FOR)
```
Repete `body` exatamente N vezes. N deve ser um número inteiro maior que zero.

Exemplo: `(3 (1 2 +) FOR)`

**Morse — MORSE**
```
("texto" MORSE)
```
Exibe a string em código Morse via LED no simulador CPUlator. A string é convertida para maiúsculas antes da exibição — `"Abc"` equivale a `"ABC"`. Apenas letras (`A–Z`) e dígitos (`0–9`) são suportados; qualquer outro caractere resulta em erro semântico. Não produz valor — não pode ser atribuído a variável nem usado como operando.

Exemplo: `("SOS" MORSE)`

---

## Sistema de tipos

A linguagem possui tipagem **estática e forte**. O tipo de cada variável é determinado no momento da primeira atribuição e não pode ser alterado.

### Tipos suportados

| Tipo | Origem |
|---|---|
| `int` | literal inteiro (`3`, `10`, `-5`) |
| `float` | literal real (`3.0`, `1.5`, `-2.7`) |
| `bool` | exclusivamente inferido de operadores relacionais (`==`, `!=`, `<`, `>`, `<=`, `>=`) |
| `string` | literal textual entre aspas duplas (`"OLA"`, `"SOS"`) — aceito exclusivamente como operando de `MORSE` |

**Não existem literais booleanos na linguagem.** Não há `true` nem `false`. O tipo `bool` só existe como resultado de uma expressão relacional — por isso os arquivos de teste não contêm literais lógicos.

### Regras de compatibilidade

- Operações aritméticas exigem operandos do **mesmo tipo**. `int + float` é erro semântico — não há promoção implícita.
- Divisão real `|` aceita `int|int` ou `float|float`, mas o resultado é sempre `float`.
- Divisão inteira `/` e módulo `%` exigem ambos os operandos `int`.
- Potenciação `^` exige expoente `int` > 0. A base pode ser `int` ou `float`.
- Operadores relacionais exigem operandos do mesmo tipo (`int` ou `float`). `bool` não pode ser operando relacional.

### Regras de variáveis

- Toda variável deve ser **declarada antes de ser usada**: `(V MEM)` declara e inicializa.
- O tipo é inferido do valor atribuído na primeira declaração.
- Reatribuição com **mesmo tipo** é válida.
- Reatribuição com **tipo diferente** é erro semântico.
- Armazenar resultado `bool` em variável é erro semântico.

### Regras do RES

- `(N RES)` referencia o resultado de N instruções anteriores (N ≥ 1).
- IF e FOR não produzem resultado com valor real — se `(N RES)` referenciar um IF/FOR, é erro semântico.
- `(0 RES)` é erro semântico — referência à instrução corrente, ainda não disponível.

---

## Exemplos

### Programa válido

```
*{ operacoes aritmeticas e variaveis }*
(START)
(4 2 +)
(3.0 2.0 *)
(10 A)
(3.0 B)
((A) 4 +)
((B) 1.0 +)
(1 RES)
((5 5 ==) (2 3 +) IF)
(3 (1 2 +) FOR)
(END)
```

### Programa com erro semântico — tipo incompatível

```
(START)
(3 2.0 +)
(END)
```
Erro: operador `+` requer operandos do mesmo tipo, recebeu `int` e `float`.

### Programa com erro semântico — variável não declarada

```
(START)
(NAOEXISTE)
(END)
```
Erro: variável `NAOEXISTE` usada antes de ser definida.

### Programa com erro semântico — condição de IF não é bool

```
(START)
((3 5 +) (1 2 +) IF)
(END)
```
Erro: condição do IF deve ser `bool`, recebeu `int`.

### Programa com erro semântico — expoente não inteiro

```
(START)
(2 3.0 ^)
(END)
```
Erro: expoente em `^` deve ser `int`, recebeu `float`.

### Programa válido com MORSE

```
(START)
("SOS" MORSE)
("Ola" MORSE)
(END)
```
Exibe `SOS` e `OLA` em código Morse via LED. Letras minúsculas são convertidas automaticamente.

### Programa com erro semântico — caractere inválido em MORSE

```
(START)
("OLÁ" MORSE)
(END)
```
Erro: MORSE não suporta os caracteres: `['Á']`.

---

## Tabela de Símbolos

A tabela de símbolos é construída pelo módulo `construirTabelaSimbolos.py` durante a análise semântica. Ela registra todas as variáveis declaradas no programa e é usada por `verificarTipos.py` para validar os tipos das expressões.

Cada entrada na tabela contém:

| Campo | Descrição |
|---|---|
| `nome` | Nome da variável (ex: `X`, `CONTADOR`) |
| `tipo` | Tipo inferido no momento da declaração: `'int'`, `'float'` ou `'bool'` |
| `linha_def` | Número da linha onde a variável foi declarada com `(V MEM)` |
| `linhas_uso` | Lista de linhas onde a variável foi lida com `(MEM)` ou reatribuída |

Regras relevantes:
- Uma variável só pode ser usada após ter sido declarada — uso antes da declaração gera erro semântico.
- O tipo é fixado na declaração e não pode ser alterado — reatribuição com tipo diferente gera erro semântico.
- Reatribuição com mesmo tipo é válida e registra a linha como uso.

A tabela é salva em `saida_tabela_simbolos.json` (formato JSON) e `saida_tabela_simbolos.md` (formato Markdown).

---

## Árvore Sintática Atribuída

A árvore sintática atribuída é a árvore sintática da Fase 2 enriquecida com informações semânticas. É gerada por `gerarArvoreAtribuida.py` apenas quando não há erros léxicos, sintáticos ou semânticos.

Cada nó relevante da árvore contém, além dos campos da Fase 2 (`tipo`, `token`, `filhos`), os seguintes campos adicionais:

| Campo | Descrição |
|---|---|
| `tipo_inferido` | Tipo semântico do resultado do nó|
| `categoria_semantica` | Categoria do nó: `'expressao_aritmetica'`, `'expressao_relacional'`, `'atribuicao'`, `'leitura'`, `'recuperacao_resultado'`, `'decisao'`, `'repeticao'`, `'morse'`, `'subexpressao'` |
| `simbolo` | Lexema do token (ex: `"+"`, `"3.14"`, `"X"`) para nós terminais relevantes |

O campo `tipo_inferido` é o principal artefato semântico: permite rastrear o tipo de cada subexpressão e justifica a geração do código Assembly correspondente.

A árvore atribuída é salva em:
- `saida_arvore_atribuida.json` — formato JSON com `string_pool` e nós anotados
- `saida_arvore_atribuida.txt` — representação em texto indentado
- `saida_arvore_atribuida.md` — representação em Markdown
- `saida_arvore_atribuida.png` — visualização gráfica (requer `matplotlib`)

---

## Arquivos de saída

| Arquivo | Conteúdo |
|---|---|
| `saida_tokens_2.txt` | tokens reconhecidos pelo léxico em JSON |
| `saida_arvore_json.txt` | árvore sintática em JSON (com string pool) |
| `saida_arvore.txt` | árvore sintática em texto |
| `saida_arvore.md` | árvore sintática em Markdown |
| `saida_arvore.png` | árvore sintática em imagem |
| `saida_tabela_simbolos.json` | tabela de símbolos em JSON |
| `saida_tabela_simbolos.md` | tabela de símbolos em Markdown |
| `saida_erros_semanticos.md` | relatório de erros semânticos |
| `saida_arvore_atribuida.json` | árvore atribuída em JSON (com tipos e categorias) |
| `saida_arvore_atribuida.txt` | árvore atribuída em texto |
| `saida_arvore_atribuida.md` | árvore atribuída em Markdown |
| `saida_arvore_atribuida.png` | árvore atribuída em imagem |
| `saida_assembly.s` | código Assembly para Cpulator-ARMv7 |

**Os artefatos presentes no repositório foram gerados a partir do arquivo `teste03.txt`.**

---

## Observações

1. O tipo `bool` não possui literal na linguagem — ele é exclusivamente o resultado de operadores relacionais. Portanto, não há literais booleanos nos arquivos de teste: isso é correto e esperado.
2. A linguagem usa tipagem forte sem promoção implícita: `int + float` é sempre erro semântico.
3. `|` é divisão real (resultado sempre `float`); `/` é divisão inteira (ambos os operandos devem ser `int`).
4. O analisador continua para as fases seguintes mesmo após encontrar erros, a fim de reportar todos os problemas de uma só vez. O assembly só é gerado quando não há nenhum erro nas três fases.
5. O terminal exibe os valores esperados de cada linha como referência para validação do assembly. Os cálculos efetivos são realizados pelo assembly no Cpulator — o Python serve apenas como simulação de verificação.