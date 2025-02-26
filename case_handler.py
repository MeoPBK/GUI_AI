# -*- coding: utf-8 -*-
"""
Created on Tue Feb 25 17:18:00 2025

@author: meoai
"""

import requests
import openai
import time

MAX_CONTEXT_LENGTH = 50 #5
headers = {"Content-Type": "application/json"}
global context

def limit_context(context, max_length):
    """Limit context to a maximum number of exchanges to prevent memory overload."""
    return context[-max_length:]

# Function to interact with Ollama API
def talk_to_ollama(user_input,model,ollama_url):
    global context
    # Add the user input to the context
    context.append({"role": "user", "content": user_input})

    # Limit the context size
    context = limit_context(context, MAX_CONTEXT_LENGTH)

    # Prepare the data to send to Ollama API
    data = {
        "model": model,
        "prompt": user_input,
        "context": context  # Send the full context
    }

    try:
        # Send the POST request to the Ollama API
        response = requests.post(ollama_url, headers=headers, json=data, timeout=10)

        if response.status_code == 200:
            response_data = response.json()
            model_output = response_data['response']

            # Add the model's response to the context
            context.append({"role": "assistant", "content": model_output})

            return model_output
        else:
            return f"Error: {response.status_code}, {response.text}"

    except requests.exceptions.RequestException as e:
        # Handle network issues or API unavailability
        return f"Network error: {e}"

# Function to interact with GPT-4 API
def talk_to_gpt4(user_input,model,url):
    global context
    openai.api_key= url
    # Add the user input to the context
    context.append({"role": "user", "content": user_input})

    # Limit the context size
    context = limit_context(context, MAX_CONTEXT_LENGTH)

    # Prepare the request for GPT-4
    try:
        response = openai.ChatCompletion.create(
            model=model,  # Use GPT-4 model
            messages=context  # Send the full context for multi-turn conversation
        )

        model_output = response['choices'][0]['message']['content']

        # Add the model's response to the context
        context.append({"role": "assistant", "content": model_output})

        return model_output

    except openai.error.OpenAIError as e:
        # Handle OpenAI API errors
        return f"API error: {e}"

# Function to switch between Models
def talk_to_gino(user_input, model_type=ollama,url):
    if model_type == "ollama":
        return talk_to_ollama(user_input, model_type, url)
    elif model_type == "gpt-4":
        return talk_to_gpt4(user_input, model_type, url)
    else:
        return "Error: Invalid model choice."
    


