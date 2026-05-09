const POLL_INTERVAL_MINUTES = 0.3; // ~18 seconds
const NATIVE_APP = "com.linuxayan.ig_poller";

// ── State ────────────────────────────────────────────────────────────────────
let lastSeenMsgId = null;
let currentSessionId = "";

// ── Load saved state on startup ──────────────────────────────────────────────
browser.storage.local.get(["lastSeenMsgId", "freeSessionId"]).then(res => {
  if (res.lastSeenMsgId) lastSeenMsgId = res.lastSeenMsgId;
  if (res.freeSessionId) currentSessionId = res.freeSessionId;
  console.log("[MsgPoller] Startup. SessionId loaded:", currentSessionId ? currentSessionId.substring(0,10)+"..." : "(none)");

  browser.alarms.create("pollMessages", { periodInMinutes: POLL_INTERVAL_MINUTES });
  checkForNewMessages();
});

// Keep currentSessionId in sync when popup saves a new one
browser.storage.onChanged.addListener((changes, area) => {
  if (area === "local" && changes.freeSessionId) {
    currentSessionId = changes.freeSessionId.newValue || "";
    // Immediately poll when a new session is saved
    if (currentSessionId) checkForNewMessages();
  }
});

// ── webRequest interceptor ───────────────────────────────────────────────────
// This is the KEY to standalone Free Mode. Firefox isolates extension background
// fetch() from page cookies. We intercept the outgoing request and manually
// inject the sessionid cookie + proper headers so Instagram thinks it's a
// normal same-origin browser request.
browser.webRequest.onBeforeSendHeaders.addListener(
  function(details) {
    if (details.tabId !== -1 || !currentSessionId) return {};

    // Inject sessionid cookie
    let cookieValue = "";
    let cookieIdx = -1;
    for (let i = 0; i < details.requestHeaders.length; i++) {
      if (details.requestHeaders[i].name.toLowerCase() === "cookie") {
        cookieValue = details.requestHeaders[i].value;
        cookieIdx = i;
        break;
      }
    }
    if (!cookieValue.includes("sessionid=")) {
      cookieValue += (cookieValue ? "; " : "") + "sessionid=" + currentSessionId;
    }
    if (cookieIdx >= 0) {
      details.requestHeaders[cookieIdx].value = cookieValue;
    } else {
      details.requestHeaders.push({ name: "Cookie", value: cookieValue });
    }

    // Log all headers for debugging
    const summary = details.requestHeaders.map(h => h.name + "=" + (h.name.toLowerCase() === "cookie" ? h.value.substring(0, 40) + "..." : h.value)).join(" | ");
    console.log("[MsgPoller] HEADERS:", summary);

    return { requestHeaders: details.requestHeaders };
  },
  { urls: ["*://*.instagram.com/*"] },
  ["blocking", "requestHeaders"]
);

// ── Alarm handler ────────────────────────────────────────────────────────────
browser.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "pollMessages") checkForNewMessages();
});

// ── Main polling entrypoint ──────────────────────────────────────────────────
async function checkForNewMessages() {
  const settings = await browser.storage.local.get({ isPollerEnabled: true });
  if (!settings.isPollerEnabled) return;

  // 1. Try Pro Mode (native host + main.py running)
  try {
    const data = await browser.runtime.sendNativeMessage(NATIVE_APP, { action: "get_data" });
    if (data && data.messages) {
      console.log("[MsgPoller] Pro Mode: got", data.messages.length, "messages from native host");
      await browser.storage.local.set({ isPremiumMode: true });
      processMessagesForBadge(data.messages);
      return;
    }
    console.log("[MsgPoller] Native host responded but no messages:", JSON.stringify(data).substring(0,100));
  } catch (err) {
    console.log("[MsgPoller] Native host not available:", err.message, "→ using Free Mode");
  }

  // 2. Free Mode (direct API polling with saved sessionid)
  await browser.storage.local.set({ isPremiumMode: false });

  if (!currentSessionId) {
    console.log("[MsgPoller] Free Mode: no sessionId saved. Waiting for user to paste one.");
    await browser.storage.local.set({ igFetchError: "no_session" });
    return;
  }

  console.log("[MsgPoller] Free Mode: polling with sessionId", currentSessionId.substring(0,10)+"...");
  await pollInstagramDirectly();
}

// ── Message text extraction ──────────────────────────────────────────────────
function extractMessageText(item) {
  const itemType = item.item_type || "";
  if (itemType === "text") return (item.text || "").trim();
  if (["voice_media", "clip"].includes(itemType)) return "🎤 [Voice Message]";
  if (["media", "raven_media", "visual_media"].includes(itemType)) return "📷 [Photo/Video]";
  if (itemType === "like") return "❤️ [Liked a message]";
  if (itemType === "animated_media") return "🎞️ [GIF/Sticker]";
  if (itemType === "reel_share") return "🔄 [Shared a Reel]";
  if (itemType === "link") return "🔗 [Link]";
  if (itemType === "action_log") return `ℹ️ [${item.action_log?.description || 'Action'}]`;
  if (itemType === "placeholder") return `ℹ️ [Placeholder: ${item.placeholder?.message || 'Message'}]`;
  return `📦 [${itemType}]`;
}

// ── Free Mode: Direct Instagram API polling ──────────────────────────────────
// Works exactly like main.py — sends sessionid cookie with API requests.
// The webRequest interceptor above handles injecting the cookie.
async function pollInstagramDirectly() {
  try {
    const headers = {
      "X-IG-App-ID": "936619743392459",
      "X-Requested-With": "XMLHttpRequest",
      "Accept": "*/*",
      "Accept-Language": "en-US,en;q=0.9"
    };

    // Step 1: Get current user ID
    console.log("[MsgPoller] Free Mode: fetching current_user...");
    const userRes = await fetch(
      "https://www.instagram.com/api/v1/accounts/current_user/?edit=true",
      { headers }
    );
    console.log("[MsgPoller] Free Mode: current_user response:", userRes.status, userRes.statusText);

    if (userRes.status === 401 || userRes.status === 403) {
      console.log("[MsgPoller] Free Mode: session expired (401/403)");
      await browser.storage.local.set({ igFetchError: "session_expired" });
      return;
    }
    if (!userRes.ok) {
      const errBody = await userRes.text();
      console.log("[MsgPoller] Free Mode: error response body:", errBody.substring(0, 500));
      throw new Error("API error: " + userRes.status);
    }

    const userData = await userRes.json();
    const myId = String(userData?.user?.pk || "");
    console.log("[MsgPoller] Free Mode: logged in as uid:", myId);

    if (!myId) {
      // Fallback: extract user ID from sessionid (format: "UID:hash:count")
      const parts = currentSessionId.split(/[:]/);
      if (parts[0] && /^\d+$/.test(parts[0])) {
        // Use parsed ID
      } else {
        throw new Error("Could not determine user ID");
      }
    }

    // Step 2: Fetch inbox
    const inboxRes = await fetch(
      "https://www.instagram.com/api/v1/direct_v2/inbox/?visual_message_return_type=unseen&persistentBadging=true&limit=20",
      { headers }
    );

    if (inboxRes.status === 401 || inboxRes.status === 403) {
      await browser.storage.local.set({ igFetchError: "session_expired" });
      return;
    }
    if (!inboxRes.ok) return; // rate limit or transient error

    const inboxData = await inboxRes.json();
    const threads = inboxData?.inbox?.threads || [];

    // Step 3: Process threads into messages
    const store = await browser.storage.local.get("freemiumMessages");
    let savedMessages = store.freemiumMessages || [];
    const seenIds = new Set(savedMessages.map(m => m.msg_id));

    let countNew = 0;
    const now = new Date().toISOString().split('.')[0];

    for (const thread of [...threads].reverse()) {
      const threadId = thread.thread_id;
      const isGroup = thread.is_group;
      const groupTitle = thread.thread_title || "";
      const users = thread.users || [];
      const userMap = {};
      users.forEach(u => userMap[String(u.pk)] = u.username);

      const otherUsers = users
        .filter(u => String(u.pk) !== myId)
        .map(u => u.username);
      const defaultPartner = otherUsers.length > 0 ? otherUsers[0] : "unknown";

      const items = thread.items || [];
      const reversedItems = [...items].reverse();

      for (const item of reversedItems) {
        const text = extractMessageText(item);
        const itemUserId = String(item.user_id);
        const isMine = itemUserId === myId;
        const msgId = String(item.item_id);

        if (!text || !msgId || seenIds.has(msgId)) continue;

        seenIds.add(msgId);

        let partnerName = defaultPartner;
        if (isGroup) {
          const title = groupTitle || "Group";
          if (isMine) partnerName = title;
          else partnerName = `${userMap[itemUserId] || "unknown"} (in ${title})`;
        }

        let msgTime = now;
        if (item.timestamp) {
          const date = new Date(parseInt(item.timestamp) / 1000);
          const pad = n => n.toString().padStart(2, '0');
          msgTime = `${date.getFullYear()}-${pad(date.getMonth()+1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
        }

        savedMessages.unshift({
          saved_at: msgTime,
          app: "Instagram",
          direction: isMine ? "sent" : "received",
          sender: partnerName,
          message: text,
          thread_id: threadId,
          msg_id: msgId
        });
        countNew++;
      }
    }

    if (countNew > 0) {
      if (savedMessages.length > 300) savedMessages = savedMessages.slice(0, 300);
      await browser.storage.local.set({ freemiumMessages: savedMessages, igFetchError: null });
    } else {
      await browser.storage.local.set({ igFetchError: null });
    }

    processMessagesForBadge(savedMessages);

  } catch (err) {
    console.error("IG fetch failed:", err);
    await browser.storage.local.set({ igFetchError: err.message });
  }
}

// ── Badge management ─────────────────────────────────────────────────────────
function processMessagesForBadge(messages) {
  if (!messages || messages.length === 0) return;

  let unreadCount = 0;
  let newLatestMsgId = null;

  for (const msg of messages) {
    if (!newLatestMsgId) newLatestMsgId = msg.msg_id;
    if (msg.msg_id === lastSeenMsgId) break;
    if (msg.direction === "received") unreadCount++;
  }

  if (unreadCount > 0) {
    browser.action.setBadgeText({ text: unreadCount > 9 ? "9+" : unreadCount.toString() });
    browser.action.setBadgeBackgroundColor({ color: "#ef4444" });
  }
}

// ── Message listener (from popup) ────────────────────────────────────────────
browser.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "clearBadge") {
    browser.action.setBadgeText({ text: "" });
    if (request.latestMsgId) {
      lastSeenMsgId = request.latestMsgId;
      browser.storage.local.set({ lastSeenMsgId: request.latestMsgId });
    }
  } else if (request.action === "forceFetch") {
    checkForNewMessages().then(() => sendResponse({ status: "ok" }));
    return true;
  }
});
