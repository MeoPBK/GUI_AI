from flask import Flask, render_template
from flask_socketio import SocketIO, send, emit
from OllamaComm import OllamaPOST

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sdifjansovkjdsnfvasnxlvmnskdjknvsv'
socketio = SocketIO(app)

# Ollama API configuration
OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "deepseek-r1:7b"  # Default model to use

# Store chat messages
chat_messages = []

# Initialize the Ollama communication instances
Ollama = OllamaPOST()
OllamaModels = OllamaPOST()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('get_available_models')
def handle_get_models(data=None):
    """Send available models to the client when requested"""
    # If data is provided, use the address from data, otherwise use default
    address = data.get('address', OLLAMA_URL) if data else OLLAMA_URL
    
    try:
        # Get models from the specified address
        models = OllamaModels.get_ollama_models(address)
        emit('available_models', {
            'models': models,
            'default_model': DEFAULT_MODEL
        })
        
        # Send system message about successful connection
        send({"sender": "system", "message": f"Connected to Ollama at {address}"}, broadcast=True)
    except Exception as e:
        # Send error message if models can't be fetched
        error_msg = f"Failed to connect to Ollama at {address}: {str(e)}"
        send({"sender": "system", "message": error_msg}, broadcast=True)
        # Still emit available_models but with empty list to avoid client errors
        emit('available_models', {
            'models': [],
            'default_model': DEFAULT_MODEL
        })

@socketio.on('change_address')
def handle_change_address(data):
    """Handle changing the Ollama server address"""
    address = data.get('address', OLLAMA_URL)
    
    try:
        # Get models from the new address
        models = OllamaModels.get_ollama_models(address)
        emit('available_models', {
            'models': models,
            'default_model': DEFAULT_MODEL
        })
        
        # Send success message
        success_msg = f"Successfully connected to Ollama at {address}"
        send({"sender": "system", "message": success_msg}, broadcast=True)
    except Exception as e:
        # Send error message
        error_msg = f"Failed to connect to Ollama at {address}: {str(e)}"
        send({"sender": "system", "message": error_msg}, broadcast=True)

@socketio.on('change_model')
def handle_change_model(data):
    """Handle changing the model"""
    model = data.get('model', DEFAULT_MODEL)
    address = data.get('address', OLLAMA_URL)
    
    # Send confirmation message
    #send({"sender": "system", "message": f"Model changed to {model}"}, broadcast=True)

@socketio.on('send_message')
def handle_send_message(data):
    """Handle sending a message and getting the model's response."""
    user_message = data['message']
    model = data.get('model', DEFAULT_MODEL)
    address = data.get('address', OLLAMA_URL)

    # Store the user's message in the chat history
    chat_messages.append({"sender": "user", "message": user_message})

    # Broadcast the user's message to all clients
    send({"sender": "user", "message": user_message}, broadcast=True)

    try:
        # Get the model's response using Ollama
        model_response = Ollama.talk_to_ollama(user_message, model, address)

        # Store the model's response in the chat history
        chat_messages.append({"sender": "ai", "message": model_response})

        # Broadcast the model's response to all clients
        send({"sender": "ai", "message": model_response}, broadcast=True)
    except Exception as e:
        # Send error message if response fails
        error_msg = f"Error getting response from {model}: {str(e)}"
        send({"sender": "system", "message": error_msg}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

## TTRYY