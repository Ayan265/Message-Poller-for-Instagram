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
      // Free Mode — no native host available
      isPremiumMode = false;

      // Check if user has saved a session ID
      const res = await browser.storage.local.get("freeSessionId");
      const savedSession = res.freeSessionId || "";

      if (savedSession) {
        const preview = savedSession.substring(0, 10) + "...";
        updateSessionUI(true, preview);
        window.DEBUG.sessionStatus = 'valid';
        return true;
      } else {
        updateSessionUI(false, "");
        window.DEBUG.sessionStatus = 'no_session';
        setTimeout(showSessionModal, 600);
        return false;
      }
    }
  }

  function updateSessionUI(valid, preview) {
    sessionDot.classList.remove('valid', 'invalid');

    if (valid) {
      sessionStatus.textContent = 'Active';
      sessionStatus.className = 'session-status valid';
      sessionDot.classList.add('valid');
      sessionPreview.textContent = preview ? '(' + preview + ')' : '';
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
    saveSessionBtn.textContent = 'Saving...';

    try {
      if (isPremiumMode) {
        // Pro Mode: send to native host
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
      } else {
        // Free Mode: save sessionid to extension storage
        // The background script's webRequest interceptor will pick it up
        // and inject it into all Instagram API requests automatically
        await browser.storage.local.set({ freeSessionId: newSession });
        hideSessionModal();
        await checkSessionStatus();
        showToast('Session saved! Fetching messages...', 'success');

        // Force an immediate background fetch
        browser.runtime.sendMessage({ action: "forceFetch" }).catch(() => {});
        setTimeout(() => loadMessages(), 1500);
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

  function showToast(message, type) {
    type = type || 'info';
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'toast toast-' + type;
    const icon = document.createElement('i');
    if (type === 'success') icon.className = 'fas fa-check-circle';
    else if (type === 'error') icon.className = 'fas fa-exclamation-circle';
    else icon.className = 'fas fa-info-circle';

    const span = document.createElement('span');
    span.textContent = message;
    toast.appendChild(icon);
    toast.appendChild(span);

    document.body.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('show'));

    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 300);
    }, type === 'error' ? 5000 : 3000);
  }

  // ── Server / Message Handling ───────────────────────────────────────────────

  function setServerStatus(connected, type) {
    type = type || 'Native Host';
    if (connected) {
      serverDot.classList.add('online');
      serverText.textContent = 'Connected (' + type + ')';
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
      if (diffMins < 60) return diffMins + 'm ago';

      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) return diffHours + 'h ago';

      const diffDays = Math.floor(diffHours / 24);
      if (diffDays < 7) return diffDays + 'd ago';

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

  function openChat(sender, isAutoRefresh) {
    isAutoRefresh = isAutoRefresh || false;
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
      bubble.className = 'chat-bubble ' + (isSent ? 'sent' : 'received');
      bubble.dataset.msgId = msg.msg_id;
      bubble.style.animationDelay = (idx * 30) + 'ms';
      const textDiv = document.createElement('div');
      textDiv.className = 'msg-text';
      textDiv.textContent = msg.message;

      const timeDiv = document.createElement('div');
      timeDiv.className = 'chat-time';
      timeDiv.textContent = formatTime(msg.saved_at);

      bubble.appendChild(textDiv);
      bubble.appendChild(timeDiv);
      chatMessagesContainer.appendChild(bubble);
    });

    requestAnimationFrame(() => {
      chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
    });
  }

  function renderInbox(messages) {
    if (!messages || messages.length === 0) {
      inboxView.innerHTML = '';
      const emptyDiv = document.createElement('div');
      emptyDiv.className = 'empty-state';
      const emptyIcon = document.createElement('i');
      emptyIcon.className = 'far fa-comments';
      const emptyText = document.createElement('div');
      emptyText.textContent = 'No recent messages';
      const emptyHint = document.createElement('div');
      emptyHint.style.cssText = 'font-size:11px;margin-top:4px;opacity:0.6';
      emptyHint.textContent = 'Start chatting on Instagram to see messages here';
      emptyDiv.appendChild(emptyIcon);
      emptyDiv.appendChild(emptyText);
      emptyDiv.appendChild(emptyHint);
      inboxView.appendChild(emptyDiv);
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
      const avatarDiv = document.createElement('div');
      avatarDiv.className = 'inbox-avatar';
      avatarDiv.style.background = getAvatarColor(contact);
      avatarDiv.textContent = getAvatarInitial(contact);

      const detailsDiv = document.createElement('div');
      detailsDiv.className = 'inbox-details';

      const headerDiv = document.createElement('div');
      headerDiv.className = 'inbox-header';

      const nameSpan = document.createElement('span');
      nameSpan.className = 'inbox-name';
      nameSpan.textContent = contact;

      const timeSpan = document.createElement('span');
      timeSpan.className = 'inbox-time';
      timeSpan.textContent = timeAgo;

      headerDiv.appendChild(nameSpan);
      headerDiv.appendChild(timeSpan);

      const previewDiv = document.createElement('div');
      previewDiv.className = 'inbox-preview';

      if (isSent) {
        const sentIcon = document.createElement('i');
        sentIcon.className = 'fas fa-paper-plane sent-icon';
        sentIcon.style.cssText = 'font-size:10px;margin-right:4px;color:var(--primary)';
        previewDiv.appendChild(sentIcon);
      }

      const previewText = latestMsg.message.length > 70
        ? latestMsg.message.substring(0, 70) + '...'
        : latestMsg.message;
      const msgText = document.createTextNode(previewText);
      previewDiv.appendChild(msgText);

      detailsDiv.appendChild(headerDiv);
      detailsDiv.appendChild(previewDiv);

      row.appendChild(avatarDiv);
      row.appendChild(detailsDiv);

      if (!isSent) {
        const unreadInd = document.createElement('div');
        unreadInd.className = 'unread-indicator';
        row.appendChild(unreadInd);
      }
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

        if (res.igFetchError === "no_session" && allMessages.length === 0) {
          throw new Error("NO_SESSION");
        }
        if (res.igFetchError === "session_expired" && allMessages.length === 0) {
          throw new Error("SESSION_EXPIRED");
        }
        if (res.igFetchError && allMessages.length === 0) {
          throw new Error(res.igFetchError);
        }
        setServerStatus(true, "Free Mode");
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
        }).catch(() => {});
      }
    } catch (err) {
      console.error("Data Fetch Error:", err);
      setServerStatus(false);
      window.DEBUG.lastError = err.message;

      inboxView.innerHTML = '';
      const emptyState = document.createElement('div');
      emptyState.className = 'empty-state';

      if (!isPremiumMode && err.message === "NO_SESSION") {
        const icon = document.createElement('i');
        icon.className = 'fas fa-key';
        const title = document.createElement('div');
        title.textContent = 'Session ID required';
        const hint = document.createElement('div');
        hint.style.cssText = 'font-size:11px;margin-top:4px;opacity:0.6';
        hint.textContent = 'Click "Renew" above to paste your Instagram sessionid';
        emptyState.appendChild(icon);
        emptyState.appendChild(title);
        emptyState.appendChild(hint);
      } else if (!isPremiumMode && err.message === "SESSION_EXPIRED") {
        const icon = document.createElement('i');
        icon.className = 'fas fa-clock';
        const title = document.createElement('div');
        title.textContent = 'Session expired';
        const hint = document.createElement('div');
        hint.style.cssText = 'font-size:11px;margin-top:4px;opacity:0.6';
        hint.textContent = 'Your session has expired. Click "Renew" to paste a fresh sessionid';
        emptyState.appendChild(icon);
        emptyState.appendChild(title);
        emptyState.appendChild(hint);
      } else if (isPremiumMode) {
        const icon = document.createElement('i');
        icon.className = 'fas fa-plug';
        const title = document.createElement('div');
        title.textContent = 'Could not connect to native host';
        const hint = document.createElement('div');
        hint.style.cssText = 'font-size:11px;margin-top:4px;opacity:0.6';
        hint.innerHTML = 'Make sure you ran:<br><code>python3 main.py --install-ext</code>';
        emptyState.appendChild(icon);
        emptyState.appendChild(title);
        emptyState.appendChild(hint);
      } else {
        const icon = document.createElement('i');
        icon.className = 'fas fa-exclamation-triangle';
        const title = document.createElement('div');
        title.textContent = 'Error fetching messages';
        const hint = document.createElement('div');
        hint.style.cssText = 'font-size:11px;margin-top:4px;opacity:0.6';
        hint.textContent = err.message;
        emptyState.appendChild(icon);
        emptyState.appendChild(title);
        emptyState.appendChild(hint);
      }

      inboxView.appendChild(emptyState);
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
    browser.runtime.sendMessage({ action: "forceFetch" }).catch(() => {});
    setTimeout(() => {
      loadMessages().finally(() => {
        setTimeout(() => refreshBtn.classList.remove('spinning'), 500);
      });
    }, 800);
  });

  // Keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
      e.preventDefault();
      refreshBtn.click();
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

  // Poll every 5 seconds for updated messages from storage
  setInterval(() => {
    if (isPollerEnabled) {
      loadMessages();
    }
  }, 5000);
});
