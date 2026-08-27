# Jarvis — Protótipo Inicial

Este é o primeiro passo de um assistente de automação pessoal. Por enquanto
ele **não escuta sua voz** — é só a "mecânica" de base: um script Python que,
quando executado, faz duas coisas:

1. Abre uma nova janela do navegador direto em um vídeo do YouTube e move
   essa janela para o **monitor secundário**.
2. Abre o **IntelliJ IDEA** e move a janela dele para o **monitor
   principal**, já maximizada.

A ideia é: depois que essa parte estiver sólida e confiável, a gente pluga
por cima o reconhecimento de voz e um LLM decidindo qual função chamar
(exatamente como conversamos antes). Por ora, o foco é só garantir que a
automação de janelas funciona bem no seu Windows.

---

## Como funciona (por baixo dos panos)

- **`screeninfo`** lista os monitores conectados e suas posições/tamanhos
  (coordenadas x, y, largura, altura). Com isso o script sabe onde fica o
  monitor principal e onde fica o secundário.
- O script abre o navegador (Chrome ou Edge) usando o argumento
  `--new-window`, o que garante que uma janela nova e "limpa" seja criada
  (facilita encontrá-la depois).
- **`pygetwindow`** (que por baixo usa o `pywin32`) é usado para: procurar a
  janela recém-aberta pelo título, mover ela (`moveTo`) e redimensionar
  (`resizeTo`) para as coordenadas do monitor desejado.
- O mesmo processo se repete para o IntelliJ IDEA, mas movendo para o
  monitor principal e chamando `maximize()` no final.
- Como abrir um programa é assíncrono (a janela não aparece instantaneamente),
  o script fica checando a cada meio segundo (`wait_for_window`) até a janela
  aparecer, com um tempo limite de segurança.

---

## Instalação

**Pré-requisitos:** Python 3.9+ instalado no Windows.

1. Extraia os arquivos deste projeto em uma pasta, por exemplo:
   `C:\Users\SeuUsuario\jarvis`

2. Abra o terminal (PowerShell ou CMD) nessa pasta e crie um ambiente
   virtual (recomendado, mas opcional):

   ```powershell
   python -m venv venv
   venv\Scripts\activate
   ```

3. Instale as dependências:

   ```powershell
   pip install -r requirements.txt
   ```

---

## Configuração (IMPORTANTE — faça antes de rodar)

Abra o arquivo `jarvis.py` em um editor de texto e ajuste as variáveis no
topo do arquivo, na seção `CONFIGURAÇÃO`:

| Variável | O que é | Como descobrir |
|---|---|---|
| `INTELLIJ_PATH` | Caminho completo do `idea64.exe` | Clique com o botão direito no atalho do IntelliJ na área de trabalho → Propriedades → veja o campo "Destino/Local do arquivo" |
| `BROWSER_PATH` | Caminho do navegador (opcional) | Deixe `None` para detecção automática (Chrome ou Edge). Só preencha se usar outro navegador ou instalação em local não padrão |
| `YOUTUBE_VIDEO_URL` | URL do vídeo que deve abrir | Copie o link do vídeo desejado no YouTube |
| `SECONDARY_MONITOR_SIDE` | `"left"` ou `"right"` | Onde fica o monitor secundário em relação ao principal (na sua mesa) |

> **Nota sobre a música:** "Iron Man" é do Black Sabbath, não do Iron Maiden
> — são bandas diferentes de heavy metal, fácil de confundir. Deixei o clipe
> oficial do Black Sabbath como padrão em `YOUTUBE_VIDEO_URL`. Se você queria
> uma música do Iron Maiden mesmo, é só trocar o link.

---

## Como usar

Com o ambiente virtual ativado (se você criou um), rode:

```powershell
# Executa as duas ações (YouTube + IntelliJ)
python jarvis.py

# Ou execute só uma ação de cada vez:
python jarvis.py youtube
python jarvis.py intellij
```

O script vai imprimir no terminal cada passo que está executando, então dá
pra acompanhar o que está acontecendo em tempo real.

---

## Problemas comuns

- **"Não encontrei o IntelliJ IDEA em: ..."** → o caminho em `INTELLIJ_PATH`
  está errado. Corrija apontando para o `idea64.exe` real.
- **"Não encontrei Chrome nem Edge nos caminhos padrão."** → seu navegador
  está instalado em outro lugar, ou você usa outro navegador (ex: Firefox,
  Brave). Preencha `BROWSER_PATH` manualmente com o caminho do `.exe`.
- **A janela abre mas não é movida para o monitor certo** → às vezes o
  Windows demora mais para "assentar" a janela recém-criada. Rode o script
  de novo, ou aumente o valor de `WINDOW_WAIT_TIMEOUT`.
- **"apenas um monitor detectado"** → o script não encontrou um segundo
  monitor conectado. Confira em Configurações do Windows → Sistema → Tela
  se os dois monitores estão sendo reconhecidos.
- **IntelliJ demora muito para abrir** → é normal, IDEs Java são pesadas.
  O script já espera até 40 segundos para essa janela específica.

---

## Camada de voz (`jarvis_voice.py`)

Esse arquivo fica escutando o microfone continuamente. Quando você diz uma
frase contendo **"jarvis"** e **"ligar"** (ex: "Jarvis, ligar"), ele:

1. Fala **"Iniciando senhor"** em voz alta.
2. Chama as mesmas funções do `jarvis.py` para abrir o YouTube no monitor
   secundário e o IntelliJ no monitor principal.

Ele não substitui o `jarvis.py` — importa e reaproveita as funções de lá.
Assim, a lógica de "o que fazer" continua num arquivo só.

### Como funciona por baixo dos panos

- **`SpeechRecognition`** captura o áudio do microfone e manda para a API
  pública de reconhecimento de voz do Google (`recognize_google`), que
  devolve o texto transcrito. É gratuita e não precisa de chave de API,
  mas **exige internet** e tem limites de uso informais (não é para uso
  comercial pesado — para um assistente pessoal funciona bem).
- O script escuta em loop (`recognizer.listen`), transcreve cada frase e
  verifica se ela contém uma palavra de ativação (`"jarvis"`) **e** uma
  palavra de comando (`"ligar"`, `"liga"`, `"iniciar"`, `"inicia"`). Exigir
  as duas evita que ele dispare à toa se você só mencionar "jarvis" numa
  conversa qualquer.
- **`pyttsx3`** usa as vozes de Text-to-Speech já instaladas no Windows
  (SAPI5) para falar a resposta — não precisa de internet nem de serviço
  externo, e o som já tem aquele timbre mais sintético/robótico por
  padrão.

### Instalação adicional

As dependências de voz já estão no `requirements.txt`, então
`pip install -r requirements.txt` cobre tudo. Só um detalhe: o **PyAudio**
às vezes falha ao instalar direto via `pip` no Windows (falta de compilador
C). Se der erro na instalação dele, use:

```powershell
pip install pipwin
pipwin install pyaudio
```

Você também vai precisar permitir acesso ao microfone: **Configurações do
Windows → Privacidade e segurança → Microfone → permitir para aplicativos
de desktop**.

### Como usar

```powershell
python jarvis_voice.py
```

O terminal vai mostrar `Calibrando ruído ambiente...` (fique em silêncio
por 1-2 segundos) e depois `Pronto. Diga "Jarvis, ligar" para iniciar.`.
Fale o comando perto do microfone. Para encerrar, `Ctrl+C`.

### Personalização

No topo do `jarvis_voice.py`:

| Variável | O que ajusta |
|---|---|
| `WAKE_WORDS` / `COMMAND_WORDS` | As palavras que disparam a ação (pode adicionar variações, ex: `"executar"`, `"chefe"`) |
| `RESPONSE_TEXT` | O que o Jarvis fala ao reconhecer o comando |
| `SPEECH_RATE` | Velocidade da fala |

Para trocar a voz por uma mais robótica ainda, você pode listar as vozes
disponíveis no seu Windows e escolher outra manualmente:

```python
import pyttsx3
engine = pyttsx3.init()
for v in engine.getProperty("voices"):
    print(v.id, "-", v.name)
```

Copie o `id` da voz que quiser e defina fixo no `build_tts_engine()`
(substituindo a busca automática por português).

### Problemas comuns

- **"Erro ao acessar o microfone"** → confira as permissões de microfone do
  Windows e se o dispositivo correto está selecionado como padrão.
- **Ele nunca reconhece o comando** → fale mais perto do microfone, num
  ambiente com menos ruído, e confira no terminal o que ele está ouvindo
  (`Ouvido: "..."`) para ver se a transcrição está saindo torta.
- **"Erro ao contatar o serviço de reconhecimento de voz"** → verifique sua
  conexão com a internet; esse reconhecimento não funciona offline.
- **Ele dispara sem eu ter falado nada de relevante** → aumente a
  exigência editando `COMMAND_WORDS` para algo mais específico, ou ajuste
  `contains_wake_command` para exigir a frase exata.

---

## Próximos passos (não incluídos ainda)

1. **Wake word offline** (Porcupine ou openWakeWord) para não depender de
   internet só para detectar "Jarvis" — hoje toda escuta passa pela API do
   Google.
2. Um **LLM com tool use** decidindo, a partir do texto transcrito, qual
   ação chamar — assim dá pra ir além de "ligar tudo" e ter comandos mais
   flexíveis ("Jarvis, abre só o YouTube", "Jarvis, qual o clima?").
3. Mais ações: clima, notícias, abrir outros programas.
4. Rodar o `jarvis_voice.py` como um serviço/inicialização automática do
   Windows, para não precisar abrir o terminal manualmente toda vez.

Mas por ora, você já tem o fluxo completo funcionando de ponta a ponta:
voz → reconhecimento → ação → confirmação falada.
