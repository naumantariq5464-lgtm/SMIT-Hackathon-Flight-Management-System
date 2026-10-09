/**
 * SkyFlow AI RAG Policy Assistant Module
 */
const ChatModule = {
  isOpen: false,

  init() {
    const bubble = document.getElementById('ai-chat-bubble');
    const win = document.getElementById('ai-chat-window');
    const footer = document.querySelector('.site-footer');
    if (!bubble || !footer) return;

    // Dynamically lifts the circular AI button slightly above footer
    const handleFooterScroll = () => {
      const footerRect = footer.getBoundingClientRect();
      const windowHeight = window.innerHeight;
      const isMobile = window.innerWidth <= 600;
      const baseBottom = isMobile ? 16 : 24;
      const maxLift = baseBottom + 28; // Subtle 28px lift
      
      // When footer enters the bottom viewport threshold
      if (footerRect.top < windowHeight) {
        const overlap = windowHeight - footerRect.top;
        const liftAmount = Math.min(Math.max(overlap * 0.4 + baseBottom, baseBottom), maxLift);
        bubble.style.bottom = `${liftAmount}px`;
        if (win && !isMobile) {
          win.style.bottom = `${liftAmount + 60}px`;
        }
      } else {
        bubble.style.bottom = '';
        if (win && !isMobile) {
          win.style.bottom = '';
        }
      }
    };

    window.addEventListener('scroll', handleFooterScroll, { passive: true });
    window.addEventListener('resize', handleFooterScroll, { passive: true });
    handleFooterScroll();
  },

  toggleChatWindow() {
    const win = document.getElementById('ai-chat-window');
    if (!win) return;

    ChatModule.isOpen = !ChatModule.isOpen;
    if (ChatModule.isOpen) {
      win.classList.add('active');
      document.getElementById('ai-input-text')?.focus();
    } else {
      win.classList.remove('active');
    }
  },

  async handleSendMessage(event) {
    event.preventDefault();
    const input = document.getElementById('ai-input-text');
    const msgContainer = document.getElementById('ai-chat-messages');
    if (!input || !msgContainer) return;

    const query = input.value.trim();
    if (!query) return;

    // Append User Message
    const userMsgEl = document.createElement('div');
    userMsgEl.className = 'ai-msg ai-msg-user';
    userMsgEl.textContent = query;
    msgContainer.appendChild(userMsgEl);

    input.value = '';
    msgContainer.scrollTop = msgContainer.scrollHeight;

    // Typing indicator
    const botMsgEl = document.createElement('div');
    botMsgEl.className = 'ai-msg ai-msg-bot';
    botMsgEl.innerHTML = '<i>AI is searching policy documents...</i>';
    msgContainer.appendChild(botMsgEl);
    msgContainer.scrollTop = msgContainer.scrollHeight;

    try {
      const response = await API.post('/chat', { query });
      botMsgEl.textContent = response.reply || 'Here is the policy information.';
    } catch (e) {
      botMsgEl.textContent = 'Sorry, I could not retrieve policy information at this moment.';
    } finally {
      msgContainer.scrollTop = msgContainer.scrollHeight;
    }
  }
};
