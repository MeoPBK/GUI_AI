# -*- coding: utf-8 -*-
"""
Created on Tue Feb 25 17:18:00 2025

@author: meoai
"""

import requests
import openai

MAX_CONTEXT_LENGTH = 50  # Adjust as needed
HEADERS = {"Content-Type": "application/json"}
# safe words
SYS_ROLE = ("sysrole", "sys_role")
EXT = "exitnow"

class GinoChat:
    def __init__(self, max_context_length=MAX_CONTEXT_LENGTH, model="mistral", api_key=None):
        self.max_context_length = max_context_length
        self.context = []
        self.session = requests.Session()  # Persistent session for efficiency
        if "gpt" in model:
            openai.api_key = api_key  # Set the API key once when the class is instantiated
        self.data = {}

    # Update the conversation context and enforce size limits in one step.
    def update_context(self, role, content):
        if any( word in content[-1]["content"].lower() for word in SYS_ROLE) and "assistant" not in role:
            role = "system"
            for word in SYS_ROLE:
                content[-1]["content"] = content[-1]["content"].replace(word, "")
            content[-1]["content"] = content[-1]["content"].strip()

        self.context.append({"role": role, "content": content})
        self.context = self.context[-self.max_context_length:]  # Keep only the last N messages

    # Create a json structure for all models.
    def prepare_data(self, user_input, model):
        if not self.data:  # If data has not been prepared yet
            self.data = {
                "model": model,
                "prompt": user_input,
                "context": self.context  # Send full context
            }
        else:  # If data is already prepared, just update the context and prompt
            self.data['prompt'] = user_input
            self.data['context'] = self.context  # Send full context

    # Communicate with Ollama API.
    def talk_to_ollama(self, user_input, model="mistral", api_key="http://localhost:11434/api/generate"):
        self.update_context("user", user_input)
        data = self.prepare_data(user_input, model)  # Use unified data structure

        try:
            response = self.session.post(api_key, headers=HEADERS, json=data, timeout=10)
            response.raise_for_status()
            response_data = response.json()

            model_output = response_data.get('response', 'No response received.')
            self.update_context("assistant", model_output)
            return model_output

        except requests.exceptions.RequestException as e:
            return f"Ollama API Error: {e}"

    # Communicate with GPT API.    
    def talk_to_gpt(self, user_input, model="gpt-4", api_key="your_api_key_here"):
        self.update_context("user", user_input)
        data = self.prepare_data(user_input, model)  # Use unified data structure

        try:
            response = openai.ChatCompletion.create(
                model=data["model"],
                messages=data["context"]
            )

            model_output = response['choices'][0]['message']['content']
            self.update_context("assistant", model_output)
            return model_output

        except openai.error.OpenAIError as e:
            return f"OpenAI API Error: {e}"

    # Choose the model to communicate with.
    def talk_to_gino(self, user_input, model_type="ollama", url=None):
        if "deepseek"  in model_type.lower() or "ollama" in model_type.lower():
            return self.talk_to_ollama(user_input, model=model_type, ollama_url=url)
        elif "gpt" in model_type.lower():
            return self.talk_to_gpt(user_input, model=model_type, api_key=url)
        else:
            return "Error: Invalid model choice."


