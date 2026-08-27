"""
weather.py - Horário local e clima atual (Jarvis)
=====================================================

Consulta o clima atual de uma cidade/endereço usando a API pública e
gratuita do Open-Meteo (não precisa de chave de API/cadastro):
  - Geocodificação: converte o nome da cidade em latitude/longitude.
  - Previsão: busca temperatura e condição do tempo atuais para essas
    coordenadas.

Também monta a frase de horário local (com base no relógio do próprio
computador).
"""

import datetime

import requests


# ==========================================================
# CONFIGURAÇÃO
# ==========================================================

# Endereço/cidade usado para localizar o clima. Pode ser algo genérico
# como "São Paulo, SP" ou mais específico como "Avenida Paulista, São
# Paulo" - a geocodificação do Open-Meteo tenta encontrar o lugar mais
# próximo do texto informado.
CITY_NAME = "São Paulo, SP"


# Tradução dos códigos de clima (WMO) usados pelo Open-Meteo.
WEATHER_CODE_DESCRIPTIONS = {
    0: "com céu limpo",
    1: "com poucas nuvens",
    2: "parcialmente nublado",
    3: "nublado",
    45: "com neblina",
    48: "com neblina e geada",
    51: "com garoa fraca",
    53: "com garoa moderada",
    55: "com garoa forte",
    56: "com garoa congelante fraca",
    57: "com garoa congelante forte",
    61: "com chuva fraca",
    63: "com chuva moderada",
    65: "com chuva forte",
    66: "com chuva congelante fraca",
    67: "com chuva congelante forte",
    71: "com neve fraca",
    73: "com neve moderada",
    75: "com neve forte",
    77: "com grãos de neve",
    80: "com pancadas de chuva fracas",
    81: "com pancadas de chuva moderadas",
    82: "com pancadas de chuva fortes",
    85: "com pancadas de neve fracas",
    86: "com pancadas de neve fortes",
    95: "com trovoadas",
    96: "com trovoadas e granizo fraco",
    99: "com trovoadas e granizo forte",
}

# Cache simples: evita geocodificar de novo a cada chamada na mesma sessão.
# Já vem pré-preenchido para a cidade padrão (São Paulo, SP), o que evita
# uma chamada de rede extra de geocodificação e deixa a resposta mais rápida.
_coords_cache = {
    "São Paulo, SP": (-23.5505, -46.6333, "America/Sao_Paulo"),
}


# ==========================================================
# Geocodificação e clima
# ==========================================================

def geocode_city(city_name):
    """Converte um nome de cidade/endereço em (latitude, longitude, timezone)."""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city_name, "count": 1, "language": "pt", "format": "json"}
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    results = data.get("results")
    if not results:
        raise ValueError(f"Não encontrei coordenadas para '{city_name}'.")

    place = results[0]
    return place["latitude"], place["longitude"], place.get("timezone", "auto")


def get_current_weather(city_name=CITY_NAME):
    """Retorna um dicionário com temperatura, sensação e condição atuais."""
    if city_name not in _coords_cache:
        _coords_cache[city_name] = geocode_city(city_name)
    lat, lon, tz = _coords_cache[city_name]

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,apparent_temperature,weather_code,relative_humidity_2m",
        "timezone": tz,
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    current = data["current"]

    return {
        "temperature": current["temperature_2m"],
        "feels_like": current["apparent_temperature"],
        "humidity": current["relative_humidity_2m"],
        "condition": WEATHER_CODE_DESCRIPTIONS.get(
            current["weather_code"], "condição de tempo desconhecida"
        ),
    }


# ==========================================================
# Horário
# ==========================================================

def get_time_phrase():
    """Monta a frase de horário atual (relógio do próprio computador)."""
    now = datetime.datetime.now()
    hour = now.hour
    minute = now.minute
    if minute == 0:
        return f"{hour} horas"
    return f"{hour} horas e {minute} minutos"


# ==========================================================
# Frase final combinando horário + clima
# ==========================================================

def build_status_phrase(city_name=CITY_NAME):
    """Monta a frase completa a ser falada: horário e clima atuais."""
    time_phrase = get_time_phrase()

    try:
        weather = get_current_weather(city_name)
        temperature = round(weather["temperature"])
        return (
            f"Agora são {time_phrase} em {city_name}. "
            f"A temperatura está em {temperature} graus, e o clima está {weather['condition']}."
        )
    except Exception as exc:
        print(f"[Jarvis] Não consegui buscar o clima: {exc}")
        return f"Agora são {time_phrase}. Não consegui obter os dados de clima no momento."


if __name__ == "__main__":
    # Teste rápido: "python weather.py" imprime a frase montada.
    print(build_status_phrase())