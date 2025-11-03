// Configuration
const API_BASE_URL = 'http://localhost:8000';

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    setupEventListeners();
});

function setupEventListeners() {
    // Enter key to send
    document.getElementById('queryInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendQuery();
        }
    });
}

async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();

        document.getElementById('systemStatus').textContent = data.status === 'healthy' ? '🟢 Online' : '🔴 Offline';
        document.getElementById('docCount').textContent = data.vector_store_docs;
    } catch (error) {
        console.error('Health check failed:', error);
        document.getElementById('systemStatus').textContent = '🔴 Offline';
    }
}

async function sendQuery() {
    const input = document.getElementById('queryInput');
    const query = input.value.trim();

    if (!query) return;

    // Clear input and disable button
    input.value = '';
    const sendButton = document.getElementById('sendButton');
    sendButton.disabled = true;
    sendButton.innerHTML = '<div class="loading"></div>';

    // Remove welcome message if present
    const welcomeMessage = document.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.remove();
    }

    // Add user message to chat
    addMessage('user', query);

    try {
        // Call API
        const response = await fetch(`${API_BASE_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query }),
        });

        if (!response.ok) {
            throw new Error('API request failed');
        }

        const data = await response.json();

        // Add agent response
        addMessage('agent', data.answer, {
            plan: data.plan,
            tool_outputs: data.tool_outputs,
            reasoning_steps: data.reasoning_steps,
        });

        // Update document count
        checkHealth();

    } catch (error) {
        console.error('Error:', error);
        addMessage('agent', 'Sorry, I encountered an error processing your request. Please try again.');
    } finally {
        // Re-enable button
        sendButton.disabled = false;
        sendButton.textContent = 'Send';
    }
}

function addMessage(type, content, metadata = null) {
    const chatContainer = document.getElementById('chatContainer');

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;

    const header = document.createElement('div');
    header.className = 'message-header';
    header.textContent = type === 'user' ? '👤 You' : '🤖 Agent';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;

    messageDiv.appendChild(header);
    messageDiv.appendChild(contentDiv);

    // Add reasoning section if metadata is provided
    if (metadata && type === 'agent') {
        if (metadata.plan) {
            const planSection = createReasoningSection('Plan', metadata.plan);
            messageDiv.appendChild(planSection);
        }

        if (metadata.tool_outputs && metadata.tool_outputs.length > 0) {
            const toolSection = createReasoningSection(
                'Tool Outputs',
                metadata.tool_outputs.map((output, i) => `${i + 1}. ${output}`).join('\n\n')
            );
            messageDiv.appendChild(toolSection);
        }
    }

    chatContainer.appendChild(messageDiv);

    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function createReasoningSection(title, content) {
    const section = document.createElement('div');
    section.className = 'reasoning-section';

    const header = document.createElement('h4');
    header.textContent = title;
    section.appendChild(header);

    const items = content.split('\n\n');
    items.forEach(item => {
        if (item.trim()) {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'reasoning-item';
            itemDiv.textContent = item;
            section.appendChild(itemDiv);
        }
    });

    return section;
}

// Refresh health status every 30 seconds
setInterval(checkHealth, 30000);
