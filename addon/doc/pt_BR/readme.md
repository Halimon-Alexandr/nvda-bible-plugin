# Bíblia

Este aplicativo é projetado para o estudo conveniente das Sagradas Escrituras e oferece ferramentas avançadas de navegação, busca e gerenciamento de traduções bíblicas. Isso permite navegar facilmente pelo texto, alternar entre livros, capítulos e versículos, trabalhar com diferentes traduções e comparar passagens bíblicas.

**Desenvolvedor:** Alexandr Halimon

**Email:** [halimon.alexandr@gmail.com](mailto:halimon.alexandr@gmail.com)

**Repositório:** [GitHub](https://github.com/Halimon-Alexandr/nvda-bible-plugin)

Apoio ao projeto

[PrivatBank Ukraine](https://www.privat24.ua/send/jkjck)  

[PayPal](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=halimon.alexandr@gmail.com)

---

## Principais recursos

O aplicativo permite:

- Usar um sistema de abas para trabalhar simultaneamente com vários textos das Escrituras.
- Navegar rapidamente entre livros, capítulos, versículos e traduções.
- Copiar versículos e trechos com referência.
- Visualizar referências paralelas e trechos semelhantes em contexto.
- Usar busca por texto com opções de filtro por livros, capítulos ou versículos, incluindo busca inteligente com a API Gemini.
- Trabalhar com planos de leitura, acompanhar o progresso e marcar trechos lidos.
- Baixar e excluir traduções para diferentes idiomas e planos de leitura.

---

### Janela principal

A janela principal contém:

- **Campo de texto** com o texto da Bíblia, que ocupa a maior parte da tela.
- **Três listas suspensas** para seleção de livro, capítulo e tradução.

O conteúdo do campo de texto corresponde aos parâmetros selecionados. O cabeçalho da janela exibe o livro atual, capítulo e tradução, ajudando a identificar rapidamente qual trecho está aberto.

**Abrir a janela:** `NVDA+X`

Nota: Na primeira execução do aplicativo, a janela de configurações é aberta automaticamente. Para começar a usar, é necessário baixar pelo menos uma tradução da Bíblia, depois fechar as configurações e reiniciar o aplicativo.

**Navegação e controle:**

- **Alternar entre listas suspensas e texto:** `Tab` / `Shift+Tab`
- **Ir para o próximo/livro anterior:** `B` / `Shift+B`
- **Ir para o próximo/capítulo anterior:** `C` / `Shift+C`
- **Ir para a próxima/tradução anterior:** `T` / `Shift+T`
- **Mover o cursor 5 versículos para trás/frente:** `PageUp` / `PageDown`
- **Mover o cursor 10 versículos para trás/frente:** `Ctrl+PageUp` / `Ctrl+PageDown`
- **Ir rapidamente para um versículo:** digite `0–9`

**Gerenciamento de abas:**

- **Criar uma nova aba:** `Ctrl+T`
- **Fechar a aba atual:** `Ctrl+W`
- **Alternar para a próxima/aba anterior:** `Ctrl+Tab` / `Ctrl+Shift+Tab`
- **Ir para a aba 1–9:** `Ctrl+1` .. `Ctrl+9`

**Configurações de visualização:**

- **Mostrar/ocultar números dos versículos:** `Ctrl+H`
- **Aumentar/diminuir o tamanho da fonte:** `Ctrl++` / `Ctrl+-`

**Teclas dependentes de contexto:**

- **Copiar o versículo atual ou texto selecionado com referência bíblica:** `Ctrl+Shift+C`
- **Abrir a janela de referências paralelas para o versículo atual:** `Ctrl+Shift+L`

**Outras teclas:**

- **Pesquisar na página:** `Ctrl+Shift+F`
- **Ir para o próximo/resultado anterior da pesquisa:** `F3` / `Shift+F3`
- **Pesquisar na Bíblia:** `Ctrl+F`
- **Planos de leitura:** `Ctrl+R`
- **Ir para a referência:** `Ctrl+L`
- **Fechar a janela:** `Alt+F4` ou `Esc`
- **Ajuda:** `F1`

---

### Janela de busca

A janela de busca é destinada à pesquisa de versículos bíblicos por texto em todos os livros ou em capítulos selecionados. Suporta filtragem por livros, busca por palavra inteira, sensibilidade a maiúsculas/minúsculas e uso de expressões regulares. Também está disponível a busca inteligente usando a API Gemini.

**Elementos principais:**

- **Campo para inserir a consulta de busca**
- **Caixas de seleção para parâmetros de busca** (palavra inteira, sensibilidade a maiúsculas/minúsculas, expressões regulares)
- **Lista de resultados da busca**

**Teclas de controle:**

- **Alternar entre elementos da janela:** `Tab` / `Shift+Tab`
- **Pesquisar na página:** `Ctrl+Shift+F`
- **Ir para o próximo/resultado anterior da pesquisa:** `F3` / `Shift+F3`
- **Visualizar o resultado selecionado no contexto do capítulo:** `Ctrl+Q`
- **Abrir o resultado selecionado na janela principal:** `Enter`
- **Abrir o resultado selecionado em uma nova aba:** `Ctrl+Enter`
- **Fechar a janela de busca:** `Esc`
- **Abrir a ajuda:** `F1`

---

### Janela de planos de leitura

A janela de planos de leitura é destinada ao trabalho com planos de leitura da Bíblia e ao acompanhamento do progresso. Permite marcar dias e trechos lidos, alternar entre os dias do plano, alterar traduções e visualizar o conteúdo de cada dia.

**Elementos principais:**

- **Lista suspensa de dias** para seleção de um dia específico do plano.
- **Lista de leituras** para o dia selecionado.
- **Campo de texto** para exibir o texto do trecho selecionado.

**Teclas de controle:**

- **Alternar entre elementos da janela:** `Tab` / `Shift+Tab`
- **Marcar dia ou trecho como lido/não lido:** `Espaço`
- **Alterar tradução:** `T` / `Shift+T`
- **Alterar plano de leitura:** `Ctrl+Tab` / `Ctrl+Shift+Tab`
- **Mover o cursor 5 versículos para trás/frente:** `PageUp` / `PageDown`
- **Mover o cursor 10 versículos para trás/frente:** `Ctrl+PageUp` / `Ctrl+PageDown`
- **Ir para o versículo:** digite `0–9`
- **Aumentar o tamanho da fonte:** `Ctrl++`
- **Diminuir o tamanho da fonte:** `Ctrl+-`
- **Mostrar/ocultar números dos versículos:** `Ctrl+H`
- **Pesquisar na página:** `Ctrl+Shift+F`
- **Ir para o próximo/resultado anterior da pesquisa:** `F3` / `Shift+F3`
- **Fechar a janela:** `Esc`
- **Ajuda:** `F1`

---

### Janela de referência e criação de nova aba

Essas janelas são destinadas à navegação rápida para um livro, capítulo ou versículo específico, inserindo uma referência bíblica, bem como para abrir uma nova aba com parâmetros definidos. São suportados diferentes formatos de referência, incluindo nomes abreviados de livros, números de capítulos e versículos. A lista de abreviações disponíveis está na ajuda do aplicativo.

São aceitos tanto o formato oriental (por exemplo, "Jo 3:16") quanto o formato ocidental ("Jo 3,16").

**Elementos principais:**

- **Campo para inserir a referência** (mantém o histórico das últimas referências).
- **Botão padrão** (abre Gênesis, capítulo 1).
- **Botão de confirmação de referência**.

**Teclas de controle:**

- **Ir para a referência inserida:** `Enter`
- **Fechar a janela:** `Esc`
- **Abrir a ajuda:** `F1`

---

### Janela de referências paralelas

A janela de referências paralelas é destinada à visualização e análise de passagens paralelas e trechos bíblicos semelhantes em contexto para o versículo selecionado. Isso ajuda a compreender melhor o conteúdo do texto e as conexões entre diferentes partes das Escrituras.

**Elementos principais:**

- **Campo de texto** com a lista de referências paralelas.

**Teclas de controle:**

- **Pesquisar na página:** `Ctrl+Shift+F`
- **Ir para o próximo/resultado anterior da pesquisa:** `F3` / `Shift+F3`
- **Visualizar o resultado selecionado no contexto do capítulo:** `Ctrl+Q`
- **Abrir o resultado selecionado na janela principal:** `Enter`
- **Abrir o resultado selecionado em uma nova aba:** `Ctrl+Enter`
- **Fechar a janela:** `Esc`
- **Abrir a ajuda:** `F1`

---

### Menu do aplicativo

O menu do aplicativo replica principalmente as funções das teclas de atalho e é projetado para a conveniência dos usuários que não se lembram de todas as combinações de teclas. Está disponível na janela principal e na janela de planos de leitura.

**Principais recursos do menu:**

- Execução de ações disponíveis por meio de teclas de atalho.
- Gerenciamento de parâmetros de visualização e abas.
- Acesso às configurações do aplicativo e à ajuda.

---

### Menu de contexto

O menu de contexto permite executar rapidamente ações principais com o texto selecionado, versículo atual ou resultado de busca selecionado no texto da Bíblia.

O menu de contexto está disponível:

- na **janela principal**;
- na **janela de busca**;
- na **janela de referências paralelas**.

O menu de contexto é aberto usando:

- `Shift+F10` ou a tecla de menu de contexto no teclado.

**Principais funções do menu de contexto:**

- **Visualização rápida** — abre o resultado selecionado no contexto do capítulo correspondente.
- **Abrir na aba atual** — abre o local selecionado na aba ativa.
- **Abrir em nova aba** — abre o local selecionado em uma nova aba.
- **Copiar** o texto selecionado ou o versículo atual junto com a referência bíblica (na janela principal).
- **Abrir a lista de referências paralelas** para o versículo atual (na janela principal).

---

### Configurações

A seção de configurações é destinada ao gerenciamento dos principais parâmetros do aplicativo, incluindo traduções, planos de leitura, integração com a API Gemini e parâmetros de atualização.

**Principais recursos:**

- **Gerenciamento de traduções** (download e exclusão).
- **Gerenciamento de planos de leitura** (download, exclusão e redefinição de progresso).
- **Inserção da chave da API** para habilitar a busca inteligente.
- **Ativar/desativar** a verificação automática de atualizações.

**Como abrir as configurações:**

- Pelo menu do aplicativo: **Ferramentas → Configurações**.
- Pelo menu de configurações do NVDA: **NVDA+N → Opções → Configurações → Bíblia**.

---

### Licença

O aplicativo "Bíblia" é distribuído sob a licença **[GPL 2](https://www.gnu.org/licenses/gpl-2.0.html)**
```---

Якщо потрібно додатково уточнити або адаптувати окремі частини, дайте знати!
