const setup = document.querySelector('#setup');
const chat = document.querySelector('#chat');
const cardSelect = document.querySelector('#card');
const personaSelect = document.querySelector('#persona');
const messages = document.querySelector('#messages');
const turns = document.querySelector('#turns');
const input = document.querySelector('#message');
let sessionToken = null;

function appendMessage(text, role) {
  const node = document.createElement('p');
  node.className = `message ${role}`;
  node.textContent = text;
  messages.append(node);
  node.scrollIntoView({ behavior: 'smooth', block: 'end' });
}

function reset() {
  sessionToken = null;
  messages.replaceChildren();
  chat.classList.add('hidden');
  setup.classList.remove('hidden');
}

async function request(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || '요청을 처리하지 못했어요.');
  return data;
}

async function initialize() {
  try {
    const catalog = await request('/api/catalog');
    catalog.cards.forEach((code) => cardSelect.add(new Option(code, code)));
    catalog.personas.forEach((persona) => {
      personaSelect.add(new Option(`${persona.name} — ${persona.tagline}`, persona.code));
    });
    const requested = new URLSearchParams(location.search).get('card');
    if (requested && catalog.cards.includes(requested)) cardSelect.value = requested;
  } catch (error) {
    setup.innerHTML = `<p>잠시 후 다시 시도해 주세요. ${error.message}</p>`;
  }
}

document.querySelector('#start').addEventListener('click', async () => {
  try {
    const data = await request('/api/session', {
      method: 'POST',
      body: JSON.stringify({ card: cardSelect.value, persona: personaSelect.value }),
    });
    sessionToken = data.session;
    document.querySelector('#friend-name').textContent = data.persona.name;
    document.querySelector('#friend-tagline').textContent = data.persona.tagline;
    turns.textContent = `${data.remaining_turns}턴 남음`;
    appendMessage(data.notice, 'notice-message');
    appendMessage(data.reply, 'friend-message');
    setup.classList.add('hidden');
    chat.classList.remove('hidden');
    input.focus();
  } catch (error) {
    alert(error.message);
  }
});

document.querySelector('#chat-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message || !sessionToken) return;
  appendMessage(message, 'user-message');
  input.value = '';
  try {
    const data = await request('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ session: sessionToken, message }),
    });
    appendMessage(data.reply, 'friend-message');
    sessionToken = data.session;
    turns.textContent = data.complete ? '대화 종료' : `${data.remaining_turns}턴 남음`;
    input.disabled = data.complete;
  } catch (error) {
    appendMessage(error.message, 'notice-message');
    input.disabled = true;
    sessionToken = null;
  }
});

document.querySelector('#end').addEventListener('click', () => {
  input.disabled = false;
  reset();
});
window.addEventListener('pagehide', () => { sessionToken = null; });
initialize();
