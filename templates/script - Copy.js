const socket = io();

// Chat Basics
const chat = document.getElementById('chat');
const input = document.getElementById('input');
const sendButton = document.getElementById('send');

// Setting
const openSettingsButton = document.getElementById('open-settings');
const closeSettingsButton = document.getElementById('close-settings');
const settingsWindow = document.getElementById('settings-window');
const modelSelect = document.getElementById('model-select');
const addressInput = document.getElementById('address-input');

// Roles
const openRolesButton = document.getElementById('open-roles');
const closeRolesButton = document.getElementById('close-roles');
const rolesWindow = document.getElementById('roles-window');
const roleList = document.getElementById('role-list');

// Settings Window: Request available models from server when page loads
socket.emit('get_available_models');
socket.on('available_models', (data) => {
    modelSelect.innerHTML = '';
    data.models.forEach((model) => {
        const option = document.createElement('option');
        option.value = model.id || model;
        option.textContent = model.name || model;
        modelSelect.appendChild(option);
    });
});

// Show and hide settings window
openSettingsButton.addEventListener('click', () => settingsWindow.style.display = 'block');
closeSettingsButton.addEventListener('click', () => settingsWindow.style.display = 'none');

// Send messages
sendButton.addEventListener('click', () => sendMessage());
input.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) sendMessage();
});

function sendMessage() {
    const message = input.value.trim();
    if (message) {
        appendMessage(message, 'user');
        const selectedModel = modelSelect.value;
        const address = addressInput.value.trim();
        socket.emit('send_message', { message, model: selectedModel, address: address });
        input.value = ''; // Clear input field
    }
}

// Roles Window: Handle roles
openRolesButton.addEventListener('click', () => {
    rolesWindow.style.display = 'block';
    socket.emit('get_roles');
});

closeRolesButton.addEventListener('click', () => rolesWindow.style.display = 'none');

socket.on('available_roles', (data) => {
    roleList.innerHTML = '';
    data.roles.forEach((role, index) => {
        const radio = document.createElement('input');
        radio.type = 'radio';
        radio.name = 'role';
        radio.value = role;
        radio.id = `role-${index}`;
        const label = document.createElement('label');
        label.htmlFor = `role-${index
