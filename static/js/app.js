const chatArea = document.getElementById('chatArea');
const input = document.getElementById('messageInput');
const status = document.getElementById('status');
const historyList = document.getElementById('historyList');
const themeToggle = document.getElementById('themeToggle');
let messages = [];
let activeConversationId = null;
let isTyping = false;
let historyEntries = [];

function showToast(message) {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.style.display = 'block';
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => { toast.style.display = 'none'; }, 2200);
}

function escapeHtml(value) {
  return String(value || '').replace(/[&<>"']/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
}

function renderMessage(message) {
  const wrap = document.createElement('div');
  wrap.className = `message ${message.role}`;
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  const formatted = escapeHtml(message.content).replace(/\n/g, '<br>');
  bubble.innerHTML = formatted.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>');
  wrap.appendChild(bubble);

  if (message.role === 'assistant') {
    const voiceContainer = document.createElement('div');
    voiceContainer.className = 'voice-controls';
    const playBtn = document.createElement('button');
    playBtn.className = 'btn-voice-play';
    playBtn.innerHTML = '🔊';
    playBtn.title = 'Play voice';
    playBtn.addEventListener('click', () => {
      playVoiceOutput(message.content);
      playBtn.classList.toggle('playing');
    });
    voiceContainer.appendChild(playBtn);
    bubble.appendChild(voiceContainer);
  }

  const meta = document.createElement('div');
  meta.className = 'meta-row';
  meta.innerHTML = `<span>${message.timestamp || ''}</span><span class="badge">${message.source || 'LLM'}</span>`;
  wrap.appendChild(meta);
  if (message.references && message.references.length) {
    const refs = document.createElement('div');
    refs.className = 'references';
    message.references.forEach((ref) => {
      const a = document.createElement('a');
      a.href = ref.url;
      a.target = '_blank';
      a.rel = 'noopener';
      a.textContent = ref.title;
      refs.appendChild(a);
    });
    wrap.appendChild(refs);
  }
  chatArea.appendChild(wrap);
  chatArea.scrollTop = chatArea.scrollHeight;
}

function renderConversationMessages(conversationMessages) {
  messages = conversationMessages || [];
  chatArea.innerHTML = '';
  messages.forEach(renderMessage);
  chatArea.scrollTop = chatArea.scrollHeight;
}

function renderHistory() {
  historyList.innerHTML = '';
  if (!historyEntries.length) {
    const empty = document.createElement('div');
    empty.className = 'history-preview';
    empty.textContent = 'No saved chats yet';
    historyList.appendChild(empty);
    return;
  }

  historyEntries.forEach((conversation) => {
    const item = document.createElement('button');
    item.className = `history-item${activeConversationId === conversation.id ? ' active' : ''}`;
    item.type = 'button';
    item.innerHTML = `<span class="history-title">${escapeHtml(conversation.title || 'New chat')}</span><span class="history-preview">${escapeHtml(conversation.preview || 'No messages yet')}</span>`;
    item.addEventListener('click', () => loadConversation(conversation.id));
    historyList.appendChild(item);
  });
}

function setTyping(state) {
  if (state) {
    isTyping = true;
    const typing = document.createElement('div');
    typing.className = 'message';
    typing.id = 'typingIndicator';
    typing.innerHTML = '<div class="bubble typing">Thinking…</div>';
    chatArea.appendChild(typing);
    chatArea.scrollTop = chatArea.scrollHeight;
  } else {
    isTyping = false;
    const typing = document.getElementById('typingIndicator');
    if (typing) typing.remove();
  }
}

function showWelcomeMessage() {
  chatArea.innerHTML = '';
  const wrap = document.createElement('div');
  wrap.className = 'message assistant';
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = 'Hello 👋 I am your AI Knowledge Assistant. I can help with Wikipedia, latest news, and general conversation.';
  wrap.appendChild(bubble);
  chatArea.appendChild(wrap);
}

function clearCurrentChat() {
  messages = [];
  activeConversationId = null;
  chatArea.innerHTML = '';
  showWelcomeMessage();
}

async function loadHistory() {
  try {
    const response = await fetch('/history');
    const data = await response.json();
    if (data.success) {
      historyEntries = data.history || [];
      renderHistory();
    }
  } catch (error) {
    console.error(error);
  }
}

async function loadConversation(conversationId) {
  try {
    const response = await fetch(`/conversation/${conversationId}`);
    const data = await response.json();
    if (!data.success) throw new Error(data.error || 'Conversation not found');
    activeConversationId = conversationId;
    renderConversationMessages(data.conversation?.messages || []);
    status.textContent = 'Loaded previous chat';
    await loadHistory();
  } catch (error) {
    showToast('Unable to load that chat');
  }
}

async function sendMessage() {
  const text = input.value.trim();
  if (!text || isTyping) return;
  input.value = '';

  const tempMessage = { role: 'user', content: text, timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }), source: 'You' };
  renderConversationMessages([...messages, tempMessage]);
  setTyping(true);

  try {
    const response = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, conversation_id: activeConversationId })
    });
    const data = await response.json();
    setTyping(false);
    if (data.success) {
      activeConversationId = data.conversation_id || activeConversationId;
      renderConversationMessages(data.conversation?.messages || [...messages]);
      status.textContent = `Source: ${data.source || 'LLM'}`;
      await loadHistory();
      if (voiceManager) {
        voiceManager.autoPlayMessage(data.content || '');
      }
    } else {
      messages = messages.filter((item) => item !== tempMessage);
      renderConversationMessages(messages);
      showToast(data.error || 'Something went wrong.');
    }
  } catch (error) {
    setTyping(false);
    messages = messages.filter((item) => item !== tempMessage);
    renderConversationMessages(messages);
    showToast('Network error. Please try again.');
  }
}

function toggleTheme() {
  document.body.classList.toggle('light');
  const isLight = document.body.classList.contains('light');
  localStorage.setItem('theme', isLight ? 'light' : 'dark');
}

input.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
});

document.getElementById('sendBtn').addEventListener('click', sendMessage);
document.getElementById('clearBtn').addEventListener('click', async () => {
  const conversationIdToClear = activeConversationId;
  clearCurrentChat();
  await fetch('/clear', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ conversation_id: conversationIdToClear })
  });
  activeConversationId = null;
  await loadHistory();
  showToast('Chat cleared');
});
document.getElementById('newChatBtn').addEventListener('click', () => {
  clearCurrentChat();
  loadHistory();
});
themeToggle.addEventListener('click', toggleTheme);

document.getElementById('exportBtn').addEventListener('click', async () => {
  const response = await fetch('/export/txt', { method: 'POST' });
  const data = await response.json();
  showToast(`Exported to ${data.path}`);
});

const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'light') document.body.classList.add('light');

showWelcomeMessage();
loadHistory();
