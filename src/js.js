const socket = io();
const chat = document.getElementById('chat');
const input = document.getElementById('input');
const sendButton = document.getElementById('send');
const openSettingsButton = document.getElementById('open-settings');
const settingsWindow = document.getElementById('settings-window');
const addChatButton = document.getElementById('add-chat');
const conversationArea = document.querySelector('.conversation-area');
const modelSelect = document.getElementById('model-select');
const addressInput = document.getElementById('address-input');

// Limite massimo di chat
const MAX_CHATS = 12;

// Memorizza i messaggi di ogni chat
const chatMessages = {};
const chatTitles = {};

chatMessages[1] = [
    { sender: 'ai', message: `Benvenuto !` }
];

chatTitles[1] = [
    { header: 'Nome del modello' }
];

// Inizializza la chat corrente
window.currentChatId = 1;

// Apri la finestra delle impostazioni
openSettingsButton.addEventListener('click', () => {
    if (settingsWindow.style.display != 'block') {
        settingsWindow.style.display = 'block';
    } else {
        settingsWindow.style.display = 'none';
    }
});

// Invia messaggio
sendButton.addEventListener('click', () => {
    const message = input.value.trim();
    if (message) {
        const currentChatId = window.currentChatId || 1; // Default alla chat 1 se non specificato
        appendMessage(message, 'user', currentChatId);
        const selectedModel = modelSelect.value;
        const address = addressInput.value.trim();
        socket.emit('send_message', { 
            message, 
            model: selectedModel, 
            address: address, 
            chatId: currentChatId 
        });
        input.value = ''; // Clear input field
    }
});

// Gestisci anche l'invio con il tasto Enter
input.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendButton.click();
    }
});

// Ricevi messaggio
socket.on('message', (data) => {
    if (data.sender !== 'user') {
        const chatId = data.chatId || window.currentChatId || 1; // Usa la chat corrente o default a 1
        appendMessage(data.message, data.sender, chatId);
        
        // Aggiorna l'anteprima del messaggio nella lista chat
        updateChatPreview(chatId, data.message);
    }
});

// Aggiorna l'anteprima del messaggio nella lista chat
function updateChatPreview(chatId, message) {
    const chatElement = document.querySelector(`[data-chat-id="${chatId}"]`);
    if (chatElement) {
        const msgPreview = chatElement.querySelector('.msg-message');
        if (msgPreview) {
            // Tronca il messaggio se è troppo lungo
            msgPreview.textContent = message.length > 30 ? message.substring(0, 27) + '...' : message;
        }
    }
}

// Apri una chat specifica
function openChat(chatId) {
    // Converti chatId in numero se è una stringa
    chatId = parseInt(chatId, 10);
    
    // Rimuovi lo stile "active" da tutte le chat
    document.querySelectorAll('.msg').forEach((msg) => {
        msg.classList.remove('active');
    });
    
    // Aggiungi lo stile "active" alla chat selezionata
    const selectedChat = document.querySelector(`[data-chat-id="${chatId}"]`);
    if (selectedChat) {
        selectedChat.classList.add('active');
    }
    
    // Aggiorna la variabile chatId corrente
    window.currentChatId = chatId;
    
    // Aggiorna i messaggi nella chat principale
    updateChatMessages(chatId);
    // Aggiorna il titolo della chat
    updateChatTitle(chatId);

    // Focus sull'input per iniziare a scrivere
    input.focus();
}

// Aggiorna i messaggi nella chat attiva
function updateChatMessages(chatId) {
    const messages = chatMessages[chatId] || [];
    chat.innerHTML = ''; // Clear existing messages
    messages.forEach((msg) => {
        // Pass false as the last parameter to avoid saving these messages again
        appendMessage(msg.message, msg.sender, chatId, false);
    });
}

// Aggiorna il titolo della chat attiva
function updateChatTitle(chatId) {
    const chatTitle = chatTitles[chatId] ? chatTitles[chatId][0].header : 'Chat';
    const chatHeader = document.querySelector('.chat-header-title');
    if (chatHeader) {
        chatHeader.textContent = chatTitle;
    }
}

// Elimina una chat
function deleteChat(chatId) {
    // Non permettere di eliminare l'ultima chat
    if (Object.keys(chatMessages).length <= 1) {
        alert("Non puoi eliminare l'unica chat presente!");
        return;
    }
    
    // Rimuovi la chat dalla UI
    const chatElement = document.querySelector(`[data-chat-id="${chatId}"]`);
    if (chatElement) {
        chatElement.remove();
    }
    
    // Rimuovi i messaggi dalla memoria
    delete chatMessages[chatId];
    delete chatTitles[chatId];
    
    // Se la chat corrente è stata eliminata, apri un'altra chat
    if (window.currentChatId === chatId) {
        const firstChatId = Object.keys(chatMessages)[0];
        if (firstChatId) {
            openChat(firstChatId);
        }
    }
}

// Genera un nome casuale per la chat
function generateChatName() {    
    return `${model.name}`;
}

// Aggiungi una nuova chat
let chatCounter = Object.keys(chatMessages).length; // Inizializza il contatore con il numero di chat esistenti
addChatButton.addEventListener('click', () => {
    // Controlla se è stato raggiunto il limite di chat
    if (Object.keys(chatMessages).length >= MAX_CHATS) {
        alert(`Hai raggiunto il limite massimo di ${MAX_CHATS} chat!`);
        return;
    }
    
    // Incrementa il contatore per il nuovo ID chat
    chatCounter++;
    const newChatId = chatCounter;
    const chatName = generateChatName();
   
    // Crea un elemento chat completo con pulsante di eliminazione
    const newChat = document.createElement('div');
    newChat.classList.add('msg');
    newChat.id = `chat-${newChatId}`;
    newChat.setAttribute('data-chat-id', newChatId);
    
    newChat.innerHTML = `
        <div class="msg-detail">
            <div class="msg-username">${chatName} ${newChatId}</div>
            <div class="msg-message">Nuova conversazione</div>
        </div>
        <button class="delete-chat" data-chat-id="${newChatId}">&times;</button>
    `;
    
    // Inizializza i messaggi per la nuova chat
    chatMessages[newChatId] = [
        { sender: 'ai', message: `Benvenuto in "${chatName} ${newChatId}"!` }
    ];
    // Inizializza il titolo per la nuova chat
    chatTitles[newChatId] = [
        { header: chatName }
    ];
    
    // Aggiungi evento di click per aprire la chat
    newChat.addEventListener('click', (e) => {
        // Non aprire la chat se è stato cliccato il pulsante di eliminazione
        if (!e.target.classList.contains('delete-chat')) {
            openChat(newChatId);
        }
    });

    // Aggiungi evento al pulsante di eliminazione
    const deleteButton = newChat.querySelector('.delete-chat');
    deleteButton.addEventListener('click', (e) => {
        e.stopPropagation(); // Evita che l'evento di click si propaghi all'elemento padre
        deleteChat(newChatId);
    });

    // Aggiungi la nuova chat all'interfaccia
    conversationArea.appendChild(newChat);

    // Apri subito la nuova chat
    openChat(newChatId);
});

// Inizializzazione: aggiungi gli eventi click alle chat esistenti e apri la prima chat
document.addEventListener('DOMContentLoaded', () => {
    // Imposta la chat corrente all'avvio
    window.currentChatId = 1;
    
    // Aggiungi gli event listener a tutte le chat esistenti
    document.querySelectorAll('.msg').forEach((msg) => {
        const chatId = msg.getAttribute('data-chat-id');
        
        // Aggiungi l'evento click per aprire la chat
        msg.addEventListener('click', (e) => {
            // Non aprire la chat se è stato cliccato il pulsante di eliminazione
            if (!e.target.classList.contains('delete-chat')) {
                openChat(chatId);
            }
        });
        
        // Aggiungi evento al pulsante di eliminazione se presente
        const deleteButton = msg.querySelector('.delete-chat');
        if (deleteButton) {
            deleteButton.addEventListener('click', (e) => {
                e.stopPropagation(); // Evita che l'evento di click si propaghi all'elemento padre
                deleteChat(chatId);
            });
        }
    });
    
    // Apri la prima chat all'avvio
    openChat(1);
});

// Funzione per salvare le chat nel localStorage
function saveChatsToStorage() {
    localStorage.setItem('chatMessages', JSON.stringify(chatMessages));
}

// Funzione per caricare le chat dal localStorage
function loadChatsFromStorage() {
    const savedChats = localStorage.getItem('chatMessages');
    if (savedChats) {
        return JSON.parse(savedChats);
    }
    return null;
}

// Salva le chat automaticamente quando la pagina si chiude
window.addEventListener('beforeunload', () => {
    saveChatsToStorage();
});




// Request available models from server when page loads
socket.emit('get_available_models');

// Listen for available models from server
socket.on('available_models', (data) => {
    // Clear existing options
    modelSelect.innerHTML = '';
    
    // Add options for each model from the server
    data.models.forEach((model, index) => {
        const option = document.createElement('option');
        option.value = model.id || model;
        option.textContent = model.name || model;
        
        // Set as selected if it's the default model
        if (data.default_model && (model.id === data.default_model || model === data.default_model)) {
            option.selected = true;
        } else if (index === 0 && !data.default_model) {
            // If no default is specified, select the first one
            option.selected = true;
        }
        
        modelSelect.appendChild(option);
    });
});

// Send message with selected model and address
sendButton.addEventListener('click', () => {
    const message = input.value.trim();
    if (message) {
        // Display your own message immediately
        appendMessage(message, 'user');

        // Get the selected model and address
        const selectedModel = modelSelect.value;
        const address = addressInput.value.trim();

        // Send message with model and address info
        socket.emit('send_message', { 
            message, 
            model: selectedModel,
            address: address
        });
        
        input.value = ''; // Clear the input field
    }
});

// Send message by pressing Enter key
input.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault(); // Prevent form submission
        const message = input.value.trim();
        if (message) {
            // Display your own message immediately
            appendMessage(message, 'user');

            // Get the selected model and address
            const selectedModel = modelSelect.value;
            const address = addressInput.value.trim();

            // Send message with model and address info
            socket.emit('send_message', { 
                message, 
                model: selectedModel,
                address: address
            });
            
            input.value = ''; // Clear the input field
        }
    }
});

// Model change event
modelSelect.addEventListener('click', () => {
    const selectedModel = modelSelect.options[modelSelect.selectedIndex].textContent;
    // Notify about model change if needed
    // appendMessage(`Model changed to ${selectedModel}`, 'system');
    
    // Inform the server about model change
    socket.emit('change_model', { 
        model: modelSelect.value,
        address: addressInput.value.trim()
    });
});


modelSelect.addEventListener('click', () => {
    // Notify about model change if needed
    // appendMessage(`Model changed to ${selectedModel}`, 'system');
    
    // Inform the server about model change
    socket.emit('change_role', { 
        model: rolesWindow.value,
    });
});

// Address change event
addressInput.addEventListener('change', () => {
    const address = addressInput.value.trim();
    if (address) {
        // Notify about address change if needed
        appendMessage(`Address set to ${address}`, 'system');
        
        // Inform the server about address change
        socket.emit('change_address', { 
            address: address,
            model: modelSelect.value
        });
    }
});

// Function to update the chat title
function appendTitle(chatId) {
    const chatTitle = chatTitles[chatId] ? chatTitles[chatId][0].header : 'Chat';
    const chatHeader = document.querySelector('.chat-header-title');
    if (chatHeader) {
        chatHeader.textContent = chatTitle;
    }
}

// Aggiungi messaggio alla chat
function appendMessage(message, sender, chatId, saveMessage = true) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', sender);

    // Regular expression to match code blocks with any language
    // Format: ```language ... ``` where language is optional
    const codeBlockRegex = /```([a-zA-Z0-9]*)\n?([^`]+)```/g;
    let match;
    let lastIndex = 0;
    let hasCodeBlock = false;

    // Process all code blocks in the message
    while ((match = codeBlockRegex.exec(message)) !== null) {
        hasCodeBlock = true;
        
        // Add text before code block
        if (match.index > lastIndex) {
            const textBefore = message.substring(lastIndex, match.index).trim();
            if (textBefore) {
                const textElement = document.createElement('div');
                textElement.textContent = textBefore;
                messageElement.appendChild(textElement);
            }
        }

        // Extract language and code content
        const language = match[1].trim() || 'code'; // Default to 'code' if no language specified
        const codeContent = match[2].trim();

        // Create code block
        const codeBlock = document.createElement('div');
        codeBlock.classList.add('code-block');
        codeBlock.setAttribute('data-code', codeContent);
        codeBlock.textContent = codeContent;

        // Add language badge if specified
        if (language && language !== 'code') {
            const langBadge = document.createElement('span');
            langBadge.classList.add('language-badge');
            langBadge.textContent = language;
            codeBlock.appendChild(langBadge);
            
            // Add more padding-top to accommodate the language badge
            codeBlock.style.paddingTop = '25px';
        }

        // Add copy button
        const copyButton = document.createElement('button');
        copyButton.classList.add('copy-button');
        copyButton.textContent = 'Copy';
        copyButton.addEventListener('click', () => {
            copyToClipboard(codeContent, copyButton);
        });

        codeBlock.appendChild(copyButton);
        messageElement.appendChild(codeBlock);

        // Update last index
        lastIndex = match.index + match[0].length;
    }

    // Add any remaining text after the last code block
    if (lastIndex < message.length) {
        const textAfter = message.substring(lastIndex).trim();
        if (textAfter) {
            const textElement = document.createElement('div');
            textElement.textContent = textAfter;
            messageElement.appendChild(textElement);
        }
    }

    // If no code blocks were found, just set the text content
    if (!hasCodeBlock) {
        messageElement.textContent = message;
    }

    chat.appendChild(messageElement);
    chat.scrollTop = chat.scrollHeight;

    // Only save the message if saveMessage is true
    if (saveMessage && chatMessages[chatId]) {
        chatMessages[chatId].push({ sender, message });
        
        // Aggiorna l'anteprima solo se è un nuovo messaggio
        if (sender === 'user') {
            updateChatPreview(chatId, message);
        }
    }
}

// Copy to clipboard function
function copyToClipboard(text, button) {
    // Modern clipboard API
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text)
            .then(() => {
                button.textContent = 'Copied!';
                setTimeout(() => {
                    button.textContent = 'Copy';
                }, 2000);
            })
            .catch(err => {
                console.error('Failed to copy: ', err);
                fallbackCopyToClipboard(text, button);
            });
    } else {
        // Fallback for browsers that don't support clipboard API
        fallbackCopyToClipboard(text, button);
    }
}

// Fallback copy method using document.execCommand
function fallbackCopyToClipboard(text, button) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed'; // Avoid scrolling to bottom
    textarea.style.opacity = '0'; // Hide the textarea
    document.body.appendChild(textarea);
    textarea.select();

    try {
        const successful = document.execCommand('copy');
        if (successful) {
            button.textContent = 'Copied!';
            setTimeout(() => {
                button.textContent = 'Copy';
            }, 2000);
        } else {
            console.error('Failed to copy text.');
            button.textContent = 'Error!';
            setTimeout(() => {
                button.textContent = 'Copy';
            }, 2000);
        }
    } catch (err) {
        console.error('Failed to copy text: ', err);
        button.textContent = 'Error!';
        setTimeout(() => {
            button.textContent = 'Copy';
        }, 2000);
    } finally {
        document.body.removeChild(textarea);
    }
}






