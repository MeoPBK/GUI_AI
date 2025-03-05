/**
 * CHAT APPLICATION MAIN JAVASCRIPT
 * This file handles all client-side functionality for a multi-chat interface with AI models
 * Features include: multiple chat management, real-time messaging, code block formatting,
 * model selection, persistence, and role management
 */

// Initialize WebSocket connection for real-time communication
const socket = io();

//_________________________________ DOM Elements: Main UI Components_____________________________________
const chat = document.getElementById('chat');               // Messages container
const input = document.getElementById('input');             // Text input for messages
const sendButton = document.getElementById('send');         // Button to send messages
const openSettingsButton = document.getElementById('open-settings');  // Toggle settings panel
const openConversationsButton = document.getElementById('open-conversations');  // Toggle conversations panel
const settingsWindow = document.getElementById('settings-window');    // Settings panel container
const addChatButton = document.getElementById('add-chat');  // Button to create new chats
const conversationArea = document.querySelector('.conversation-area'); // List of chats sidebar
const modelSelect = document.getElementById('model-select'); // Dropdown for model selection
const addressInput = document.getElementById('address-input'); // Input for API endpoint
const contextInput = document.getElementById('context-input'); // Input for context length
const tempInput = document.getElementById('temperature-input'); // Input for temperature setting
const chatContainer = document.getElementById('chat-container');
const rolesWindow = document.getElementById('roles-window'); // Roles panel container
const roleList = document.getElementById('role-list');      // List of available roles

//______________________________________________________________________________________________________
// Application Constants
const MAX_CHATS = 12;  // Maximum number of concurrent chats allowed
// Stores messages for each chat, indexed by chat ID
const chatMessages = {};
// Stores titles for each chat, indexed by chat ID
const chatTitles = {};
// Global variable to track current active chat
window.currentChatId = 1;

// Initialize first chat with default welcome message
chatMessages[1] = [
    { sender: 'ai', message: `Benvenuto !` }
];

// Initialize first chat with default title
chatTitles[1] = [
    { header: 'Nome del modello' }
];

//______________________________________________________________________________________________________
// settings panel open close
openSettingsButton.addEventListener('click', () => {
    if (settingsWindow.style.display != 'block') {
        settingsWindow.style.display = 'block';
    } else {
        settingsWindow.style.display = 'none';
    }
});

//______________________________________________________________________________________________________
// conversation panel open close
openConversationsButton.addEventListener('click', () => {
    if (conversationArea.style.display != 'block') {
        conversationArea.style.display = 'block';
    } else {
        conversationArea.style.display = 'none';
    }
});

//______________________________________________________________________________________________________
// Generates a chat name based on model and ID
/**
 * @param {number} chatId - The unique identifier for the chat
 * @returns {string} Formatted chat name
 */
function generateChatName(chatId) {
    // Get the currently selected model name from dropdown
    const selectedOption = modelSelect.options[modelSelect.selectedIndex];
    const modelName = selectedOption ? selectedOption.textContent : 'Chat';
    
    // Format name as "[model]'s chat [id]"
    return `${modelName}'s chat ${chatId}`;
}
//______________________________________________________________________________________________________
// sendMessage from the user to the IA
function sendMessage() {
    const message = input.value.trim();
    if (message) {
        const currentChatId = window.currentChatId || 1; // Default to chat 1 if not specified
        appendMessage(message, 'user', currentChatId);
        const selectedModel = modelSelect.value;
        const address = addressInput.value.trim();
        
        // Emit message to server with metadata
        socket.emit('send_message', { 
            message, 
            model: selectedModel, 
            address: address, 
            chatId: currentChatId 
        });
        input.value = ''; // Clear input field after sending
    }
}
// Add click event for send button
sendButton.addEventListener('click', sendMessage);
// Allow sending with Enter key
input.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault(); // Prevent form submission
        sendMessage();
    }
});


//______________________________________________________________________________________________________
// MESSAGE RECEIVING FUNCTIONALITY
const streamingMessages = new Map();
const FORMAT_UPDATE_FREQUENCY = 500; // Update formatting every 5 chunks

// Function to process message content with formatting
function processMessageContent(content) {
    // Your existing processMessageContent function
    // Apply markdown, code highlighting, etc.
    return formatText(content);
}

// Format text with Markdown, code blocks, etc.
function formatText(text) {
    // Replace markdown elements
    // This is a simplified version - use a proper markdown parser in production
    
    // Store original text for comparison at the end
    const originalText = text;
    
    // Format code blocks
    text = text.replace(/```([a-z]*)([\s\S]*?)```/g, 
        '<pre><code class="language-$1">$2</code></pre>');
    
    // Format inline code
    text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Format bold text
    text = text.replace(/\*\*([^\*]+)\*\*/g, '<strong>$1</strong>');
    
    // Format italic text
    text = text.replace(/\*([^\*]+)\*/g, '<em>$1</em>');
    
    // Format lists - properly handle unordered lists with proper wrapping
    let hasListItems = text.match(/^\s*-\s+(.+)$/gm);
    if (hasListItems) {
        // First identify list items and wrap them
        text = text.replace(/^\s*-\s+(.+)$/gm, '<li>$1</li>');
        
        // Then wrap consecutive <li> elements with <ul> tags
        text = text.replace(/(?:<li>.*?<\/li>)+/g, function(match) {
            return '<ul>' + match + '</ul>';
        });
    }
    
    // Format headings (h1, h2, h3)
    text = text.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    text = text.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    text = text.replace(/^# (.+)$/gm, '<h1>$1</h1>');
    
    // Handle numbered lists - look for patterns like "1. item" etc.
    let hasNumberedList = text.match(/^\s*\d+\.\s+(.+)$/gm);
    if (hasNumberedList) {
        // First identify numbered list items and wrap them
        text = text.replace(/^\s*\d+\.\s+(.+)$/gm, '<li>$1</li>');
        
        // Then wrap consecutive <li> elements with <ol> tags
        // This is a simplified approach - a complete solution would need to check 
        // if these aren't already wrapped in <ul> tags
        text = text.replace(/(?:<li>.*?<\/li>)+/g, function(match) {
            // Only wrap with <ol> if not already in a <ul>
            if (!originalText.match(/^\s*-\s+(.+)$/gm)) {
                return '<ol>' + match + '</ol>';
            }
            return match;
        });
    }
    
    // Convert remaining newlines to <br> tags (but not within list items)
    // This is a simplified approach
    text = text.replace(/\n(?![^<]*<\/[uo]l>)/g, '<br>');
    
    return text;
}

// Update the message event handler
socket.on('message', (data) => {
    if (data.sender !== 'user') {
        const chatId = data.chatId || window.currentChatId || 1;
       
        if (data.sender === 'ai') {
            // Handle streaming messages
            if (data.isStreaming) {
                let messageElement;
                let chunkCount = 0;
               
                // If this is the first chunk of a streaming message
                if (!streamingMessages.has(chatId)) {
                    messageElement = appendMessage('', 'ai', chatId, true);
                    streamingMessages.set(chatId, {
                        element: messageElement,
                        content: '',
                        chunkCount: 0
                    });
                } else {
                    const messageData = streamingMessages.get(chatId);
                    messageElement = messageData.element;
                    chunkCount = messageData.chunkCount;

                }
                // Update the message content
                if (data.message && data.message.trim() !== '') {
                    const messageData = streamingMessages.get(chatId);
                    messageData.content += data.message; // Accumulate the content
                    messageData.chunkCount += 1;

                    // Update the displayed message with formatting
                    const contentElement = messageElement.querySelector('.content');
                    if (contentElement) {
                        // Only apply formatting periodically to improve performance
                        if (messageData.chunkCount % FORMAT_UPDATE_FREQUENCY === 0) {
                            contentElement.innerHTML = processMessageContent(messageData.content);
                        } else {
                            // For intermediate updates, just update the text
                            // Using textContent would remove any existing formatting,
                            // so we need to keep using innerHTML for all updates
                            contentElement.innerHTML = messageData.content;
                        }

                        
                        // Scroll to bottom
                        chat.scrollTop = chat.scrollHeight;
                    }
                }
            } else {
                // Final message - clean up streaming state and apply full formatting
                if (streamingMessages.has(chatId)) {
                    const messageData = streamingMessages.get(chatId);
                    const messageElement = messageData.element;

                    // Update final content with full formatting
                    const contentElement = messageElement.querySelector('.content');
                    if (contentElement) {
                        // Use the accumulated content if final message is empty
                        const finalContent = (data.message && data.message.trim() !== '') 
                            ? data.message 
                            : messageData.content;
                            
                        contentElement.innerHTML = processMessageContent(finalContent);
                    }
                    
                    // Update chat preview
                    updateChatPreview(chatId, data.message || messageData.content);
                   
                    // Clean up
                    streamingMessages.delete(chatId);
                } else {
                    // Handle non-streaming message
                    appendMessage(data.message, 'ai', chatId);
                    updateChatPreview(chatId, data.message);
                }
            }
        } else {
            // Handle system messages
            appendMessage(data.message, data.sender, chatId);
            updateChatPreview(chatId, data.message);
        }
    }
});

//______________________________________________________________________________________________________
// appendMessage 
/**
* Appends a message to the chat with proper formatting
* @param {string} message - The message content
* @param {string} sender - The sender of the message ('user', 'ai', or 'system')
* @param {number} chatId - The ID of the chat
* @param {boolean} isStreaming - Whether the message is part of a streaming response
* @returns {HTMLElement} The message element
* @param {boolean} saveMessage - Whether to save message to history (default: true)

*/
function appendMessage(message, sender, chatId, isStreaming = false, saveMessage = true) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', sender);
   
    const contentElement = document.createElement('div');
    contentElement.className = 'content';
    
    // IMPORTANT: For streaming messages, initialize with empty string
    // but don't skip this step completely
    if (!isStreaming && message) {
        contentElement.innerHTML = processMessageContent(message);
    } else {
        // Initialize with empty string, NOT null/undefined
        contentElement.innerHTML = '';
    }
   
    messageElement.appendChild(contentElement);
    chat.appendChild(messageElement);
    chat.scrollTop = chat.scrollHeight;
   
    // Store original raw message
    if (saveMessage && chatId && chatMessages[chatId]) {
        chatMessages[chatId].push({ sender, message });
       
        // Update preview only if it's a new message
        if (sender === 'user') {
            updateChatPreview(chatId, message);
        }
    }
   
    return messageElement;
}


function processMessageContent(content, openLinksInNewTab = true) {
    // Store placeholders for special content
    const specialElements = {
        codeBlocks: [],
        thinkBlocks: []
    };
    
    // Extract code blocks first (before any processing)
    content = content.replace(/```([\w]+)?(?:\s*\n|\s)([\s\S]+?)```/g, (match, lang, code) => {
        const placeholder = `__CODE_BLOCK_${specialElements.codeBlocks.length}__`;
        specialElements.codeBlocks.push({ match, lang, code });
        return placeholder;
    });
    
    // Extract think blocks
    content = content.replace(/<think>([\s\S]+?)<\/think>/g, (match, thinkContent) => {
        const placeholder = `__THINK_BLOCK_${specialElements.thinkBlocks.length}__`;
        specialElements.thinkBlocks.push({ content: thinkContent });
        return placeholder;
    });
    
    // Now escape HTML in the non-special content
    content = escapeHTML(content);
    
    // Process lists before restoring special elements
    content = processLists(content, specialElements);
    
    // Restore think blocks (convert to <em> tags)
    specialElements.thinkBlocks.forEach((block, index) => {
        const placeholder = `__THINK_BLOCK_${index}__`;
        content = content.replace(placeholder, `<em>${block.content}</em>`);
    });
    
    // Process code blocks
    specialElements.codeBlocks.forEach((block, index) => {
        const placeholder = `__CODE_BLOCK_${index}__`;
        
        // Check if lang contains code (like "pythonprint" or "javascriptconst")
        let language = block.lang || 'plaintext';
        let codeToProcess = block.code;
        
        // Extract the language from cases like "pythonprint" -> "python"
        if (block.lang) {
            // Common language identifiers to check against
            const commonLangs = ['python', 'javascript', 'typescript', 'java', 'csharp', 'cpp', 'php', 'ruby', 'go', 'rust', 'bash', 'shell', 'sql', 'html', 'css', 'json', 'xml'];
            
            // Try to match a known language prefix
            for (const knownLang of commonLangs) {
                if (block.lang.toLowerCase().startsWith(knownLang)) {
                    // Extract the real language name
                    language = knownLang;
                    
                    // Add the rest of the "language" string to the beginning of the code
                    // as it's actually the first part of code
                    const remainingText = block.lang.substring(knownLang.length);
                    if (remainingText) {
                        codeToProcess = remainingText + (block.code.startsWith('\n') ? '' : ' ') + block.code;
                    }
                    break;
                }
            }
        }
        
        const codeHtml = codeToProcess.trim();
        const highlightedCode = Prism.highlight(codeHtml, Prism.languages[language] || Prism.languages.plaintext, language);
        
        const codeBlockHtml = `
            <div class="code-block" data-language="${language}">
                ${language ? `<span class="language-badge">${language}</span>` : ''}
                <pre class="line-numbers"><code class="language-${language}">${highlightedCode}</code></pre>
                <button class="copy-button" onclick="copyCodeBlock(this)">Copy</button>
            </div>
        `;
        
        content = content.replace(placeholder, codeBlockHtml);
    });
    
    // Titles
    content = content.replace(/^#{1,6}\s(.+)$/gm, (match, title) => {
        const level = match.match(/^#+/)[0].length;
        return `<h${level} class="chat-title h${level}">${title}</h${level}>`;
    });
    
    // Block quotes - improved to handle multiline blockquotes
    content = content.replace(/^&gt;\s(.+)$/gm, (match, quote) => {
        return `<blockquote class="chat-blockquote">${quote}</blockquote>`;
    });
    
    // Merge adjacent blockquotes
    content = content.replace(/<\/blockquote>\s*<blockquote class="chat-blockquote">/g, '<br>');
    
    // Bold, italic, strikethrough
    content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    content = content.replace(/__(.*?)__/g, '<strong>$1</strong>');
    content = content.replace(/\*(.*?)\*/g, '<em>$1</em>');
    content = content.replace(/_(.*?)_/g, '<em>$1</em>');
    content = content.replace(/~~(.*?)~~/g, '<del>$1</del>');
    
    // Links
    const target = openLinksInNewTab ? 'target="_blank" rel="noopener noreferrer"' : '';
    content = content.replace(/\[([^\]]+)\]\(([^)]+)\)/g, `<a href="$2" ${target} class="chat-link">$1</a>`);
    
    // Auto-link URLs
    content = content.replace(/(https?:\/\/[^\s]+)/g, function(url) {
        if (url.match(/<a[^>]*>/)) return url;
        return `<a href="${url}" ${target} class="chat-link">${url}</a>`;
    });
    
    // Paragraphs and line breaks - fixed to properly close paragraphs
    content = '<p>' + content.replace(/\n{2,}/g, '</p><p>') + '</p>';
    content = content.replace(/\n/g, '<br>');
    
    // Clean up empty paragraphs
    content = content.replace(/<p>\s*<\/p>/g, '');
   
    return content;
}

function processLists(content, specialElements) {
    // Split content into lines
    const lines = content.split('\n');
    const processedLines = [];
    
    let inList = false;
    let currentListType = null;
    let currentListItems = [];
    let startNumber = 1; // Track the starting number for ordered lists
    let currentIndentation = 0;
    
    // Process line by line
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        
        // Check if this line is a placeholder for a code block
        if (line.trim().match(/__CODE_BLOCK_\d+__/)) {
            if (inList) {
                // Add the code block placeholder to the current list item's content
                if (currentListItems.length > 0) {
                    // Append to the last list item
                    currentListItems[currentListItems.length - 1].content += '\n' + line;
                }
            } else {
                // Not in a list, add as normal content
                processedLines.push(line);
            }
            continue;
        }
        
        // Regular list processing
        const isUnorderedListItem = line.match(/^(\s*)-\s(.+)$/);
        const isOrderedListItem = line.match(/^(\s*)(\d+)\.\s(.+)$/);
        
        // Check if this line is a list item
        if (isUnorderedListItem || isOrderedListItem) {
            let indentation, itemContent, itemNumber;
            
            if (isUnorderedListItem) {
                indentation = isUnorderedListItem[1].length;
                itemContent = isUnorderedListItem[2];
                itemNumber = null;
                listType = 'ul';
            } else {
                indentation = isOrderedListItem[1].length;
                itemContent = isOrderedListItem[3];
                itemNumber = parseInt(isOrderedListItem[2], 10);
                listType = 'ol';
            }
            
            // Starting a new list or continuing the current one
            if (!inList) {
                inList = true;
                currentListType = listType;
                currentIndentation = indentation;
                currentListItems = [{content: itemContent, number: itemNumber}];
                
                if (listType === 'ol') {
                    startNumber = itemNumber;
                }
            } else if (currentListType === listType && currentIndentation === indentation) {
                // Continue current list
                currentListItems.push({content: itemContent, number: itemNumber});
            } else {
                // New list type or indentation change - close current list and start a new one
                processedLines.push(createListHTML(currentListItems, currentListType, startNumber));
                currentListType = listType;
                currentIndentation = indentation;
                currentListItems = [{content: itemContent, number: itemNumber}];
                
                if (listType === 'ol') {
                    startNumber = itemNumber;
                }
            }
        } else {
            // Not a list item
            const isEmptyOrWhitespace = line.trim() === '';
            
            if (inList && !isEmptyOrWhitespace) {
                // Check if this might be a continuation of a list item (indented text)
                const indentMatch = line.match(/^(\s+)(.+)$/);
                
                if (indentMatch && indentMatch[1].length > currentIndentation) {
                    // This is indented content belonging to the previous list item
                    if (currentListItems.length > 0) {
                        currentListItems[currentListItems.length - 1].content += '\n' + indentMatch[2];
                    }
                    continue;
                }
                
                // Not a continuation, close the list
                processedLines.push(createListHTML(currentListItems, currentListType, startNumber));
                inList = false;
                currentListItems = [];
            }
            
            // Add the non-list line
            processedLines.push(line);
        }
    }
    
    // Close any final open list
    if (inList) {
        processedLines.push(createListHTML(currentListItems, currentListType, startNumber));
    }
    
    return processedLines.join('\n');
}

function createListHTML(items, listType, startNumber = 1) {
    let html;
    
    if (listType === 'ol' && startNumber !== 1) {
        html = `<${listType} class="chat-list" start="${startNumber}">`;
    } else {
        html = `<${listType} class="chat-list">`;
    }
    
    items.forEach(item => {
        // Check if item content contains a code block placeholder
        const content = item.content.replace(/__CODE_BLOCK_(\d+)__/g, (match, index) => {
            // Return the placeholder as is - it will be replaced later
            return match;
        });
        
        html += `<li>${content}</li>`;
    });
    
    html += `</${listType}>`;
    return html;
}

function escapeHTML(str) {
    const escapeMap = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return str.replace(/[&<>"']/g, m => escapeMap[m]);
}


/**
 * Copies code block content to clipboard
 * @param {HTMLElement} button - The copy button that was clicked
 */
function copyCodeBlock(button) {
    const codeBlock = button.closest('.code-block');
    const codeElement = codeBlock.querySelector('code');
    const text = codeElement.textContent;
    
    copyToClipboard(text, button);
}

//______________________________________________________________________________________________________
// Updates the preview text shown in the chat list
/**
 * @param {number} chatId - Chat identifier
 * @param {string} message - Message to preview
 */
function updateChatPreview(chatId, message) {
    const chatElement = document.querySelector(`[data-chat-id="${chatId}"]`);
    if (chatElement) {
        const msgPreview = chatElement.querySelector('.msg-message');
        if (msgPreview) {
            // Truncate message if too long
            msgPreview.textContent = message.length > 30 ? message.substring(0, 27) + '...' : message;
        }
    }
}



//______________________________________________________________________________________________________
// CHAT NAVIGATION
/**
 * Opens a specific chat and updates UI
 * @param {number|string} chatId - ID of chat to open
 */
function openChat(chatId) {
    // Convert chatId to number if it's a string
    chatId = parseInt(chatId, 10);
    
    // Remove "active" style from all chats
    document.querySelectorAll('.msg').forEach((msg) => {
        msg.classList.remove('active');
    });
    
    // Add "active" style to selected chat
    const selectedChat = document.querySelector(`[data-chat-id="${chatId}"]`);
    if (selectedChat) {
        selectedChat.classList.add('active');
    }
    
    // Update current chat ID
    window.currentChatId = chatId;
    
    // Update messages in main chat area
    updateChatMessages(chatId);
    // Update chat title
    updateChatTitle(chatId);

    // Focus on input for immediate typing
    input.focus();
}
/**
 * Updates message display when switching chats
 * @param {number} chatId - ID of chat to display
 */
function updateChatMessages(chatId) {
    const messages = chatMessages[chatId] || [];
    chat.innerHTML = ''; // Clear existing messages
    
    messages.forEach((msg) => {
        // Pass false for both isStreaming and saveMessage parameters
        appendMessage(msg.message, msg.sender, chatId, false, false);
    });
}
/**
 * Updates displayed chat title
 * @param {number} chatId - ID of chat
 */
function updateChatTitle(chatId) {
    const chatTitle = chatTitles[chatId] ? chatTitles[chatId][0].header : generateChatName(chatId);
    const chatHeader = document.querySelector('.chat-header-title');
    if (chatHeader) {
        chatHeader.textContent = chatTitle;
    }
    
    // Also update the chat list element
    const chatElement = document.querySelector(`[data-chat-id="${chatId}"]`);
    if (chatElement) {
        const usernameElement = chatElement.querySelector('.msg-username');
        if (usernameElement) {
            usernameElement.textContent = chatTitle;
        }
    }
}


//______________________________________________________________________________________________________
// CHAT MANAGEMENT: DELETION
/**
 * Deletes a chat if it's not the only one
 * @param {number} chatId - ID of chat to delete
 */
function deleteChat(chatId) {
    // Don't allow deleting the last chat
    if (Object.keys(chatMessages).length <= 1) {
        alert("Non puoi eliminare l'unica chat presente!");
        return;
    }
    
    // Remove chat from UI
    const chatElement = document.querySelector(`[data-chat-id="${chatId}"]`);
    if (chatElement) {
        chatElement.remove();
    }
    
    // Remove chat data from memory
    delete chatMessages[chatId];
    delete chatTitles[chatId];
    
    // If current chat was deleted, open another one
    if (window.currentChatId === chatId) {
        const firstChatId = Object.keys(chatMessages)[0];
        if (firstChatId) {
            openChat(firstChatId);
        }
    }
}
//______________________________________________________________________________________________________
// CHAT MANAGEMENT: CREATION
/**
 * Handles creation of new chat conversations
 */
let chatCounter = Object.keys(chatMessages).length; // Initialize counter with number of existing chats
addChatButton.addEventListener('click', () => {
    // Check if maximum chat limit is reached
    if (Object.keys(chatMessages).length >= MAX_CHATS) {
        alert(`Hai raggiunto il limite massimo di ${MAX_CHATS} chat!`);
        return;
    }
    
    // Increment counter for new chat ID
    chatCounter++;
    const newChatId = chatCounter;
    const chatName = generateChatName(newChatId);
   
    // Create a complete chat element with deletion button
    const newChat = document.createElement('div');
    newChat.classList.add('msg');
    newChat.id = `chat-${newChatId}`;
    newChat.setAttribute('data-chat-id', newChatId);
    
    newChat.innerHTML = `
        <div class="msg-detail">
            <div class="msg-username">${chatName}</div>
            <div class="msg-message">Nuova conversazione</div>
        </div>
        <button class="delete-chat" data-chat-id="${newChatId}">&times;</button>
    `;
    
    // Initialize messages and title for new chat
    chatMessages[newChatId] = [
        { sender: 'ai', message: `Benvenuto in "${chatName}"!` }
    ];
    
    chatTitles[newChatId] = [
        { header: chatName }
    ];

    
    // Add click event to open the chat
    newChat.addEventListener('click', (e) => {
        // Don't open chat if delete button was clicked
        if (!e.target.classList.contains('delete-chat')) {
            openChat(newChatId);
        }
    });

    // Add event to delete button
    const deleteButton = newChat.querySelector('.delete-chat');
    deleteButton.addEventListener('click', (e) => {
        e.stopPropagation(); // Prevent click event from propagating to parent element
        deleteChat(newChatId);
    });

    // Add new chat to UI
    conversationArea.appendChild(newChat);

    // Immediately open the new chat
    openChat(newChatId);
});


    openChat(1);




//______________________________________________________________________________________________________
// MODEL MANAGEMENT Handle model selection and configuration
// Request available models from server when page loads
socket.emit('get_available_models');
/**
 * Receives and displays available AI models from server
 */
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
        }

        modelSelect.appendChild(option);
    });
    // Automatically select the first model if no default is specified
    if (!data.default_model && modelSelect.options.length > 0) {
        modelSelect.options[0].selected = true;
    }
    // Update the first chat title if necessary
    const selectedModel = modelSelect.options[modelSelect.selectedIndex].textContent;
        chatTitles[1][0].header = `${selectedModel}'s chat 1`;
        updateChatTitle(1);
        
        // Update the chat list element
        const chatElement = document.querySelector(`[data-chat-id="1"]`);
        if (chatElement) {
            const usernameElement = chatElement.querySelector('.msg-username');
            if (usernameElement) {
                usernameElement.textContent = `${selectedModel}'s chat 1`;
            }
        }
});
/**
 * Handles model selection changes
 */
modelSelect.addEventListener('change', () => {
    const selectedModel = modelSelect.options[modelSelect.selectedIndex].textContent;
    
    // Inform the server about model change
    socket.emit('change_model', { 
        model: modelSelect.value,
        address: addressInput.value.trim()
    });
    
    // Update all chat titles
    Object.keys(chatTitles).forEach(chatId => {
        const newTitle = generateChatName(chatId);
        chatTitles[chatId][0].header = newTitle;
        
        // Update UI for each chat
        updateChatTitle(chatId);
    });
});/**
 * Handles API address changes
 */
addressInput.addEventListener('change', () => {
    const address = addressInput.value.trim();
    if (address) {
        // Notify about address change
        appendMessage(`Address set to ${address}`, 'system', window.currentChatId);
        
        // Inform the server about address change
        socket.emit('change_address', { 
            address: address,
            model: modelSelect.value
        });
    }
});
/**
 * Handles context length changes
 */
contextInput.addEventListener('change', () => {
    const context = contextInput.value.trim();
    if (context) {
        // Notify about context change
        appendMessage(`context set to ${context}`, 'system', window.currentChatId);
        
        // Inform the server about context change
        socket.emit('change_context', { 
            context_lenght: context,
        });
    }
});
/**
 * Handles temperature setting changes
 */
tempInput.addEventListener('change', () => {
    const temp = tempInput.value.trim();
    if (temp) {
        // Notify about temperature change
        appendMessage(`tempInput set to ${temp}`, 'system', window.currentChatId);
        
        // Inform the server about temperature change
        socket.emit('change_temp', { 
            temp: temp,
        });
    }
});



//______________________________________________________________________________________________________
//  * CODE BLOCK CLIPBOARD FUNCTIONALITY
/**
 * Copies text to clipboard with visual feedback
 * @param {string} text - Text to copy
 * @param {HTMLElement} button - Button element for feedback
 */
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

/**
 * Fallback method for copying to clipboard
 * Used when the Clipboard API is not available
 * 
 * @param {string} text - Text to copy
 * @param {HTMLElement} button - Button element for feedback
 */
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



//______________________________________________________________________________________________________
// ROLES MANAGEMENT
/**
 * Handles AI role selection
 */
let selectedRole = null; // Global variable to store selected role

// Request available roles from server
socket.emit('get_roles');

/**
 * Receives and displays available AI roles from server
 */
socket.on('available_roles', (data) => {
    roleList.innerHTML = ''; // Clear previous list

    // Create radio buttons for each role
    data.roles.forEach((role, index) => {
        const radio = document.createElement('input');
        radio.type = 'radio';
        radio.name = 'role';
        radio.value = role;
        radio.id = `role-${index}`;

        // If this role was previously selected, check it
        if (selectedRole === role) {
            radio.checked = true;
        }

        const label = document.createElement('label');
        label.htmlFor = `role-${index}`;
        label.textContent = role;

        // Handle role selection change
        radio.addEventListener('change', () => {
            selectedRole = role
            socket.emit('set_role', { selected_role: role }); // Send selected role to server
        });

        // Add elements to role list
        roleList.appendChild(radio);
        roleList.appendChild(label);
        roleList.appendChild(document.createElement('br'));
    });
});

















