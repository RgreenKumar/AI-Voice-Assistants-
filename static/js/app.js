const chatArea = document.getElementById('chatArea');
const input = document.getElementById('messageInput');
const status = document.getElementById('status');
const historyList = document.getElementById('historyList');
const themeToggle = document.getElementById('themeToggle');
let messages = [];
let isTyping = false;

function showToast(message) {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.style.display = 'block';
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => { toast.style.display = 'none'; }, 2200);
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
}

function renderHistory() {
  historyList.innerHTML = '';
  const userMessages = messages.filter((m) => m.role === 'user').slice(-6);
  userMessages.forEach((m) => {
    const item = document.createElement('div');
    item.className = 'history-item';
    item.textContent = m.content;
    historyList.appendChild(item);
  });
}

function renderMessage(message) {
  const wrap = document.createElement('div');
  wrap.className = `message ${message.role}`;
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  const formatted = escapeHtml(message.content).replace(/\n/g, '<br>');
  bubble.innerHTML = formatted.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>');
  wrap.appendChild(bubble);
  
  // Add voice play button for assistant messages
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
  
  wrap.appendChild(bubble);
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

function addMessage(role, text, source = 'LLM', references = [], timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })) {
  const item = { role, content: text, source, references, timestamp };
  messages.push(item);
  renderMessage(item);
  renderHistory();
  
  // Auto-play voice for assistant messages if enabled
  if (role === 'assistant' && voiceManager) {
    voiceManager.autoPlayMessage(text);
  }
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

function clearChat() {
  messages = [];
  chatArea.innerHTML = '';
  renderHistory();
}

async function sendMessage() {
  const text = input.value.trim();
  if (!text || isTyping) return;
  input.value = '';
  addMessage('user', text);
  setTyping(true);
  try {
    const response = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    });
    const data = await response.json();
    setTyping(false);
    if (data.success) {
      addMessage('assistant', data.content || data.response, data.source, data.references || []);
      status.textContent = `Source: ${data.source || 'LLM'}`;
    } else {
      addMessage('assistant', data.error || 'Something went wrong.');
    }
  } catch (error) {
    setTyping(false);
    addMessage('assistant', 'Network error. Please try again.');
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
  clearChat();
  await fetch('/clear', { method: 'POST' });
  showToast('Chat cleared');
});
themeToggle.addEventListener('click', toggleTheme);

document.getElementById('exportBtn').addEventListener('click', async () => {
  const response = await fetch('/export/txt', { method: 'POST' });
  const data = await response.json();
  showToast(`Exported to ${data.path}`);
});

const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'light') document.body.classList.add('light');

addMessage('assistant', 'Hello 👋 I am your AI Knowledge Assistant. I can help with Wikipedia, latest news, and general conversation.');
