# -*- coding: utf-8 -*-
"""
@author: meoai and iacop
"""
import requests 

# URL to send in the POST request
OLLAMA_URL = "https://3b2b-93-35-170-99.ngrok-free.app/api/generate"
# URL to send in the GET request
# OLLAMA_URL_GET = "https://c6e7-93-35-170-99.ngrok-free.app"

MODEL = "mistral"
headers = {"Content-Type": "application/json"}
PROMPT = "invent a story about an horse named JusyPani"

# Data to send in the POST request
data = {
    "model": MODEL,
    "prompt": PROMPT,
    "stream": False
}

#request, just for debugging
#try:
#    response = requests.get(OLLAMA_URL_GET)
#    if response.status_code == 200:
#        print("Server is up and running!")
#    else:
#        print(f"Error: {response.status_code}, {response.text}")
#except Exception as e:
#    print(f"An error occurred: {e}")
    
try:
    # Make the POST request
    response = requests.post(OLLAMA_URL, headers=headers, json=data)

    # If the response is successful, print it
    if response.status_code == 200:
        response_data = response.json()
        print("Model Response:", response_data['response'])
    else:
        print(f"Error: {response.status_code}, {response.text}")
except Exception as e:
    print(f"Error occurred: {e}")
    