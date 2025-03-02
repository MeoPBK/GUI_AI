# -*- coding: utf-8 -*-
"""
@author: meoai and iacop
"""
import requests 
import re

HEADERS = {"Content-Type": "application/json"}

OllamaData = {
        "model":  "deepseek-r1:14b",
        "prompt": "Prova" ,
        "stream": False
}

def clean_response(response):
    """
    Rimuove il contenuto tra i tag <think> e </think> dalla risposta.
    """
    # Usa una regex per trovare e rimuovere tutto ciò che è tra <think> e </think>
    cleaned_response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
    return cleaned_response.strip()  # Rimuove spazi bianchi extra


class GinoeasyChat:
        def __init__(self):
            self.session = requests.Session()  # Persistent session for efficiency

        def talk_to_ollama(self, user_input, model="deepseek-r1:14b", api_key="http://localhost:11434/api/generate"):

            OllamaData["prompt"] = user_input
            OllamaData["model"]  = model
            
            try:
                # Make the POST request
            #response = self.session.post(api_key, headers=HEADERS, json=data, timeout=10)
                response = self.session.post(api_key, headers=HEADERS, json=OllamaData)
                response.raise_for_status()
                response_data = response.json()
                model_output = response_data.get('response', 'No response received.')
                cleaned_output = clean_response(model_output)
                return cleaned_output
            
            except requests.exceptions.RequestException as e:
                return f"API Error: {e}"
