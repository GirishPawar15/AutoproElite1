// Chatbot functionality
document.addEventListener('DOMContentLoaded', function() {
    const chatbotIcon = document.getElementById('chatbotIcon');
    const chatbotPanel = document.getElementById('chatbotPanel');
    const chatbotClose = document.getElementById('chatbotClose');
    const chatbotInput = document.getElementById('chatbotInput');
    const sendChatMessage = document.getElementById('sendChatMessage');
    const chatbotMessages = document.getElementById('chatbotMessages');

    // Check if elements exist before adding event listeners
    if (!chatbotIcon || !chatbotPanel || !chatbotClose || !chatbotInput || !sendChatMessage || !chatbotMessages) {
        console.error('Chatbot elements not found');
        return;
    }

    chatbotIcon.addEventListener('click', () => {
        chatbotPanel.classList.toggle('active');
    });

    chatbotClose.addEventListener('click', () => {
        chatbotPanel.classList.remove('active');
    });

    const liveChatLink = document.getElementById('liveChatLink');
    if (liveChatLink) {
        liveChatLink.addEventListener('click', (e) => {
            e.preventDefault();
            chatbotPanel.classList.add('active');
        });
    }

    function addMessage(content, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        messageDiv.classList.add(isUser ? 'user-message' : 'bot-message');

        const avatarDiv = document.createElement('div');
        avatarDiv.classList.add('message-avatar');
        avatarDiv.innerHTML = isUser ? `
            <svg width="18" height="18" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path fill="#ffffff" d="M12 12c2.761 0 5-2.239 5-5s-2.239-5-5-5-5 2.239-5 5 2.239 5 5 5zm0 2c-3.866 0-7 3.134-7 7h14c0-3.866-3.134-7-7-7z"/>
            </svg>
        ` : `
            <svg width="18" height="18" viewBox="0 0 96 96" xmlns="http://www.w3.org/2000/svg">
                <circle cx="48" cy="48" r="44" fill="#e2e8f0"/>
                <g fill="#1e293b">
                    <path d="M30 58h36c1.7 0 3-1.3 3-3v-8c0-7.7-10.7-14-21-14s-21 6.3-21 14v8c0 1.7 1.3 3 3 3z"/>
                    <circle cx="39" cy="47" r="5" fill="#3b82f6"/>
                    <circle cx="57" cy="47" r="5" fill="#3b82f6"/>
                </g>
            </svg>
        `;

        const contentDiv = document.createElement('div');
        contentDiv.classList.add('message-content');
        contentDiv.innerHTML = `<p>${content}</p>`;

        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);

        chatbotMessages.appendChild(messageDiv);
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    }

    sendChatMessage.addEventListener('click', () => {
        if (chatbotInput.value.trim() !== '') {
            addMessage(chatbotInput.value, true);
            const userText = chatbotInput.value;
            chatbotInput.value = '';

            // Show typing indicator
            const typingId = `typing-${Date.now()}`;
            const typingDiv = document.createElement('div');
            typingDiv.id = typingId;
            typingDiv.className = 'message bot-message';
            typingDiv.innerHTML = `
                <div class="message-avatar">
                    <svg width="18" height="18" viewBox="0 0 96 96" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="48" cy="48" r="44" fill="#e2e8f0"/>
                        <g fill="#1e293b">
                            <path d="M30 58h36c1.7 0 3-1.3 3-3v-8c0-7.7-10.7-14-21-14s-21 6.3-21 14v8c0 1.7 1.3 3 3 3z"/>
                            <circle cx="39" cy="47" r="5" fill="#3b82f6"/>
                            <circle cx="57" cy="47" r="5" fill="#3b82f6"/>
                        </g>
                    </svg>
                </div>
                <div class="message-content">Typing...</div>
            `;
            chatbotMessages.appendChild(typingDiv);
            chatbotMessages.scrollTop = chatbotMessages.scrollHeight;

            // Call backend chatbot API
            fetch('/api/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: userText })
            })
            .then(async (res) => {
                const data = await res.json().catch(() => ({}));
                if (!res.ok) {
                    throw new Error(data.detail || 'Server error');
                }
                return data;
            })
            .then((data) => {
                document.getElementById(typingId)?.remove();
                // If backend indicates to ignore (e.g., simple greeting), do not add a bot reply
                if (data && data.ignore) { return; }
                addMessage(data.reply || 'Sorry, I could not generate a response.');
            })
            .catch((err) => {
                document.getElementById(typingId)?.remove();
                const raw = String(err && err.message ? err.message : 'Unable to reach server');
                const looksLikeGemini = /gemini|api key|permission_denied|403/i.test(raw);
                const msg = looksLikeGemini
                    ? 'Sorry, the AI assistant is temporarily unavailable. Please try again later.'
                    : `Error: ${raw}`;
                addMessage(msg);
            });
        }
    });

    chatbotInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendChatMessage.click();
        }
    });

    // Voice Input Functionality
    const voiceInputBtn = document.getElementById('voiceInputBtn');
    let recognition = null;

    // Initialize speech recognition if available
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        recognition.onstart = () => {
            voiceInputBtn.classList.add('recording');
            voiceInputBtn.innerHTML = '<i class="fas fa-stop"></i>';
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            chatbotInput.value = transcript;
            chatbotInput.focus();
        };

        recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            addMessage('Voice input error. Please try again.');
        };

        recognition.onend = () => {
            voiceInputBtn.classList.remove('recording');
            voiceInputBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        };
    }

    // Voice button click handler
    if (voiceInputBtn) {
        voiceInputBtn.addEventListener('click', () => {
            if (!recognition) {
                addMessage('Voice input is not supported in your browser. Please use Chrome or Edge.');
                return;
            }

            if (voiceInputBtn.classList.contains('recording')) {
                recognition.stop();
            } else {
                recognition.start();
            }
        });
    }
});
