from flask import Flask, render_template
from flask_socketio import SocketIO, send
from OllamaComm import GinoeasyChat

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

# Ollama API configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "deepseek-r1:7b"  # Replace with your desired model

# Store chat messages
chat_messages = []

# Initialize the GinoeasyChat instance
gino = GinoeasyChat()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('send_message')
def handle_send_message(data):
    """Handle sending a message and getting the model's response."""
    user_message = data['message']

    # Store the user's message in the chat history
    chat_messages.append({"sender": "user", "message": user_message})

    # Broadcast the user's message to all clients
    send({"sender": "user", "message": user_message}, broadcast=True)

    # Get the model's response using GinoeasyChat
    model_response = gino.talk_to_ollama(user_message, MODEL, OLLAMA_URL)

    # Store the model's response in the chat history
    chat_messages.append({"sender": "ai", "message": model_response})

    # Broadcast the model's response to all clients
    send({"sender": "ai", "message": model_response}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)