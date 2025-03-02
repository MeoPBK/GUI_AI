<<<<<<< HEAD
from flask import Flask, render_template
from flask_socketio import SocketIO, send, emit
from OllamaComm import OllamaPOST, GetAvailableModels

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

# Ollama API configuration
OLLAMA_URL = "https://277c-93-35-170-99.ngrok-free.app"
MODEL = "deepseek-r1:7b"  # Replace with your desired model

# Store chat messages
chat_messages = []

# Initialize the GinoeasyChat instance
Ollama = OllamaPOST()
OllamaModels = GetAvailableModels()

# Get the ollama available models
models = OllamaModels.get_ollama_models(OLLAMA_URL)





# Chat Start
@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('get_available_models')
def handle_get_models():
    """Send available models to the client when requested"""
    emit('available_models', {
        'models': models,
        'default_model': MODEL
    })

@socketio.on('send_message')
def handle_send_message(data):
    """Handle sending a message and getting the model's response."""
    user_message = data['message']
    model        = data['model']

    # Store the user's message in the chat history
    chat_messages.append({"sender": "user", "message": user_message})

    # Broadcast the user's message to all clients
    send({"sender": "user", "message": user_message}, broadcast=True)

    # Get the model's response using GinoeasyChat
    model_response = Ollama.talk_to_ollama(user_message, model, OLLAMA_URL)

    # Store the model's response in the chat history
    chat_messages.append({"sender": "ai", "message": model_response})

    # Broadcast the model's response to all clients
    send({"sender": "ai", "message": model_response}, broadcast=True)

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
