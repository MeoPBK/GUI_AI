<<<<<<< HEAD
from flask import Flask, render_template
from flask_socketio import SocketIO, send, emit
from OllamaComm import OllamaPOST, GetAvailableModels

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sdifjansovkjdsnfvasnxlvmnskdjknvsv'
socketio = SocketIO(app)

# Ollama API configuration
DEFAULT_OLLAMA_URL = "http://localhost:11434"
MODEL = "deepseek-r1:7b"  # Replace with your desired model

# Store chat messages
chat_messages = []

# Initialize the GinoeasyChat instance
Ollama = OllamaPOST()
OllamaModels = GetAvailableModels()

# Chat Start
@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('get_available_models')
def handle_get_models():
    """Send available models to the client when requested"""
    # Use the default address initially
    models = OllamaModels.get_ollama_models(DEFAULT_OLLAMA_URL)
    emit('available_models', {
        'models': models,
        'default_model': MODEL
    })


@socketio.on('send_message')
def handle_send_message(data):
    """Handle sending a message and getting the model's response."""
    user_message = data['message']
    model = data['model']
    
    # Get the address from the data, use default if not provided
    address = data.get('address')
    if not address or address.strip() == "":
        address = DEFAULT_OLLAMA_URL
    
    # Store the user's message in the chat history
    chat_messages.append({"sender": "user", "message": user_message})

    # Broadcast the user's message to all clients
    send({"sender": "user", "message": user_message}, broadcast=True)

    # Get the model's response using the specified address
    model_response = Ollama.talk_to_ollama(user_message, model, address)

    # Store the model's response in the chat history
    chat_messages.append({"sender": "ai", "message": model_response})

    # Broadcast the model's response to all clients
    send({"sender": "ai", "message": model_response}, broadcast=True)


@socketio.on('change_address')
def handle_change_address(data):
    """Handle address change and verify if the server is reachable"""
    address = data.get('address')
    if not address or address.strip() == "":
        address = DEFAULT_OLLAMA_URL
    
    try:
        # Try to get models from the new address to verify it's working
        models = OllamaModels.get_ollama_models(address)
        emit('available_models', {
            'models': models,
            'default_model': data.get('model', MODEL)
        })
        
        # Send confirmation to the client
        send({"sender": "system", "message": f"Successfully connected to Ollama at {address}"})
    except Exception as e:
        # If there's an error, send an error message
        error_msg = f"Could not connect to Ollama at {address}. Error: {str(e)}"
        send({"sender": "system", "message": error_msg})


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
=======
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
>>>>>>> 7aee24f7180c9db72bda11a7f601bb3a73a93886
