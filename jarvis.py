"""
Jarvis - Protótipo inicial de assistente de automação (Windows)
=================================================================

O que este script faz, na ordem:
  1. Detecta os monitores conectados (principal e secundário).
  2. Abre uma NOVA janela do navegador direto num vídeo do YouTube
     e move essa janela para o monitor secundário.
  3. Abre o IntelliJ IDEA e move a janela dele para o monitor principal,
     maximizada.

Este é só o esqueleto de "mecânica" (abrir programas e posicionar
janelas). Ainda não tem reconhecimento de voz - isso vem depois.

Veja o README.md para instruções de instalação e configuração.
"""

import os
import subprocess
import sys
import time
import argparse
import urllib.parse
from pathlib import Path

try:
    import pygetwindow as gw
except ImportError:
    print("Erro: a biblioteca 'pygetwindow' não está instalada.")
    print("Rode: pip install -r requirements.txt")
    sys.exit(1)

try:
    from screeninfo import get_monitors
except ImportError:
    print("Erro: a biblioteca 'screeninfo' não está instalada.")
    print("Rode: pip install -r requirements.txt")
    sys.exit(1)


# ==========================================================
# CONFIGURAÇÃO — edite estas variáveis conforme o seu ambiente
# ==========================================================

# Caminho completo do executável do IntelliJ IDEA.
# Abra o IntelliJ, vá em Help > About, ou procure a pasta de instalação
# em "C:\Program Files\JetBrains\..." e ajuste a versão abaixo.
INTELLIJ_PATH = r"C:\Users\kamodares\AppData\Local\Programs\IntelliJ IDEA 2026.1.4\bin\idea64.exe"

# Caminho do navegador. Deixe None para o script tentar detectar
# automaticamente (Chrome, Edge ou Opera nos locais padrão de instalação).
BROWSER_PATH = r"C:\Users\kamodares\AppData\Local\Programs\Opera GX\opera.exe"

# URL que deve abrir no YouTube.
# OBS: "Iron Man" é do Black Sabbath, não do Iron Maiden (são bandas
# diferentes). Deixei o clipe oficial do Black Sabbath como padrão.
# Troque pela URL que você quiser (ex: uma música do Iron Maiden).
YOUTUBE_VIDEO_URL = "https://www.youtube.com/watch?v=7ZuoM3Ivgt0"

# URL que deve abrir no comando "Jarvis, Alura".
ALURA_URL = "https://cursos.alura.com.br/loginForm?urlAfterLogin=https%3A%2F%2Fcursos.alura.com.br%2Fclasspage%2Fjava-trabalhando-lambdas-streams-spring-framework%2Ftask%2F135646"

# ----------------------------------------------------------
# Busca de vagas no LinkedIn ("Jarvis, envie meu currículo")
# ----------------------------------------------------------
# IMPORTANTE: isso NÃO clica em "Candidatura simplificada" automaticamente.
# Automatizar candidaturas em massa viola os Termos de Uso do LinkedIn e
# pode suspender sua conta. O que este comando faz é abrir a busca de
# vagas já FILTRADA pelos critérios abaixo, em duas abas (vagas locais e
# vagas remotas) - você revisa e se candidata manualmente nas que fizerem
# sentido.

# Nível de senioridade + área/tecnologia desejada, no formato de busca
# booleana que o LinkedIn aceita (AND / OR / aspas para frase exata).
LINKEDIN_KEYWORDS = (
    '(Estágio OR Júnior OR Técnico) AND '
    '(TI OR "Desenvolvedor Backend" OR "Desenvolvedor Fullstack" OR '
    '"Help Desk" OR "Suporte de TI" OR Java OR C# OR Python OR '
    'JavaScript OR TypeScript)'
)

# Localização usada na busca presencial/híbrida.
LINKEDIN_LOCAL_LOCATION = "São Paulo, Brazil"

# Raio de distância (em km) a partir de LINKEDIN_LOCAL_LOCATION, para
# incluir cidades próximas (Grande São Paulo). Valores comuns aceitos
# pelo LinkedIn: 8, 16, 40, 80, 160.
LINKEDIN_LOCAL_DISTANCE_KM = 40

# Códigos de nível de experiência do LinkedIn (parâmetro f_E):
#   1 = Estágio | 2 = Júnior (Entry level) | 3 = Pleno/Técnico (Associate)
LINKEDIN_EXPERIENCE_LEVELS = [1, 2, 3]

# Códigos de modelo de trabalho do LinkedIn (parâmetro f_WT):
#   1 = Presencial | 2 = Remoto | 3 = Híbrido
LINKEDIN_LOCAL_WORKPLACE_TYPES = [1, 3]  # presencial + híbrido, perto de SP
LINKEDIN_REMOTE_WORKPLACE_TYPES = [2]  # remoto, sem restrição de local

# ----------------------------------------------------------
# Desligar o computador ("Jarvis, encerrar por hoje")
# ----------------------------------------------------------
# Tempo de espera (segundos) entre o comando de voz e o desligamento de
# fato. Dá tempo de cancelar (dizendo "Jarvis, cancelar") caso o
# reconhecimento de voz tenha entendido errado, ou caso você tenha algo
# não salvo em algum programa.
SHUTDOWN_DELAY_SECONDS = 25

# Posição do monitor secundário em relação ao principal: "left" ou "right".
# Isso só é usado como critério de desempate caso o Windows não informe
# claramente qual monitor é qual - normalmente a detecção automática
# por coordenadas já resolve isso sozinha.
SECONDARY_MONITOR_SIDE = "left"

# Tempo máximo (segundos) esperando cada janela abrir.
WINDOW_WAIT_TIMEOUT = 20


# ==========================================================
# Detecção de monitores
# ==========================================================

def get_primary_and_secondary_monitors():
    """Retorna (monitor_principal, monitor_secundario).

    Se só houver um monitor, retorna o mesmo monitor duas vezes.
    """
    monitors = get_monitors()
    primary = next((m for m in monitors if m.is_primary), monitors[0])
    secondary_candidates = [m for m in monitors if m is not primary]

    if not secondary_candidates:
        print("Aviso: apenas um monitor detectado. Usando o mesmo monitor para tudo.")
        return primary, primary

    if len(secondary_candidates) > 1:
        # Mais de dois monitores: escolhe o que está do lado configurado.
        if SECONDARY_MONITOR_SIDE == "left":
            secondary_candidates.sort(key=lambda m: m.x)
        else:
            secondary_candidates.sort(key=lambda m: -m.x)

    secondary = secondary_candidates[0]
    return primary, secondary


# ==========================================================
# Utilitários de navegador / janelas
# ==========================================================

def find_browser_path():
    if BROWSER_PATH:
        if not Path(BROWSER_PATH).exists():
            print(f"Aviso: BROWSER_PATH está definido, mas o arquivo não existe: {BROWSER_PATH}")
            print("Corrija o caminho ou defina BROWSER_PATH = None para detecção automática.")
            return None
        return BROWSER_PATH

    local_appdata = os.environ.get("LOCALAPPDATA", "")

    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]

    if local_appdata:
        candidates += [
            str(Path(local_appdata) / "Programs" / "Opera GX" / "Launcher.exe"),
            str(Path(local_appdata) / "Programs" / "Opera" / "launcher.exe"),
        ]

    for path in candidates:
        if Path(path).exists():
            return path
    return None


def wait_for_window(title_contains, timeout=WINDOW_WAIT_TIMEOUT):
    """Espera até aparecer uma janela cujo título contenha o texto dado."""
    elapsed = 0.0
    interval = 0.5
    while elapsed < timeout:
        all_titles = [t for t in gw.getAllTitles() if t.strip()]
        match = next((t for t in all_titles if title_contains.lower() in t.lower()), None)
        if match:
            windows = gw.getWindowsWithTitle(match)
            if windows:
                return windows[0]
        time.sleep(interval)
        elapsed += interval
    return None


def move_window_to_monitor(window, monitor):
    try:
        window.restore()
    except Exception:
        pass
    time.sleep(0.3)
    try:
        window.moveTo(monitor.x, monitor.y)
        window.resizeTo(monitor.width, monitor.height)
    except Exception as exc:
        print(f"Não consegui mover/redimensionar a janela automaticamente: {exc}")


# ==========================================================
# Ações
# ==========================================================

def open_url_on_secondary(urls, window_title_hint=None):
    """Abre uma ou mais URLs em uma nova janela do navegador (cada URL extra
    vira uma aba na mesma janela), movida para o monitor secundário.

    urls: uma única URL (str) ou uma lista de URLs (list[str]).
    window_title_hint: um texto que costuma aparecer no título da aba/janela
    (ex: "YouTube", "Alura", "LinkedIn") para ajudar a encontrar a janela
    mais rápido. Opcional - se não achar por esse texto, tenta pelo nome
    do navegador.
    """
    if isinstance(urls, str):
        urls = [urls]

    primary, secondary = get_primary_and_secondary_monitors()
    browser_path = find_browser_path()

    if not browser_path:
        print("Não encontrei Chrome, Edge nem Opera nos caminhos padrão.")
        print("Edite a variável BROWSER_PATH no topo do arquivo com o caminho real do seu navegador.")
        return

    print(f"Abrindo navegador em nova janela: {browser_path}")
    subprocess.Popen([browser_path, "--new-window"] + urls)

    print("Aguardando a janela do navegador abrir...")
    window = None
    if window_title_hint:
        window = wait_for_window(window_title_hint)
    window = (
        window
        or wait_for_window("Opera")
        or wait_for_window("Chrome")
        or wait_for_window("Edge")
    )

    if window is None:
        print("Não consegui localizar a janela do navegador automaticamente.")
        print("A página deve ter aberto mesmo assim - mova-a manualmente se precisar.")
        return

    print(f"Movendo janela para o monitor secundário ({SECONDARY_MONITOR_SIDE})...")
    move_window_to_monitor(window, secondary)
    print("Pronto! Site aberto no monitor secundário.")


def open_youtube_on_secondary():
    open_url_on_secondary(YOUTUBE_VIDEO_URL, window_title_hint="YouTube")


def open_alura_on_secondary():
    open_url_on_secondary(ALURA_URL, window_title_hint="Alura")


def _build_linkedin_job_search_url(keywords, location=None, workplace_types=None,
                                    experience_levels=None, distance_km=None):
    params = {"keywords": keywords}
    if location:
        params["location"] = location
    if workplace_types:
        params["f_WT"] = ",".join(str(x) for x in workplace_types)
    if experience_levels:
        params["f_E"] = ",".join(str(x) for x in experience_levels)
    if distance_km:
        params["distance"] = str(distance_km)

    query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    return f"https://www.linkedin.com/jobs/search/?{query}"


def open_linkedin_job_search_on_secondary():
    """Abre duas abas no LinkedIn: vagas locais (SP e região) e vagas remotas.

    NÃO clica em nenhuma vaga nem envia candidaturas - só monta a busca já
    filtrada. Depende de você já estar logado no LinkedIn no navegador
    configurado (BROWSER_PATH).
    """
    local_url = _build_linkedin_job_search_url(
        keywords=LINKEDIN_KEYWORDS,
        location=LINKEDIN_LOCAL_LOCATION,
        workplace_types=LINKEDIN_LOCAL_WORKPLACE_TYPES,
        experience_levels=LINKEDIN_EXPERIENCE_LEVELS,
        distance_km=LINKEDIN_LOCAL_DISTANCE_KM,
    )
    remote_url = _build_linkedin_job_search_url(
        keywords=LINKEDIN_KEYWORDS,
        workplace_types=LINKEDIN_REMOTE_WORKPLACE_TYPES,
        experience_levels=LINKEDIN_EXPERIENCE_LEVELS,
    )

    print("Abrindo busca de vagas no LinkedIn (local + remoto)...")
    open_url_on_secondary([local_url, remote_url], window_title_hint="LinkedIn")


def shutdown_computer(delay_seconds=SHUTDOWN_DELAY_SECONDS):
    """Agenda o desligamento do Windows daqui a `delay_seconds` segundos.

    Usa o comando nativo `shutdown /s /t <segundos>` do Windows. O
    desligamento agendado pode ser cancelado a qualquer momento (dentro do
    prazo) com cancel_shutdown() - por voz, "Jarvis, cancelar".
    """
    print(f"Agendando desligamento do Windows em {delay_seconds} segundos...")
    try:
        subprocess.run(
            ["shutdown", "/s", "/t", str(delay_seconds)],
            capture_output=True,
            text=True,
            check=True,
        )
        print("Desligamento agendado com sucesso.")
    except subprocess.CalledProcessError as exc:
        print(f"Não consegui agendar o desligamento: {exc.stderr or exc}")
    except FileNotFoundError:
        print("Comando 'shutdown' não encontrado - isso só funciona no Windows.")


def cancel_shutdown():
    """Cancela um desligamento agendado, se houver algum pendente."""
    print("Tentando cancelar desligamento agendado...")
    try:
        subprocess.run(
            ["shutdown", "/a"],
            capture_output=True,
            text=True,
            check=True,
        )
        print("Desligamento cancelado com sucesso.")
    except subprocess.CalledProcessError:
        print("Não havia nenhum desligamento agendado para cancelar (ou já era tarde demais).")
    except FileNotFoundError:
        print("Comando 'shutdown' não encontrado - isso só funciona no Windows.")


def open_intellij_on_primary():
    primary, secondary = get_primary_and_secondary_monitors()

    if not Path(INTELLIJ_PATH).exists():
        print(f"Não encontrei o IntelliJ IDEA em: {INTELLIJ_PATH}")
        print("Edite a variável INTELLIJ_PATH no topo do arquivo com o caminho correto.")
        return

    print(f"Abrindo IntelliJ IDEA: {INTELLIJ_PATH}")
    subprocess.Popen([INTELLIJ_PATH])

    print("Aguardando a janela do IntelliJ abrir (pode demorar, ele é pesado)...")
    window = wait_for_window("IntelliJ IDEA", timeout=max(WINDOW_WAIT_TIMEOUT, 40))

    if window is None:
        print("Não consegui localizar a janela do IntelliJ automaticamente.")
        print("Ele deve estar abrindo mesmo assim - mova-o manualmente se precisar.")
        return

    print("Movendo janela para o monitor principal e maximizando...")
    move_window_to_monitor(window, primary)
    try:
        window.maximize()
    except Exception:
        pass
    print("Pronto! IntelliJ aberto no monitor principal.")


# ==========================================================
# Ponto de entrada
# ==========================================================

def main():
    parser = argparse.ArgumentParser(
        description="Jarvis - protótipo de automação (abrir YouTube/Alura e IntelliJ)"
    )
    parser.add_argument(
        "acao",
        nargs="?",
        default="tudo",
        choices=["youtube", "alura", "linkedin", "intellij", "shutdown", "cancelar", "tudo"],
        help=(
            "O que executar: youtube, alura, linkedin, intellij, shutdown, "
            "cancelar ou tudo (padrão: tudo = youtube + intellij)"
        ),
    )
    args = parser.parse_args()

    if args.acao in ("youtube", "tudo"):
        open_youtube_on_secondary()

    if args.acao == "alura":
        open_alura_on_secondary()

    if args.acao == "linkedin":
        open_linkedin_job_search_on_secondary()

    if args.acao == "shutdown":
        shutdown_computer()

    if args.acao == "cancelar":
        cancel_shutdown()

    if args.acao in ("intellij", "tudo", "alura"):
        open_intellij_on_primary()


if __name__ == "__main__":
    main()