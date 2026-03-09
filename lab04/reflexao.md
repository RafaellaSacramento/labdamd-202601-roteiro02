# Reflexao — Roteiro 02

## 1) Sintese

Eu considero a transparencia de concorrencia uma das mais dificeis de implementar corretamente em sistemas reais, porque envolve sincronizacao entre processos/maquinas, latencia e falhas parciais.
No laboratorio, isso ficou evidente quando dois processos atualizaram o mesmo saldo no Redis sem coordenacao, produzindo um saldo final incorreto (race condition).
Quando aplicamos um lock distribuido, a complexidade aumenta (TTL, espera, falhas), mas o resultado fica consistente.
Relaciono isso com as demais tarefas: T3 reforca estado fora da instancia (Redis), e T5 mostra que replicacao/failover precisa ser transparente, mas ainda tem trade-offs de consistencia.

## 2) Trade-offs

Um cenario em que esconder totalmente a distribuicao pode piorar a resiliencia e quando o app trata chamadas remotas como se fossem locais (anti-pattern), sem expor latencia/timeout.
Por exemplo, em um app que busca dados de um servico remoto, se a API parece “instantanea” e nao obriga o chamador a tratar falhas, o usuario pode ficar travado em loading ou o sistema pode quebrar em cascata.
Nesse caso, e melhor ter um contrato explicito (ex.: nome indicando remoto, timeout, retorno opcional) para que a camada de negocio implemente fallback e mensagens de erro amigaveis.
Ou seja: transparencia demais pode esconder falhas de rede e levar a uma experiencia pior do que uma transparência “consciente”.

## 3) Conexao com Labs anteriores

O `async/await` ajuda a deixar explicito que uma operacao pode “esperar” (I/O) e nao e equivalente a uma chamada local.
Isso quebra a transparencia de proposito: quando eu vejo `await`, eu sei que existe latencia e que podem ocorrer timeouts/falhas parciais.
Esse ponto se conecta com a ideia da Tarefa 7 (limites da transparencia): esconder rede como chamada local viola falacias da computacao distribuida.
Entao, `async/await` e uma decisao de design que torna o custo da distribuicao mais visivel e facilita tratar erro e degradacao de forma correta.

## 4) GIL e multiprocessing

A Tarefa 6 usa `multiprocessing` em vez de `threading` porque, no CPython, existe o GIL (Global Interpreter Lock) que impede duas threads de executarem bytecode Python ao mesmo tempo no mesmo processo.
Isso pode mascarar ou tornar nao-reproduziveis algumas race conditions em exemplos didaticos, ja que as threads nao rodam em paralelo “de verdade” no nivel do interpretador.
Com `multiprocessing`, cada processo tem seu proprio espaco de memoria e seu proprio GIL, entao a concorrencia fica mais parecida com um sistema distribuido (processos separados, possivelmente em maquinas diferentes).
Assim, o problema de condicao de corrida fica mais realista e a necessidade de lock distribuido (ex.: via Redis) fica evidente.

## 5) Desafio tecnico

Minha principal dificuldade foi configurar o Redis Cloud e as variaveis no `.env`, porque quando alguma variavel estava vazia o script caia no default (`localhost:6379`) e a conexao falhava.
O diagnostico foi feito observando a mensagem de erro (ConnectionRefused/ConnectionError) e validando a configuracao com `teste_conexao_redis.py` (que depois retornou `SET/GET funcionando: ok`).
Depois disso, a Tarefa 3 funcionou: a Instancia A salvou `session:user_42` no Redis e a Instancia B recuperou a mesma sessao em um processo Python separado.
O ponto tecnico principal que aprendi e que, em sistemas distribuidos, estado em memoria local nao sobrevive a migracao/replicas; um store externo (Redis) e essencial.

## Tarefa 4 — Relocacao

1) Qual e a diferenca pratica entre migracao (Tarefa 3) e relocacao (Tarefa 4)? Por que relocacao e tecnicamente mais dificil?

Na migracao, a instancia “A” encerra e outra instancia “B” assume depois, entao existe uma quebra natural entre as duas execucoes.
O foco e garantir que o estado (ex.: sessao) esteja fora da memoria do processo, em um store externo (Redis), para sobreviver a troca de instancia.
Ja a relocacao acontece “ao vivo”: o cliente continua usando o recurso enquanto ele muda de endpoint/instancia, e o codigo de negocio idealmente nao percebe.
Isso e mais dificil porque existem mensagens em voo, latencia, reconexao, ordem de entrega e consistencia do estado durante o handoff (troca de conexao).

2) O buffer interno (`_message_buffer`) garante semantica exactly-once? O que poderia causar entrega duplicada ou perda de mensagem mesmo com buffer?

Nao, o buffer por si so nao garante exactly-once; no maximo ele ajuda a aproximar uma semantica “at-least-once” para mensagens geradas durante MIGRATING.
Pode haver duplicacao se uma mensagem foi enviada antes de detectar a migracao (ou foi enviada e o ack se perdeu) e depois for reenviada do buffer na reconexao.
Pode haver perda se o processo cliente cair durante a migracao, porque o `_message_buffer` e memoria local (nao persistida) e sera perdido.
Para reduzir isso, normalmente voce precisa de IDs de mensagem, acknowledgements, idempotencia/deduplicacao no servidor e, em alguns casos, persistencia do buffer.

3) Por que modelar estados explicitamente (CONNECTED/MIGRATING/RECONNECTING) em vez de uma flag booleana `is_relocating`?

Estados explicitos formam uma maquina de estados finita, o que deixa claro quais transicoes sao validas e quais comportamentos devem ocorrer em cada fase.
Uma flag booleana so diz “esta relocando” ou “nao esta”, mas nao distingue etapas importantes (ex.: migrando vs. tentando reconectar), que exigem acoes diferentes.
Isso melhora a legibilidade e ajuda a evitar bugs de concorrencia/condicao de corrida, como enviar mensagens enquanto ainda nao existe conexao nova.
Tambem facilita testes e log/observabilidade, porque o sistema consegue registrar em que fase esta e reagir de forma deterministica.

4) Cite um sistema real em que transparencia de relocacao e requisito (ex.: Kubernetes, live migration).

Um exemplo e o Kubernetes quando um Pod e reescalonado (rescheduling) para outro node: o endpoint real muda e o cliente tenta continuar acessando via Service/DNS.
Outro exemplo e live migration de VMs (ex.: hypervisors) ou de conexoes em proxies/LBs que precisam manter sessoes ativas sem derrubar o usuario.
Em apps mobile, a troca de rede (Wi‑Fi para 4G/5G) pode exigir reconexao transparente para manter streams ou chats em tempo real.
Em todos esses casos, a ideia e manter continuidade de uso apesar de mudancas de localizacao/endpoint, lidando internamente com reconexao e falhas transitórias.

## Tarefa 7 — Falha (bonus)

Parte A (Circuit Breaker): codigo em `t7_falha/transparencia_falha.py`.

Parte B (quando NAO aplicar transparencia):

1) Qual falacia das oito falacies da computacao distribuida (Peter Deutsch) o `anti_pattern.py` viola diretamente?

Viola a falacia de que “a rede e confiavel” (e, em parte, a de que “a latencia e zero”).
No anti-pattern, a funcao parece uma consulta local simples, mas na pratica uma chamada remota pode falhar, atrasar, retornar vazio e quebrar o fluxo do programa.
Quando o contrato nao expõe isso, o chamador nao implementa timeouts/fallback e os erros aparecem em camadas erradas (ex.: KeyError adiante).
Isso piora a resiliencia e a depuracao, porque o local real da falha (rede/servico) fica escondido.

2) Por que `async/await` e uma forma deliberada de quebrar a transparencia — e por que isso e correto aqui?

`async/await` torna explicito no codigo que aquela operacao pode suspender por I/O e, portanto, tem custo de latencia e chance de timeout.
Isso “quebra” a ideia de chamada local transparente, mas obriga o chamador a tratar o caso de falha e a nao bloquear a aplicacao esperando indefinidamente.
No contexto de chamadas remotas, essa explicitacao melhora o design do contrato (timeout, retorno Optional, erros tratados) e evita efeitos cascata.
Ou seja, e uma transparencia consciente: o sistema tenta ser amigavel, mas nao finge que rede e memoria local.