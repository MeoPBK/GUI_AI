from flask import Flask, render_template
from flask_socketio import SocketIO, send, emit
from OllamaComm import OllamaPOST, GetAvailableModels

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sdifjansovkjdsnfvasnxlvmnskdjknvsv'
socketio = SocketIO(app)

# Ollama API configuration
OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_URL = "http://localhost:11434"
MODEL = "deepseek-r1:7b"  # Replace with your desired model

# Store chat messages
chat_messages = []

# Initialize the GinoeasyChat instance
Ollama = OllamaPOST()
OllamaModels = GetAvailableModels()

# Get the ollama available models
#models = OllamaModels.get_ollama_models(OLLAMA_URL)





# Chat Start
@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('change_address')
def handle_change_address(data):
    """Handle address change from client"""
    address = data.get('address', DEFAULT_OLLAMA_URL)
    
    # If address doesn't start with http://, add it
    if not address.startswith('http://') and not address.startswith('https://'):
        address = 'http://' + address
    
    # Store the new address for this client
    if request.sid not in client_settings:
        client_settings[request.sid] = {}
    
    client_settings[request.sid]['ollama_url'] = address
    
    # Try to get models from the new address
    try:
        models = OllamaModels.get_ollama_models(address)
        emit('available_models', {
            'models': models,
            'default_model': client_settings[request.sid].get('model', MODEL)
        })
        emit('message', {"sender": "system", "message": f"Successfully connected to Ollama at {address}"})
    except Exception as e:
        emit('message', {"sender": "system", "message": f"Error connecting to Ollama at {address}: {str(e)}"})







@socketio.on('get_available_models')
def handle_get_models():
    models = OllamaModels.get_ollama_models(OLLAMA_URL)
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