from flask import Flask, render_template
from flask_socketio import SocketIO, send, emit
from OllamaComm import OllamaPOST

#### COSTANTS
OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "deepseek-r1:7b"  # Default model to use
ROLES =["None",
        "User Defined",
        "Basic Assistant",
        "Precise Scientist & Engineer", 
        "Software Engineer (light)", 
        "Software Engineer (full)", 
        "Chef",
        "Story Teller"]

#template = os.path.join(os.getcwd(), "templates2") # needs import os
app = Flask(__name__) # app = Flask(__name__)
app.config['SECRET_KEY'] = 'sdifjansovkjdsnfvasnxlvmnskdjknvsv'
socketio = SocketIO(app)

# Store chat messages
chat_messages = []

# Initialize the Ollama communication instances
Ollama = OllamaPOST()

@app.route('/')
def index():
    return render_template('index.html')

#### GET_AVAILABLE_MODELS
@socketio.on('get_available_models')
def handle_get_models(data=None):
    """Send available models to the client when requested"""
    # If data is provided, use the address from data, otherwise use default
    Ollama.address = data.get('address', OLLAMA_URL) if data else OLLAMA_URL
    
    try:
        # Get models from the specified address
        models = Ollama.get_ollama_models(Ollama.address)
        emit('available_models', {
            'models': models,
            'default_model': DEFAULT_MODEL
        })
        
        # Send system message about successful connection
        send({"sender": "system", "message": f"Connected to Ollama at {Ollama.address}"}, broadcast=True)
    except Exception as e:
        # Send error message if models can't be fetched
        error_msg = f"Failed to connect to Ollama at {Ollama.address}: {str(e)}"
        send({"sender": "system", "message": error_msg}, broadcast=True)
        # Still emit available_models but with empty list to avoid client errors
        emit('available_models', {
            'models': [],
            'default_model': DEFAULT_MODEL
        })

#### GET_AVAILABLE_MODELS FROM ADDRESS
@socketio.on('change_address')
def handle_change_address(data):
    """Handle changing the Ollama server address"""
    Ollama.address = data.get('address', OLLAMA_URL)
    
    try:
        # Get models from the new address
        models = Ollama.get_ollama_models(Ollama.address)
        emit('available_models', {
            'models': models,
            'default_model': DEFAULT_MODEL
        })    
        # Send success message
        success_msg = f"Successfully connected to Ollama at {Ollama.address}"
        send({"sender": "system", "message": success_msg}, broadcast=True)
    except Exception as e:
        # Send error message
        error_msg = f"Failed to connect to Ollama at {Ollama.address}: {str(e)}"
        send({"sender": "system", "message": error_msg}, broadcast=True)

@socketio.on('change_model')
def handle_change_model(data):
    """Handle changing the model"""
    Ollama.model = data.get('model', DEFAULT_MODEL)
    Ollama.address = data.get('address', OLLAMA_URL)
    
#### GET_ROLES
@socketio.on('get_roles')
def send_roles():
    try:
        socketio.emit('available_roles', {'roles': ROLES})
    except Exception as e:
        send(f"Error sending roles: {e}", broadcast=True)

@socketio.on('set_role')
def receive_role(data):  
    try:
        selected_role = data.get('selected_role')
        # Emit available roles (if needed by the client)
        socketio.emit('available_roles', {'roles': ROLES})
        if selected_role in ROLES:
            Ollama.role_index = ROLES.index(selected_role)
            # Store all attributes for the selected role
            Ollama.role_flag = 1
            # print("role_idx: " + str(role_index))
            send({"sender": "system", "message": f"Role set to: {selected_role}"}, broadcast=True)
        else:
            send({"sender": "system", "message": "Invalid role selected."}, broadcast=True)
    except Exception as e:
        send({"sender": "system", "message": f"Error processing role selection: {str(e)}"}, broadcast=True)

#### MANAGE MESSAGES
@socketio.on('send_message')
def handle_send_message(data):
    """Handle sending a message and getting the model's response."""
    user_message = data['message']
    Ollama.model = data.get('model', DEFAULT_MODEL)
    Ollama.address = data.get('address', OLLAMA_URL)

    chat_messages.append({"sender": "user", "message": user_message})     # Store the user's message in the chat history
    send({"sender": "user", "message": user_message}, broadcast=True)     # Broadcast the user's message to all clients

    try:
        # Get the model's response using Ollama
        model_response = Ollama.talk_to_ollama(user_message)
        # Store the model's response in the chat history
        chat_messages.append({"sender": "ai", "message": model_response})
        # Broadcast the model's response to all clients
        send({"sender": "ai", "message": model_response}, broadcast=True)
        print(Ollama.context)
    except Exception as e:
        # Send error message if response fails
        error_msg = f"Error getting response from {Ollama.model}: {str(e)}"
        send({"sender": "system", "message": error_msg}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

## TTRYY 4

