# -*- coding: utf-8 -*-
"""
Created on Tue Feb 25 17:36:30 2025

@author: meoai
"""
import requests
import openai
global context
from my_model import GinoChat

OLLAMA_URL = "https://3b2b-93-35-170-99.ngrok-free.app/api/generate"
GPT_URL = "your_openai_api_key_here"  # Set your OpenAI API key
MODEL =  "mistral" # "deepseek-r1:14b" #"deepseek-r1:32b" # "mistral" "gpt-4" "gpt-3.5-turbo" "gpt-3.5-turbo-davinci" "gpt-3.5-turbo-codex" "gpt-3.5-turbo-codex-davinci"

context = ["You are a useful assistant that answers my questions!",
           "You are a deeplearning, machine learning and control engineer.",
           "Always double check your sources, quote them and base your conclusions on scientific papers"]

gino = GinoChat(api_key=OLLAMA_URL)  # Pass API key at initialization

while True:
    user_input = input("You: ")

    model_response = gino.talk_to_gino(user_input, model_type=MODEL, url=OLLAMA_URL)
    print("Model:", model_response)
    
gino.close()
