document.addEventListener('DOMContentLoaded', () => {
  // Debug mode: expose state to console for troubleshooting
  window.DEBUG = {
    lastFetchTime: null,
    lastError: null,
    sessionStatus: null,
    messagesCount: 0
  };

  const serverDot = document.getElementById('server-dot');
  const serverText = document.getElementById('server-text');
  const refreshBtn = document.getElementById('refresh-btn');
  const inboxView = document.getElementById('inbox-view');
  const chatView = document.getElementById('chat-view');
  const chatBackBtn = document.getElementById('chat-back-btn');
  const chatContactName = document.getElementById('chat-contact-name');
  const chatAvatar = document.getElementById('chat-avatar');
  const chatMessagesContainer = document.getElementById('chat-messages');

  const sessionDot = document.getElementById('session-dot');
  const sessionStatus = document.getElementById('session-status');
  const sessionPreview = document.getElementById('session-preview');
  const renewSessionBtn = document.getElementById('renew-session-btn');
  const aboutBtn = document.getElementById('about-btn');
  const aboutModal = document.getElementById('about-modal');
  const closeAboutBtn = document.getElementById('close-about-btn');
  const sessionModal = document.getElementById('session-modal');
  const newSessionInput = document.getElementById('new-session-input');
  const cancelSessionBtn = document.getElementById('cancel-session-btn');
  const saveSessionBtn = document.getElementById('save-session-btn');
  const powerBtn = document.getElementById('power-btn');

  let allMessages = [];
  let lastUpdateTime = null;
  let isPollerEnabled = true;

  // Initialize power button
  browser.storage.local.get({ isPollerEnabled: true }).then(res => {
    isPollerEnabled = res.isPollerEnabled;
    updatePowerBtn();
  });

  function updatePowerBtn() {
    if (isPollerEnabled) {
      powerBtn.classList.remove('paused');
      powerBtn.title = "Poller is ON (Click to turn OFF)";
    } else {
      powerBtn.classList.add('paused');
      powerBtn.title = "Poller is OFF (Click to turn ON)";
    }
  }

  // ── Session Management ──────────────────────────────────────────────────────

  let isPremiumMode = false;

  async function checkSessionStatus() {
    try {
      const data = await browser.runtime.sendNativeMessage(
        "com.linuxayan.ig_poller",
        { action: "get_session" }
      );
      isPremiumMode = true;
      if (data.status === "ok") {
        updateSessionUI(data.has_session, data.session_preview);
        window.DEBUG.sessionStatus = data.has_session ? 'valid' : 'invalid';
        if (!data.has_session) {
          setTimeout(showSessionModal, 600);
        }
        return data.has_session;
      } else {
        updateSessionUI(false, "");
        window.DEBUG.sessionStatus = 'error';
        return false;
      }
    } catch (err) {
      // Freemium Mode
      isPremiumMode = false;
      updateSessionUI(true, "Browser auto-auth");
      window.DEBUG.sessionStatus = 'valid';
      showFreemiumBanner();
      return true;
    }
  }

  function showFreemiumBanner() {
    let banner = document.getElementById('freemium-banner');
    if (!banner) {
      banner = document.createElement('div');
      banner.id = 'freemium-banner';
      banner.innerHTML = `
        <div style="background: linear-gradient(90deg, #833ab4, #fd1d1d, #fcb045); padding: 10px; color: white; text-align: center; font-size: 12px; font-weight: 600; border-radius: 8px; margin-bottom: 12px; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; box-shadow: 0 4px 15px rgba(225, 48, 108, 0.3);">
          <i class="fas fa-rocket"></i> Get 24/7 background polling & notifications (Free Pro setup)
        </div>
      `;
      banner.addEventListener('click', () => {
        browser.tabs.create({ url: "https://github.com/linuxayan/ig_poller" });
      });
      document.querySelector('.header').after(banner);
    }
  }

  function updateSessionUI(valid, preview) {
    sessionDot.classList.remove('valid', 'invalid');

    if (valid) {
      sessionStatus.textContent = 'Active';
      sessionStatus.className = 'session-status valid';
      sessionDot.classList.add('valid');
      sessionPreview.textContent = preview ? `(${preview})` : '';
      sessionPreview.title = 'Session valid';
    } else {
      sessionStatus.textContent = 'Expired';
      sessionStatus.className = 'session-status invalid';
      sessionDot.classList.add('invalid');
      sessionPreview.textContent = '';
    }
  }

  function showSessionModal() {
    sessionModal.style.display = 'flex';
    newSessionInput.value = '';
    newSessionInput.focus();
  }

  function hideSessionModal() {
    sessionModal.style.display = 'none';
  }

  async function saveNewSession() {
    const newSession = newSessionInput.value.trim();
    if (!newSession) {
      showToast('Please paste a session ID', 'error');
      return;
    }

    if (newSession.length < 20) {
      showToast('Session ID looks too short', 'error');
      return;
    }

    saveSessionBtn.disabled = true;
    saveSessionBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

    try {
      const data = await browser.runtime.sendNativeMessage(
        "com.linuxayan.ig_poller",
        { action: "set_session", session_id: newSession }
      );
      hideSessionModal();

      if (data.status === "ok") {
        await checkSessionStatus();
        loadMessages();
        showToast('Session saved! Restart poller to apply.', 'success');
      } else {
        showToast('Failed: ' + (data.message || 'Unknown error'), 'error');
      }
    } catch (err) {
      hideSessionModal();
      showToast('Error: ' + err.message, 'error');
    } finally {
      saveSessionBtn.disabled = false;
      saveSessionBtn.innerHTML = '<i class="fas fa-check"></i> Save & Restart';
    }
  }

  // ── Toast Notifications ─────────────────────────────────────────────────────

  function showToast(message, type = 'info') {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
      <span>${message}</span>
    `;

    document.body.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('show'));

    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 300);
    }, type === 'error' ? 5000 : 3000);
  }

  // ── Server / Message Handling ───────────────────────────────────────────────

  let refreshTimeout = null;

  function setServerStatus(connected, type = 'Native Host') {
    if (connected) {
      serverDot.classList.add('online');
      serverText.textContent = `Connected (${type})`;
    } else {
      serverDot.classList.remove('online');
      serverText.textContent = 'Disconnected';
    }
  }

  function formatTime(isoString) {
    if (!isoString) return '';
    try {
      const date = new Date(isoString);
      const now = new Date();
      const diffMs = now - date;
      const diffMins = Math.floor(diffMs / 60000);

      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;

      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) return `${diffHours}h ago`;

      const diffDays = Math.floor(diffHours / 24);
      if (diffDays < 7) return `${diffDays}d ago`;

      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    } catch (e) {
      return isoString;
    }
  }

  function getAvatarInitial(name) {
    const clean = name.replace(/[^a-zA-Z0-9]/g, '').trim();
    return clean ? clean.charAt(0).toUpperCase() : '?';
  }

  function getAvatarColor(name) {
    const colors = [
      'linear-gradient(135deg, #f58529, #dd2a7b)',
      'linear-gradient(135deg, #405de6, #5851db)',
      'linear-gradient(135deg, #00ba7c, #00b4a0)',
      'linear-gradient(135deg, #e1306c, #cc2a6c)',
      'linear-gradient(135deg, #833ab4, #9c50c4)',
      'linear-gradient(135deg, #f77737, #e1306c)',
    ];
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }
    return colors[Math.abs(hash) % colors.length];
  }

  function openChat(sender, isAutoRefresh = false) {
    inboxView.style.display = 'none';
    chatView.style.display = 'flex';
    chatContactName.textContent = sender;
    chatAvatar.textContent = getAvatarInitial(sender);
    chatAvatar.style.background = getAvatarColor(sender);

    const threadMsgs = allMessages.filter(m => m.sender === sender).reverse();

    if (isAutoRefresh && chatMessagesContainer.children.length > 0 && threadMsgs.length > 0) {
      const lastRenderedMsgId = chatMessagesContainer.lastElementChild.dataset.msgId;
      if (lastRenderedMsgId === threadMsgs[threadMsgs.length - 1].msg_id) {
        return;
      }
    }

    chatMessagesContainer.innerHTML = '';
    threadMsgs.forEach((msg, idx) => {
      const isSent = msg.direction === 'sent';
      const bubble = document.createElement('div');
      bubble.className = `chat-bubble ${isSent ? 'sent' : 'received'}`;
      bubble.dataset.msgId = msg.msg_id;
      bubble.style.animationDelay = `${idx * 30}ms`;
      bubble.innerHTML = `
        <div class="msg-text">${escapeHtml(msg.message)}</div>
        <div class="chat-time">${formatTime(msg.saved_at)}</div>
      `;
      chatMessagesContainer.appendChild(bubble);
    });

    requestAnimationFrame(() => {
      chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
    });
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function renderInbox(messages) {
    if (!messages || messages.length === 0) {
      inboxView.innerHTML = `
        <div class="empty-state">
          <i class="far fa-comments"></i>
          <div>No recent messages</div>
          <div style="font-size:11px;margin-top:4px;opacity:0.6">Start chatting on Instagram to see messages here</div>
        </div>
      `;
      return;
    }

    const grouped = {};
    messages.forEach(msg => {
      const contact = msg.sender;
      if (!grouped[contact]) {
        grouped[contact] = [];
      }
      grouped[contact].push(msg);
    });

    inboxView.innerHTML = '';

    const sortedContacts = Object.keys(grouped).sort((a, b) => {
      const tA = new Date(grouped[a][0].saved_at).getTime();
      const tB = new Date(grouped[b][0].saved_at).getTime();
      return tB - tA;
    });

    sortedContacts.forEach(contact => {
      const latestMsg = grouped[contact][0];
      const isSent = latestMsg.direction === 'sent';
      const timeAgo = formatTime(latestMsg.saved_at);

      const row = document.createElement('div');
      row.className = 'inbox-row';
      row.innerHTML = `
        <div class="inbox-avatar" style="background: ${getAvatarColor(contact)}">${getAvatarInitial(contact)}</div>
        <div class="inbox-details">
          <div class="inbox-header">
            <span class="inbox-name">${escapeHtml(contact)}</span>
            <span class="inbox-time">${escapeHtml(timeAgo)}</span>
          </div>
          <div class="inbox-preview">
            ${isSent ? '<i class="fas fa-paper-plane sent-icon" style="font-size:10px;margin-right:4px;color:var(--primary)"></i>' : ''}
            ${escapeHtml(latestMsg.message.length > 70 ? latestMsg.message.substring(0, 70) + '...' : latestMsg.message)}
          </div>
        </div>
        ${!isSent ? '<div class="unread-indicator"></div>' : ''}
      `;
      row.addEventListener('click', () => openChat(contact));
      inboxView.appendChild(row);
    });
  }

  async function loadMessages() {
    try {
      if (isPremiumMode) {
        const data = await browser.runtime.sendNativeMessage(
          "com.linuxayan.ig_poller",
          { action: "get_data" }
        );
        setServerStatus(true, "Pro Mode");
        allMessages = data.messages || [];
      } else {
        const res = await browser.storage.local.get(["freemiumMessages", "igFetchError"]);
        allMessages = res.freemiumMessages || [];
        setServerStatus(true, "Free Mode");

        if (res.igFetchError === "not_logged_in" && allMessages.length === 0) {
          throw new Error("NOT_LOGGED_IN");
        }
      }
      lastUpdateTime = Date.now();
      window.DEBUG.lastFetchTime = new Date().toISOString();
      window.DEBUG.messagesCount = allMessages.length;

      if (inboxView.style.display !== 'none') {
        renderInbox(allMessages);
      } else {
        const currentChat = chatContactName.textContent;
        if (currentChat) {
          openChat(currentChat, true);
        }
      }

      if (allMessages.length > 0) {
        browser.runtime.sendMessage({
          action: "clearBadge",
          latestMsgId: allMessages[0].msg_id
        }).catch(() => { });
      }
    } catch (err) {
      console.error("Data Fetch Error:", err);
      setServerStatus(false);
      window.DEBUG.lastError = err.message;

      if (!isPremiumMode && err.message === "NOT_LOGGED_IN") {
        inboxView.innerHTML = `
          <div class="empty-state">
            <i class="fas fa-cookie-bite"></i>
            <div>Please log into Instagram.com first</div>
            <div style="font-size:11px;margin-top:4px;opacity:0.6">The Free mode relies on your browser session</div>
          </div>
        `;
      } else if (!isPremiumMode && allMessages.length === 0) {
        inboxView.innerHTML = `
          <div class="empty-state">
            <i class="fas fa-exclamation-triangle"></i>
            <div>Error fetching messages</div>
            <div style="font-size:11px;margin-top:4px;opacity:0.6">${escapeHtml(err.message)}</div>
          </div>
        `;
      } else if (isPremiumMode) {
        inboxView.innerHTML = `
          <div class="empty-state">
            <i class="fas fa-plug"></i>
            <div>Could not connect to native host</div>
            <div style="font-size:11px;margin-top:4px;opacity:0.6">Make sure you ran:<br><code>python3 main.py --install-ext</code></div>
          </div>
        `;
      }
    }
  }

  powerBtn.addEventListener('click', () => {
    isPollerEnabled = !isPollerEnabled;
    browser.storage.local.set({ isPollerEnabled });
    updatePowerBtn();
    if (isPollerEnabled) {
      refreshBtn.click();
    }
  });

  refreshBtn.addEventListener('click', () => {
    refreshBtn.classList.add('spinning');
    const fetchPromise = !isPremiumMode
      ? browser.runtime.sendMessage({ action: "forceFetch" }).catch(() => { })
      : Promise.resolve();

    fetchPromise.then(() => loadMessages()).finally(() => {
      setTimeout(() => refreshBtn.classList.remove('spinning'), 500);
    });
  });

  // Keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
      e.preventDefault();
      refreshBtn.classList.add('spinning');
      const fetchPromise = !isPremiumMode
        ? browser.runtime.sendMessage({ action: "forceFetch" }).catch(() => { })
        : Promise.resolve();

      fetchPromise.then(() => loadMessages()).finally(() => {
        setTimeout(() => refreshBtn.classList.remove('spinning'), 500);
      });
    }
    if (e.key === 'Escape') {
      hideSessionModal();
      aboutModal.style.display = 'none';
    }
  });

  chatBackBtn.addEventListener('click', () => {
    chatView.style.display = 'none';
    inboxView.style.display = 'flex';
    renderInbox(allMessages);
  });

  aboutBtn.addEventListener('click', () => {
    aboutModal.style.display = 'flex';
  });

  closeAboutBtn.addEventListener('click', () => {
    aboutModal.style.display = 'none';
  });

  aboutModal.addEventListener('click', (e) => {
    if (e.target === aboutModal) {
      aboutModal.style.display = 'none';
    }
  });

  renewSessionBtn.addEventListener('click', showSessionModal);
  cancelSessionBtn.addEventListener('click', hideSessionModal);
  saveSessionBtn.addEventListener('click', saveNewSession);

  newSessionInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      saveNewSession();
    }
  });

  sessionModal.addEventListener('click', (e) => {
    if (e.target === sessionModal) {
      hideSessionModal();
    }
  });

  // ── Initialization ───────────────────────────────────────────────────────────

  checkSessionStatus().then(() => {
    loadMessages();
  });

  // Poll every 5 seconds
  setInterval(() => {
    if (isPollerEnabled) {
      loadMessages();
    }
  }, 5000);
});
