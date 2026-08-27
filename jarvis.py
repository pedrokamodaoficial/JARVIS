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
YOUTUBE_VIDEO_URL = "https://www.youtube.com/watch?v=b3-QqGVt-tM&list=RDb3-QqGVt-tM&start_radio=1&pp=ygUWaXJvbiBtYW4gYmxhY2sgc2FiYmF0aKAHAQ%3D%3D"

# URL que deve abrir no comando "Jarvis, Alura".
ALURA_URL = "https://cursos.alura.com.br/loginForm?urlAfterLogin=https%3A%2F%2Fcursos.alura.com.br%2Fclasspage%2Fjava-trabalhando-lambdas-streams-spring-framework%2Ftask%2F135646"

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

def open_url_on_secondary(url, window_title_hint=None):
    """Abre uma URL em uma nova janela do navegador, no monitor secundário.

    window_title_hint: um texto que costuma aparecer no título da aba/janela
    (ex: "YouTube", "Alura") para ajudar a encontrar a janela mais rápido.
    Opcional - se não achar por esse texto, tenta pelo nome do navegador.
    """
    primary, secondary = get_primary_and_secondary_monitors()
    browser_path = find_browser_path()

    if not browser_path:
        print("Não encontrei Chrome, Edge nem Opera nos caminhos padrão.")
        print("Edite a variável BROWSER_PATH no topo do arquivo com o caminho real do seu navegador.")
        return

    print(f"Abrindo navegador em nova janela: {browser_path}")
    subprocess.Popen([browser_path, "--new-window", url])

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
        choices=["youtube", "alura", "intellij", "tudo"],
        help="O que executar: youtube, alura, intellij ou tudo (padrão: tudo = youtube + intellij)",
    )
    args = parser.parse_args()

    if args.acao in ("youtube", "tudo"):
        open_youtube_on_secondary()

    if args.acao == "alura":
        open_alura_on_secondary()

    if args.acao in ("intellij", "tudo", "alura"):
        open_intellij_on_primary()


if __name__ == "__main__":
    main()