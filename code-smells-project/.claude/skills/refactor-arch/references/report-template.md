# Template do Relatório de Auditoria (Fase 2)

Use este formato **exato** ao gerar o relatório. Ele é salvo em
`reports/audit-<nome-do-projeto>.md` e também impresso no terminal — **na íntegra, com todos os
findings expandidos** (título, `File:`, `Description:`, `Impact:`, `Recommendation:`), nunca só o
`## Summary` ou uma lista de títulos. A consistência importa: o relatório precisa ser comparável
entre projetos e stacks diferentes.

## Regras de preenchimento

- **Ordene os findings por severidade:** todos os CRITICAL, depois HIGH, MEDIUM e LOW.
- **Cada finding tem `arquivo:linha(s)` exatos.** Se o problema é um bloco, use um intervalo
  (`models.py:1-350`); se é uma linha, use a linha (`app.py:8`).
- **Descrição, Impacto e Recomendação** são frases curtas e concretas, referindo-se ao trecho
  real — não copie a definição genérica do catálogo.
- O contador do `## Summary` deve bater com a quantidade de findings listados.
- Use o **nome do anti-pattern** do catálogo no título de cada finding, entre colchetes com a
  severidade.

## Formato

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome-do-projeto>
Stack:   <linguagem> + <framework>
Files:   <N> analyzed | ~<linhas> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [CRITICAL] <Nome do Anti-Pattern>
File: <arquivo>:<linha(s)>
Description: <o que está errado neste trecho específico>
Impact: <consequência concreta se não for corrigido>
Recommendation: <como corrigir, apontando a camada/transformação alvo>

### [CRITICAL] <Nome do Anti-Pattern>
File: <arquivo>:<linha(s)>
Description: ...
Impact: ...
Recommendation: ...

### [HIGH] <Nome do Anti-Pattern>
File: <arquivo>:<linha(s)>
Description: ...
Impact: ...
Recommendation: ...

### [MEDIUM] <Nome do Anti-Pattern>
File: <arquivo>:<linha(s)>
Description: ...
Impact: ...
Recommendation: ...

### [LOW] <Nome do Anti-Pattern>
File: <arquivo>:<linha(s)>
Description: ...
Impact: ...
Recommendation: ...

================================
Total: <N> findings
================================
```

Depois de imprimir o relatório, e antes de qualquer modificação, imprima a linha de confirmação:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## Exemplo preenchido (trecho)

Use como calibração de tom e nível de detalhe:

```
### [CRITICAL] SQL Injection
File: models.py:26
Description: get_produto_por_id monta a query concatenando o id direto na string SQL
("SELECT * FROM produtos WHERE id = " + str(id)), sem parâmetros.
Impact: Um id malicioso permite ler ou destruir o banco inteiro. O padrão se repete em
todas as funções de acesso a dados do arquivo.
Recommendation: Mover o acesso a dados para um Model e usar queries parametrizadas
(cursor.execute("... WHERE id = ?", [id])).

### [MEDIUM] Query N+1
File: models.py:170-200
Description: get_todos_pedidos busca os itens de cada pedido e, para cada item, o nome do
produto em queries separadas dentro de laços aninhados.
Impact: O número de queries cresce linearmente com pedidos e itens; degrada com o volume.
Recommendation: Buscar itens e produtos com JOIN ou um único IN (...) e montar o resultado
em memória.
```
