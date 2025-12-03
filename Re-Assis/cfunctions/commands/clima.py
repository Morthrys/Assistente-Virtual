# clima.py
# Futuramente implementar capacidade de informar previsão de demais dias
import requests
from function_reg import Registry

@Registry.command("clima", aliases=["mostrar_clima", "previsao", "previsão_do_tempo"])
def ver_clima(cidade: str, pais: str | None = None):
    try:
        cidade = cidade.strip()
        if not cidade:
            cidade = "Rio de Janeiro"

        # Obtém coordenadas da cidade
        geo_params = {
            "name": cidade,
            "count": 1,
            "language": "pt",
            "format": "json"
        }
        if pais:
            geo_params["country"] = pais

        geo_resp = requests.get("https://geocoding-api.open-meteo.com/v1/search", params=geo_params, timeout=5)
        geo_resp.raise_for_status()
        geo_data = geo_resp.json()
        
        if not geo_data.get("results"):
            mensagem = f"Não foi possível encontrar a cidade '{cidade}'"
            if pais:
                mensagem += f" no país '{pais}'."
            else:
                mensagem += "."
            print(f"Konto> {mensagem}")
            return mensagem

        loc = geo_data["results"][0]
        latitude, longitude = loc["latitude"], loc["longitude"]
        nome_cidade = loc.get("name", cidade)
        nome_pais = loc.get("country", pais or "")

        # Busca os dados meteorológicos
        clima_params = {
            "latitude": latitude,
            "longitude": longitude,
            "current_weather": True,
            "hourly": "precipitation_probability",
            "timezone": "auto"
        }

        clima_resp = requests.get("https://api.open-meteo.com/v1/forecast", params=clima_params, timeout=5)
        clima_resp.raise_for_status()
        clima_data = clima_resp.json()

        atual = clima_data.get("current_weather")
        if not atual:
            print(f"Konto> Não foi possível obter os dados do clima para '{cidade}'.")
            return

        temperatura = atual.get("temperature")
        codigo_clima = atual.get("weathercode", -1)
        descricao = _descricao_clima(codigo_clima)

        prob_chuva = None
        hourly = clima_data.get("hourly", {})
        if "precipitation_probability" in hourly:
            prob_chuva = hourly["precipitation_probability"][0]

        chuva_txt = f"Probabilidade de chuva: {prob_chuva}%" if prob_chuva is not None else "Sem previsão de chuva disponível."
        
        localizacao = f"{nome_cidade}, {nome_pais}" if nome_pais else nome_cidade
        mensagem = f"Clima em {localizacao}: {descricao}, {temperatura}°C. {chuva_txt}"

        print(f"Konto> {mensagem}")
        return mensagem

    except requests.RequestException:
        print(f"Konto> Não foi possível obter o clima para '{cidade}' no momento.")
        return


def _descricao_clima(codigo: int) -> str:
    """
    Converte código de condição climática da API em texto legível (Open-Meteo)
    """
    mapa = {
        0: "céu limpo",
        1: "parcialmente nublado",
        2: "nublado",
        3: "encoberto",
        45: "nevoeiro",
        48: "nevoeiro com geada",
        51: "chuvisco leve",
        53: "chuvisco moderado",
        55: "chuvisco intenso",
        61: "chuva leve",
        63: "chuva moderada",
        65: "chuva forte",
        80: "pancadas isoladas",
        81: "pancadas moderadas",
        82: "pancadas fortes"
    }
    return mapa.get(codigo, "condição desconhecida")
