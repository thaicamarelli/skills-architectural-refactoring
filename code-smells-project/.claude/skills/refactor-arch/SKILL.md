---
name: refactor-arch
description: >-
  Audita e refatora automaticamente uma base de código para o padrão MVC, de forma
  agnóstica de tecnologia. Roda em 3 fases — (1) Análise: detecta linguagem, framework,
  banco e arquitetura atual; (2) Auditoria: cruza o código contra um catálogo de
  anti-patterns/code smells, classifica por severidade com arquivo:linha exatos, gera
  um relatório e pede confirmação; (3) Refatoração: reestrutura para MVC e valida que a
  aplicação continua funcionando. Use SEMPRE que o usuário pedir para auditar arquitetura,
  encontrar code smells ou anti-patterns, revisar segurança/qualidade de um projeto legado,
  refatorar/reestruturar para MVC ou camadas, "organizar" uma codebase bagunçada, ou
  invocar /refactor-arch — mesmo que não diga "MVC" explicitamente, e independentemente da
  stack (Python/Flask, Node/Express, etc.).
---

# refactor-arch — Auditoria e Refatoração Arquitetural para MVC

Esta skill transforma um projeto legado, de qualquer stack, em uma arquitetura MVC limpa.
Ela existe porque revisar e corrigir código manualmente é lento e inconsistente: aqui o
conhecimento de "o que é um anti-pattern e como corrigi-lo" vive nos arquivos de referência,
e o SKILL.md apenas orquestra o processo em 3 fases sequenciais.

## Princípios que valem para todas as fases

- **Seja agnóstico de tecnologia.** Não assuma Python ou Node. Descubra a stack na Fase 1 e
  deixe essa descoberta guiar tudo depois. As referências trazem sinais para várias stacks.
- **Aponte evidências, não opiniões.** Todo achado precisa de `arquivo:linha` e do trecho que
  o comprova. "Código ruim" não ajuda ninguém; "SQL montado com concatenação de string em
  `models.py:47`" é acionável.
- **Nunca modifique arquivos antes da confirmação humana.** As Fases 1 e 2 são somente leitura.
  A Fase 3 só começa depois de um "sim" explícito do usuário. Esse portão é a segurança do
  processo — respeite-o.
- **Preserve o comportamento.** Refatorar não é reescrever regras de negócio. Os mesmos
  endpoints devem responder da mesma forma depois. Se um bug de segurança for corrigido
  (ex.: senha em texto puro), avise o usuário da mudança de comportamento.
- **Adapte-se ao ponto de partida.** Um monolito de 4 arquivos e um projeto que já tem
  `models/` e `routes/` exigem transformações diferentes. Não imponha estrutura onde ela já
  existe — melhore o que está lá.

## Arquivos de referência

Leia o arquivo relevante **no início da fase correspondente** — não tente decorar tudo de uma vez.

| Arquivo | Quando ler | O que contém |
|---|---|---|
| `references/project-analysis.md` | Início da Fase 1 | Heurísticas para detectar linguagem, framework, banco de dados e mapear a arquitetura atual |
| `references/antipattern-catalog.md` | Início da Fase 2 | Catálogo de anti-patterns e code smells, com sinais de detecção, severidade e APIs deprecated |
| `references/report-template.md` | Ao gerar o relatório (Fase 2) | Formato exato do relatório de auditoria |
| `references/mvc-architecture.md` | Início da Fase 3 | Regras do MVC alvo: responsabilidades de Models, Views/Routes, Controllers, Config e Middlewares |
| `references/refactoring-playbook.md` | Durante a Fase 3 | Transformações concretas (antes/depois) para eliminar cada anti-pattern |

---

## Fase 1 — Análise

Objetivo: entender o terreno antes de julgar. Saída: um resumo impresso da stack e arquitetura.

1. Leia `references/project-analysis.md`.
2. Aplique as heurísticas: identifique **linguagem**, **framework (com versão)**, **dependências
   relevantes**, **banco de dados/tabelas**, **domínio da aplicação** e **arquitetura atual**
   (quantos arquivos, como as responsabilidades estão distribuídas, existe separação de camadas?).
3. Conte os arquivos de código-fonte de verdade (ignore `node_modules`, `venv`, `.git`, lockfiles).
4. Imprima o resumo **exatamente neste formato** (preencha os valores; omita linhas que não se
   aplicam ao projeto):

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem>
Framework:     <framework e versão>
Dependencies:  <deps relevantes>
Domain:        <o que a aplicação faz, em uma linha>
Architecture:  <descrição da arquitetura atual>
Source files:  <N> files analyzed
DB tables:     <tabelas detectadas>
================================
```

Não sugira correções ainda. Aqui você só descreve o que existe.

---

## Fase 2 — Auditoria

Objetivo: encontrar os problemas, classificá-los e produzir um relatório para o humano revisar.
Esta fase é **somente leitura**.

1. Leia `references/antipattern-catalog.md`.
2. Percorra os arquivos-fonte cruzando cada um contra os sinais de detecção do catálogo. Para
   cada ocorrência, registre: nome do anti-pattern, severidade, `arquivo:linha(s)`, uma
   descrição do problema real naquele trecho, o impacto e a recomendação.
   - Inclua explicitamente a detecção de **APIs deprecated** (o catálogo tem uma seção para isso):
     aponte o uso obsoleto e o equivalente moderno.
   - Priorize achados de maior impacto arquitetural e de segurança. Encontre **no mínimo 5**
     achados, com **pelo menos 1 CRITICAL ou HIGH**.
3. Gere o relatório seguindo `references/report-template.md`. Ordene os findings por severidade
   (CRITICAL → HIGH → MEDIUM → LOW).
4. **Salve** o relatório em `reports/audit-<nome-do-projeto>.md` (crie a pasta `reports/` se
   necessário) e **imprima o relatório completo no terminal** — não apenas o `## Summary`. A
   seção `## Findings` deve aparecer no terminal com **todos os findings expandidos** no formato
   do template: cada um com `### [SEVERIDADE] <Nome do Anti-Pattern>`, `File:`, `Description:`,
   `Impact:` e `Recommendation:`. O terminal e o arquivo salvo devem ter exatamente o mesmo
   conteúdo. Nunca resuma os findings a uma lista de títulos ou só à contagem por severidade.
5. **PARE e peça confirmação** antes de qualquer modificação. Use exatamente:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

   Só avance para a Fase 3 se a resposta for afirmativa. Se for negativa, encerre deixando o
   relatório salvo.

---

## Fase 3 — Refatoração

Objetivo: reestruturar para MVC eliminando os problemas do relatório, sem quebrar a aplicação.
Só execute após a confirmação da Fase 2.

1. Leia `references/mvc-architecture.md` (o alvo) e `references/refactoring-playbook.md` (o como).
2. Planeje a nova estrutura de pastas com base no MVC e no que o projeto já tem. Reaproveite
   camadas existentes em vez de recriá-las.
3. Aplique as transformações do playbook, endereçando os findings do relatório por ordem de
   severidade. Passos que quase sempre se aplicam:
   - Extrair configuração/segredos para um módulo de config (nada hardcoded; ler de env).
   - Criar **Models** que encapsulam acesso a dados (com queries parametrizadas — fim do SQL
     Injection) e a lógica de domínio.
   - Separar **Views/Routes** (só HTTP: rota, request, response) dos **Controllers** (orquestram
     o fluxo e chamam Models/Services).
   - Centralizar **error handling** em um middleware/handler.
   - Definir um **entry point** claro (composition root) que só monta a aplicação.
   - Substituir APIs deprecated pelos equivalentes modernos.
4. **Valide** o resultado — este passo é obrigatório:
   - A aplicação **inicia sem erros** (rode o comando de boot da stack; ex.: `python app.py`,
     `npm start`).
   - Os **endpoints originais continuam respondendo** (dispare algumas requisições
     representativas; use o `.http` do projeto se existir, ou `curl`).
   - Idealmente, **zero anti-patterns** do relatório permanecem. Se algum não pôde ser
     removido, diga qual e por quê.
5. Imprima o resumo final **neste formato**:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios resultante>

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero anti-patterns remaining
================================
```

Se a validação falhar, não declare sucesso: mostre o erro, corrija e valide de novo. É melhor
reportar honestamente um endpoint quebrado do que fingir que passou.

---

## Como esta skill é reutilizada

A skill é agnóstica de propósito: a pasta `refactor-arch/` inteira pode ser copiada para dentro
de qualquer outro projeto (`.claude/skills/refactor-arch/`) e invocada com `/refactor-arch`. Todo
o conhecimento específico de stack está nos arquivos de referência, que já cobrem múltiplas
tecnologias — então nada aqui deve ser reescrito de projeto para projeto.
