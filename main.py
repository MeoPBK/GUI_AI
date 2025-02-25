# -*- coding: utf-8 -*-
"""
Created on Tue Feb 25 17:36:30 2025

@author: meoai
"""
import requests
import openai
import case_handler
global context

OLLAMA_URL = "https://c6e7-93-35-170-99.ngrok-free.app/api/generate"
openai.api_key = "your_openai_api_key_here"  # Set your OpenAI API key

MODEL =   "deepseek-r1:14b"#"mistral"  # Ollama model, change to GPT-4 for OpenAI
context = []
MAX_CONTEXT_LENGTH = 50 #5

ext = "exitnow" 
sys_role = "sysrole"  # how do i make it better??
   
while True:
    user_input = input("You: ")
        
    if sys_role in user_input.lower():     
        context.append({"role": "system", "content": user_input})
    else:
        context.append({"role": "user", "content": user_input})
    

    reply = response["choices"][0]["message"]["content"]
    
    context.append({"role": "assistant", "content": reply})
    
    print("GINO:", talk_to_gino(user_input, model_type="ollama",OLLAMA_URL)
    
    if ext in user_input.lower() :
        messages.append({"role": "system", "content": user_input})
        break
    
