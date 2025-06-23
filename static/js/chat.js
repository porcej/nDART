// Initialize socket connection
const socket = io.connect('//' + document.domain + ':' + location.port + '/chat');

// Chat elements
const chatBox = document.getElementById('chat-box');
const messageForm = document.getElementById('message-form');
const messageInput = document.getElementById('message');
// const roomSelect = document.getElementById('room-select');
const sendButton = document.getElementById('send-button');

// Get current room from localStorage or use default
let currentRoomId = localStorage.getItem('currentRoomId') || roomSelect.value;

// Theme handling
function updateTheme() {
    const isDarkMode = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    document.body.classList.toggle('dark-mode', isDarkMode);
}

// Listen for theme changes
const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
        if (mutation.attributeName === 'data-bs-theme') {
            updateTheme();
        }
    });
});

observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['data-bs-theme']
});

// Initial theme setup
updateTheme();

// Connect and join default room
socket.on('connect', () => {
    joinRoom(currentRoomId);
    messageInput.focus();
});

// Load previous messages
socket.on('previous_messages', (messages) => {
    chatBox.innerHTML = '';
    messages.forEach(message => {
        addMessageToChatBox(message, message.sender === window.chatConfig.sender ? 'right' : 'left');
    });
    scrollToBottom();
});

// Handle incoming messages
socket.on('receive_message', (data) => {
    addMessageToChatBox(data, data.sender === window.chatConfig.sender ? 'right' : 'left');
    scrollToBottom();
});

// Handle message submission
messageForm.onsubmit = (e) => {
    e.preventDefault();
    const message = messageInput.value.trim();
    
    if (message) {
        // Disable button while sending
        sendButton.disabled = true;
        
        socket.emit('send_message', {
            message: message,
            room_id: currentRoomId
        });
        
        messageInput.value = '';
        
        // Re-enable button after sending
        setTimeout(() => {
            sendButton.disabled = false;
            messageInput.focus();
        }, 100);
    }
};

// Handle room changes
roomSelect.onchange = () => {
    const newRoomId = roomSelect.value;
    if (newRoomId !== currentRoomId) {
        leaveRoom(currentRoomId);
        currentRoomId = newRoomId;
        localStorage.setItem('currentRoomId', currentRoomId);
        joinRoom(currentRoomId);
        
        // Clear chat box when changing rooms
        chatBox.innerHTML = '';
        
        // Add room change notification
        addSystemMessage(`Switched to ${roomSelect.options[roomSelect.selectedIndex].text} room`);
    }
};

// Join room function
function joinRoom(roomId) {
    socket.emit('join', { room_id: roomId });
    addSystemMessage(`Joined ${roomSelect.options[roomSelect.selectedIndex].text} room`);
}

// Leave room function
function leaveRoom(roomId) {
    socket.emit('leave', { room_id: roomId });
}

// Add message to chat box
function addMessageToChatBox(data, alignment) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', alignment);
    messageDiv.dataset.messageId = data.id;

    const bubble = document.createElement('div');
    bubble.classList.add('bubble', alignment);

    // Format timestamp
    const timestamp = new Date(data.created_at);
    const formattedTime = formatTime(timestamp);

    // Create message content structure
    const senderInfo = document.createElement('div');
    senderInfo.classList.add('sender-info');
    senderInfo.textContent = data.nick_name ? `${data.nick_name} (${data.sender})` : data.sender;

    const messageContent = document.createElement('div');
    messageContent.classList.add('message-content');
    messageContent.textContent = data.content;

    const timeElement = document.createElement('div');
    timeElement.classList.add('timestamp');
    timeElement.textContent = formattedTime;

    // Assemble message
    bubble.appendChild(senderInfo);
    bubble.appendChild(messageContent);
    bubble.appendChild(timeElement);
    messageDiv.appendChild(bubble);
    chatBox.appendChild(messageDiv);
}

// Add system message
function addSystemMessage(message) {
    const systemDiv = document.createElement('div');
    systemDiv.classList.add('system-message');
    systemDiv.textContent = message;
    chatBox.appendChild(systemDiv);
    scrollToBottom();
}

// Format time helper
function formatTime(date) {
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
}

// Scroll chat to bottom with smooth animation
function scrollToBottom() {
    chatBox.scrollTo({
        top: chatBox.scrollHeight,
        behavior: 'smooth'
    });
}

// Handle Enter key for sending messages
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        messageForm.dispatchEvent(new Event('submit'));
    }
});

// Add typing indicator
let typingTimeout;
messageInput.addEventListener('input', () => {
    clearTimeout(typingTimeout);
    socket.emit('typing', { room_id: currentRoomId });
    
    typingTimeout = setTimeout(() => {
        socket.emit('stop_typing', { room_id: currentRoomId });
    }, 1000);
});

// Message status tracking
function updateMessageStatus(messageId, status) {
    const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
    if (messageElement) {
        messageElement.dataset.status = status;
        updateStatusIndicator(messageElement, status);
    }
}

// Message editing
function enableMessageEdit(messageId) {
    const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
    if (messageElement && messageElement.dataset.sender === window.chatConfig.nick_name) {
        const content = messageElement.querySelector('.message-content');
        content.contentEditable = true;
        content.focus();
    }
}

// File upload handling
function handleFileUpload(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    fetch('/chat/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            sendMessage({
                type: 'file',
                content: data.file_url,
                filename: file.name
            });
        }
    });
}

// Typing indicators
let typingUsers = new Set();
function updateTypingIndicator() {
    const typingList = document.getElementById('typing-indicators');
    if (typingUsers.size > 0) {
        typingList.textContent = `${Array.from(typingUsers).join(', ')} typing...`;
        typingList.style.display = 'block';
    } else {
        typingList.style.display = 'none';
    }
}

// Add custom scrollbar styles
const style = document.createElement('style');
style.textContent = `
    .scrollbar-custom::-webkit-scrollbar {
        width: 8px;
    }
    .scrollbar-custom::-webkit-scrollbar-track {
        background: var(--bs-tertiary-bg);
    }
    .scrollbar-custom::-webkit-scrollbar-thumb {
        background: var(--bs-secondary-bg);
        border-radius: 4px;
    }
    .scrollbar-custom::-webkit-scrollbar-thumb:hover {
        background: var(--bs-secondary-color);
    }
`;
document.head.appendChild(style);