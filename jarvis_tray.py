"""
jarvis_tray.py - Jarvis rodando em segundo plano com ícone na bandeja
=========================================================================

Este é o ponto de entrada pensado para uso do dia a dia: ao rodar (via
pythonw.exe, sem console visível), o Jarvis fica ouvindo o microfone em
segundo plano e mostra um ícone na bandeja do sistema (perto do relógio
do Windows) indicando que está ativo. Pelo ícone dá pra encerrar o
programa quando quiser.

Veja o README.md, seção "Virando um aplicativo", para instruções
completas de como deixar isso iniciando automaticamente com o Windows.
"""

import os
import sys

# Quando rodado sem console (pythonw.exe, ou um .exe empacotado com
# --windowed), sys.stdout/stderr podem ser None. Qualquer print() nessa
# condição derrubaria o programa - substituímos por um "buraco negro"
# para evitar isso. Precisa vir ANTES de importar jarvis_voice, que usa
# print() para status.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

import threading

from PIL import Image, ImageDraw
import pystray

import jarvis_voice as jv


PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(PROJECT_DIR, "jarvis_error.log")


def build_icon_image():
    # Ícone gerado na hora (um círculo azul com "J"), para não depender
    # de um arquivo .ico externo.
    size = 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((4, 4, size - 4, size - 4), fill=(30, 144, 255, 255))
    draw.text((22, 16), "J", fill=(255, 255, 255, 255))
    return image


def log_error(exc):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{exc}\n")


def run_listener():
    try:
        jv.listen_loop()
    except Exception as exc:
        # Sem console visível, um erro aqui não aparece em lugar nenhum -
        # registramos num arquivo de log para dar pra investigar depois.
        log_error(exc)


def on_quit(icon, item):
    icon.stop()
    os._exit(0)  # encerra o processo inteiro, incluindo a thread de escuta


def main():
    listener_thread = threading.Thread(target=run_listener, daemon=True)
    listener_thread.start()

    icon = pystray.Icon(
        "jarvis",
        build_icon_image(),
        "Jarvis (ouvindo)",
        menu=pystray.Menu(
            pystray.MenuItem("Jarvis está ativo e ouvindo", None, enabled=False),
            pystray.MenuItem("Sair", on_quit),
        ),
    )
    icon.run()


if __name__ == "__main__":
    main()