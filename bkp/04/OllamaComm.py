# -*- coding: utf-8 -*-
"""
@author: meoai and iacop
"""
import requests 
import re

HEADERS = {"Content-Type": "application/json"}

OllamaData = {
        "model":  "deepseek-r1:7b", #Specifica il modello LLM che desideri utilizzare
        "prompt": "Prova" ,         #Il testo di input o la domanda che desideri inviare al LLM
        "temperature": 0.7,         #Controlla la casualità dell'output. Valori più alti (es. 1.0) rendono l'output più casuale e creativo, mentre valori più bassi (es. 0.2) lo rendono più deterministico e focalizzato
        "max_tokens": 8192,         #Specifica il numero massimo di token (parole o parti di parole) nella risposta generata
        "top_p": 1.0,               #Come compilarlo: Scegli un valore compreso tra 0.0 e 1.0. Un valore di 1.0 considera tutti i token, mentre valori più bassi considerano solo i token con probabilità più alta
        "frequency_penalty": 0.0,   #Come compilarlo: Scegli un valore compreso tra -2.0 e 2.0. Valori positivi riducono la ripetizione
        "presence_penalty": 0.0,    #Come compilarlo: Scegli un valore compreso tra -2.0 e 2.0. Valori positivi incoraggiano la diversità
        "stop": ["\n\n", "###"],    #Come compilarlo: Inserisci un array di stringhe che rappresentano le sequenze di stop. Ad esempio, ["\n\n", "###"] potrebbe indicare che il modello dovrebbe smettere di generare output quando incontra due newline o la sequenza "###"
        "stream": False             #come compilarlo: imposta a true se vuoi ricevere la risposta in parti, oppure a false se vuoi riceverla tutta in una volta
}

def clean_response(response):
    """
    Rimuove il contenuto tra i tag <think> e </think> dalla risposta.
    """
    # Usa una regex per trovare e rimuovere tutto ciò che è tra <think> e </think>
    cleaned_response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
    return cleaned_response.strip()  # Rimuove spazi bianchi extra


class OllamaPOST:
        def __init__(self):
            self.session = requests.Session()  # Persistent session for efficiency

        def talk_to_ollama(self, user_input, model="deepseek-r1:14b", api_key="http://localhost:11434"):

            OllamaData["prompt"] = user_input
            OllamaData["model"]  = model
            
            try:
                # Make the POST request
            #response = self.session.post(api_key, headers=HEADERS, json=data, timeout=10)
                response = self.session.post(api_key+"/api/generate", headers=HEADERS, json=OllamaData)
                response.raise_for_status()
                response_data = response.json()
                model_output = response_data.get('response', 'No response received.')
                cleaned_output = clean_response(model_output)
                return cleaned_output
            
            except requests.exceptions.RequestException as e:
                return f"API Error: {e}"

class GetAvailableModels:
        def __init__(self):
            self.session = requests.Session()  # Persistent session for efficiency

        def get_ollama_models(self, api_key="http://localhost:11434"):
            try:
                response = self.session.get(api_key+"/api/tags")
                models_data = response.json()
                # Extract model names from the response
                models = [model['name'] for model in models_data['models']]
                return models
            except requests.exceptions.RequestException as e:
                return []
            