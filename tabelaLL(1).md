# Tabela LL(1)

| Não-terminal | DIV | EQ | GT | GTE | ID | INT_DIV | KEYWORD_END | KEYWORD_FOR | KEYWORD_IF | KEYWORD_RES | LPAREN | LT | LTE | MINUS | MOD | MULT | NEQ | NUM_FLOAT | NUM_INT | PLUS | POW | STRING |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **list_item** | | | | | list_item → rpn RPAREN list_stmts | | list_item → KEYWORD_END RPAREN | | | | list_item → rpn RPAREN list_stmts | | | list_item → rpn RPAREN list_stmts | | | | list_item → rpn RPAREN list_stmts | list_item → rpn RPAREN list_stmts | | | list_item → rpn RPAREN list_stmts |
| **list_stmts** | | | | | | | | | | | list_stmts → LPAREN list_item | | | | | | | | | | | |
| **num** | | | | | | | | | | | | | | num → MINUS num_tipo | | | | num → NUM_FLOAT | num → NUM_INT | | | |
| **num_tipo** | | | | | | | | | | | | | | | | | | num_tipo → NUM_FLOAT | num_tipo → NUM_INT | | | |
| **op_arit** | op_arit → DIV | | | | | op_arit → INT_DIV | | | | | | | | op_arit → MINUS | op_arit → MOD | op_arit → MULT | | | | op_arit → PLUS | op_arit → POW | |
| **op_bin** | op_bin → op_arit | op_bin → op_rel | op_bin → op_rel | op_bin → op_rel | | op_bin → op_arit | | | | | | op_bin → op_rel | op_bin → op_rel | op_bin → op_arit | op_bin → op_arit | op_bin → op_arit | op_bin → op_rel | | | op_bin → op_arit | op_bin → op_arit | |
| **op_rel** | | op_rel → EQ | op_rel → GT | op_rel → GTE | | | | | | | | op_rel → LT | op_rel → LTE | | | | op_rel → NEQ | | | | | |
| **op_stmt_num** | op_stmt_num → op_arit | op_stmt_num → op_rel | op_stmt_num → op_rel | op_stmt_num → op_rel | | op_stmt_num → op_arit | | op_stmt_num → KEYWORD_FOR | | | | op_stmt_num → op_rel | op_stmt_num → op_rel | op_stmt_num → op_arit | op_stmt_num → op_arit | op_stmt_num → op_arit | op_stmt_num → op_rel | | | op_stmt_num → op_arit | op_stmt_num → op_arit | |
| **op_stmt_stmt** | op_stmt_stmt → op_arit | op_stmt_stmt → op_rel | op_stmt_stmt → op_rel | op_stmt_stmt → op_rel | | op_stmt_stmt → op_arit | | | op_stmt_stmt → KEYWORD_IF | | | op_stmt_stmt → op_rel | op_stmt_stmt → op_rel | op_stmt_stmt → op_arit | op_stmt_stmt → op_arit | op_stmt_stmt → op_arit | op_stmt_stmt → op_rel | | | op_stmt_stmt → op_arit | op_stmt_stmt → op_arit | |
| **prog** | | | | | | | | | | | prog → LPAREN KEYWORD_START RPAREN list_stmts EOF | | | | | | | | | | | |
| **rpn** | | | | | rpn → ID | | | | | | rpn → stmt rpn_tail_stmt | | | rpn → num rpn_tail_num | | | | rpn → num rpn_tail_num | rpn → num rpn_tail_num | | | rpn → STRING KEYWORD_MORSE |
| **rpn_tail_num** | | | | | rpn_tail_num → ID | | | | | rpn_tail_num → KEYWORD_RES | rpn_tail_num → stmt op_stmt_num | | | rpn_tail_num → num op_bin | | | | rpn_tail_num → num op_bin | rpn_tail_num → num op_bin | | | |
| **rpn_tail_stmt** | | | | | rpn_tail_stmt → ID | | | | | | rpn_tail_stmt → stmt op_stmt_stmt | | | rpn_tail_stmt → num op_bin | | | | rpn_tail_stmt → num op_bin | rpn_tail_stmt → num op_bin | | | |
| **stmt** | | | | | | | | | | | stmt → LPAREN rpn RPAREN | | | | | | | | | | | |
