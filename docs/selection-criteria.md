# Critérios de seleção dos defeitos

## População inicial

A população inicial é composta por todos os defeitos ativos
disponibilizados pelo Defects4J 3.0.1 nos seguintes projetos:

- Apache Commons Lang (Lang): 61 defeitos.
- Jsoup: 93 defeitos.
- Gson: 18 defeitos.

Total: 172 defeitos.

## Estratégia de seleção

Será realizado um censo dos defeitos que atenderem aos
critérios de elegibilidade definidos neste documento.

Não haverá seleção com base nos resultados do PMD ou SpotBugs.

## Critérios de inclusão

1. Defeito ativo registrado no Defects4J 3.0.1.
2. Disponibilidade da versão defeituosa e da versão corrigida.
3. Existência de teste de referência associado ao defeito.
4. Possibilidade de reproduzir o comportamento defeituoso.
5. Possibilidade de executar o procedimento experimental
   no ambiente configurado.

## Critérios de exclusão

1. Defeito cuja versão defeituosa não possa ser recuperada.
2. Defeito sem teste de referência executável.
3. Defeito que não possa ser reproduzido após investigação
   das condições de execução.
4. Projeto incompatível com o procedimento experimental,
   mesmo após tentativa documentada de configuração.

## Registro

Cada defeito será identificado por projeto e ID.

As exclusões deverão conter justificativa técnica registrada.

A capacidade de detecção do PMD ou SpotBugs não será
utilizada como critério de inclusão ou exclusão.
