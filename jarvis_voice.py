"""
jarvis_voice.py - Camada de voz do Jarvis
===========================================

Fica escutando o microfone em segundo plano esperando o comando de voz
"Jarvis, ligar". Quando detecta, responde falando "Iniciando senhor" (com
uma voz neural natural, via Edge TTS) e dispara as mesmas ações do
jarvis.py (abrir YouTube no monitor secundário e IntelliJ no monitor
principal).

Requer internet tanto para o reconhecimento de voz quanto para a voz
neural. Se a voz neural falhar (ex: sem internet no momento), o script
cai automaticamente para uma voz offline mais simples (SAPI5/Windows)
como alternativa, para não travar o assistente.

Veja o README.md para instalação e configuração.
"""

import argparse
import asyncio
import os
import sys
import tempfile
import threading
import time

import speech_recognition as sr
import edge_tts
import pygame

import jarvis  # reaproveita open_youtube_on_secondary / open_intellij_on_primary
import weather  # horário local e clima atual


# ==========================================================
# CONFIGURAÇÃO — edite conforme preferir
# ==========================================================

# Palavra(s) de ativação e palavra(s) de comando. O Jarvis só dispara a
# ação quando ouvir PELO MENOS uma palavra de cada lista na mesma frase.
WAKE_WORDS = ["jarvis"]
COMMAND_WORDS = ["ligar", "liga", "iniciar", "inicia", "começar", "começa", "start", "run", "está na hora"]

# Idioma usado no reconhecimento de voz.
LANGUAGE = "pt-BR"

# O que o Jarvis fala ao reconhecer o comando.
RESPONSE_TEXT = "Perfeito senhor, sistema iniciando."

# Voz neural do Edge TTS. Algumas opções em português do Brasil:
#   "pt-BR-AntonioNeural"   -> masculina
#   "pt-BR-FranciscaNeural" -> feminina
# Para ver a lista completa de vozes disponíveis, rode no terminal:
#   edge-tts --list-voices
TTS_VOICE = "pt-BR-AntonioNeural"

# Ajustes finos opcionais de tom/velocidade da voz neural.
# Formato: "+0%", "-10%", "+15%" etc.
# Pitch mais baixo (negativo) = voz mais grave/grossa.
# Rate um pouco mais lento = soa mais deliberado e imponente.
TTS_RATE = "-8%"
TTS_PITCH = "-15Hz"

# Índice do microfone a usar. Deixe None para usar o padrão do Windows.
# Se o padrão não funcionar, rode "python jarvis_voice.py --list-mics"
# para ver a lista de microfones e o número de cada um, e preencha aqui.
MIC_DEVICE_INDEX = None

# Se True, depois de "Iniciando senhor" o Jarvis também fala o horário
# atual e o clima da cidade configurada em weather.py (CITY_NAME).
ANNOUNCE_TIME_AND_WEATHER = True


# ==========================================================
# Voz (Text-to-Speech) - Edge TTS (neural, natural) com fallback offline
# ==========================================================

async def _generate_speech_async(text, output_path):
    communicate = edge_tts.Communicate(
        text, voice=TTS_VOICE, rate=TTS_RATE, pitch=TTS_PITCH
    )
    await communicate.save(output_path)


def _speak_neural(text):
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        asyncio.run(_generate_speech_async(text, tmp_path))

        pygame.mixer.init()
        pygame.mixer.music.load(tmp_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        pygame.mixer.music.unload()
        pygame.mixer.quit()
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def _speak_fallback(text):
    # Voz offline (SAPI5/Windows) usada só se a voz neural falhar
    # (ex: sem internet no momento).
    import pyttsx3

    engine = pyttsx3.init()
    engine.setProperty("rate", 165)
    engine.say(text)
    engine.runAndWait()


def speak(text):
    print(f"[Jarvis] {text}")
    try:
        _speak_neural(text)
    except Exception as exc:
        print(f"Não consegui usar a voz neural (Edge TTS): {exc}")
        print("Usando voz offline como alternativa.")
        _speak_fallback(text)


# ==========================================================
# Escuta e detecção do comando
# ==========================================================

def contains_wake_command(text):
    text = text.lower()
    has_wake = any(w in text for w in WAKE_WORDS)
    has_command = any(w in text for w in COMMAND_WORDS)
    return has_wake and has_command


def list_microphones():
    print("Microfones disponíveis:\n")
    for index, name in enumerate(sr.Microphone.list_microphone_names()):
        print(f"  [{index}] {name}")
    print(
        "\nSe o microfone padrão não funcionar, copie o número entre colchetes "
        "do dispositivo certo e defina MIC_DEVICE_INDEX no topo do arquivo "
        "jarvis_voice.py com esse número."
    )


def listen_loop():
    recognizer = sr.Recognizer()

    with sr.Microphone(device_index=MIC_DEVICE_INDEX) as source:
        print("Calibrando ruído ambiente... fique em silêncio por um instante.")
        recognizer.adjust_for_ambient_noise(source, duration=1.5)
        print('Pronto. Diga "Jarvis, ligar" para iniciar. (Ctrl+C para sair)')

        while True:
            try:
                audio = recognizer.listen(source, phrase_time_limit=5)
            except KeyboardInterrupt:
                print("\nEncerrando.")
                break

            try:
                text = recognizer.recognize_google(audio, language=LANGUAGE)
                print(f'Ouvido: "{text}"')
            except sr.UnknownValueError:
                # Não entendeu o áudio (ruído, silêncio, fala incompreensível) - ignora
                continue
            except sr.RequestError as exc:
                print(f"Erro ao contatar o serviço de reconhecimento de voz: {exc}")
                print("Verifique sua conexão com a internet.")
                time.sleep(2)
                continue

            if contains_wake_command(text):
                speak(RESPONSE_TEXT)

                # Abre os programas em segundo plano (threads), sem bloquear
                # o resto do fluxo. Isso evita que o Jarvis fique "mudo"
                # esperando o reposicionamento de janela terminar (pode
                # levar dezenas de segundos, principalmente no IntelliJ)
                # antes de conseguir falar o horário/clima.
                threading.Thread(target=jarvis.open_youtube_on_secondary, daemon=True).start()
                threading.Thread(target=jarvis.open_intellij_on_primary, daemon=True).start()

                if ANNOUNCE_TIME_AND_WEATHER:
                    speak(weather.build_status_phrase())

                print('\nPronto. Diga "Jarvis, ligar" novamente se quiser repetir.')


def main():
    parser = argparse.ArgumentParser(description="Jarvis - camada de voz")
    parser.add_argument(
        "--list-mics",
        action="store_true",
        help="Lista os microfones disponíveis no sistema e sai (não inicia a escuta).",
    )
    args = parser.parse_args()

    if args.list_mics:
        list_microphones()
        return

    try:
        listen_loop()
    except OSError as exc:
        import traceback

        print(f"Erro ao acessar o microfone: {exc}")
        print()
        print("--- Detalhe técnico completo (para diagnóstico) ---")
        traceback.print_exc()
        print("----------------------------------------------------")
        print()
        print("Isso geralmente NÃO é falta de permissão - costuma ser o PyAudio")
        print("ou o conversor FLAC (usado internamente pelo SpeechRecognition)")
        print("mal instalado / bloqueado por antivírus. Veja o README.md,")
        print('seção "Problemas comuns", para os passos de diagnóstico.')
        sys.exit(1)


if __name__ == "__main__":
    main()