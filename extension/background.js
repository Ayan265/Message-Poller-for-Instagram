const POLL_INTERVAL_MINUTES = 0.3; // 18 seconds
const NATIVE_APP = "com.linuxayan.ig_poller";

// Store the latest message ID we have seen
let lastSeenMsgId = null;

// Initialize
browser.storage.local.get("lastSeenMsgId").then(res => {
  if (res.lastSeenMsgId) {
    lastSeenMsgId = res.lastSeenMsgId;
  }
  
  // Set up alarm to poll every 30s
  browser.alarms.create("pollMessages", { periodInMinutes: POLL_INTERVAL_MINUTES });
  // Also check immediately on startup
  checkForNewMessages();
});

// Run when alarm fires
browser.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "pollMessages") {
    checkForNewMessages();
  }
});

async function checkForNewMessages() {
  const settings = await browser.storage.local.get({ isPollerEnabled: true });
  if (!settings.isPollerEnabled) return;

  try {
    // 1. Try Premium Mode (Native Host)
    const data = await browser.runtime.sendNativeMessage(NATIVE_APP, { action: "get_data" });
    if (data && data.messages) {
      await browser.storage.local.set({ isPremiumMode: true });
      processMessagesForBadge(data.messages);
      return; // Success, we're done.
    }
  } catch (err) {
    // Native host not found or error. Fall through to Freemium Mode.
    // console.log("Native host not found. Falling back to JS Poller (Freemium).");
  }

  // 2. Freemium Mode (JS Fetch)
  await browser.storage.local.set({ isPremiumMode: false });
  await pollInstagramDirectly();
}

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

async function pollInstagramDirectly() {
  try {
    // Get current user ID to know direction
    const userRes = await fetch("https://www.instagram.com/api/v1/accounts/current_user/?edit=true", {
      credentials: "include",
      headers: { "X-IG-App-ID": "936619743392459", "X-Requested-With": "XMLHttpRequest" }
    });
    if (!userRes.ok) throw new Error("Not logged in");
    const userData = await userRes.json();
    const myId = String(userData?.user?.pk || "");

    const inboxRes = await fetch("https://www.instagram.com/api/v1/direct_v2/inbox/?visual_message_return_type=unseen&persistentBadging=true&limit=20", {
      credentials: "include",
      headers: { "X-IG-App-ID": "936619743392459", "X-Requested-With": "XMLHttpRequest" }
    });
    
    if (!inboxRes.ok) return; // rate limit or auth error
    const inboxData = await inboxRes.json();
    const threads = inboxData?.inbox?.threads || [];

    // Also get existing saved messages from storage to deduplicate
    const store = await browser.storage.local.get("freemiumMessages");
    let savedMessages = store.freemiumMessages || [];
    const seenIds = new Set(savedMessages.map(m => m.msg_id));

    let countNew = 0;
    const now = new Date().toISOString().split('.')[0]; // YYYY-MM-DDTHH:MM:SS

    // Process threads from oldest to newest so newest end up at the top
    for (const thread of [...threads].reverse()) {
      const threadId = thread.thread_id;
      const isGroup = thread.is_group;
      const groupTitle = thread.thread_title || "";
      const users = thread.users || [];
      const userMap = {};
      users.forEach(u => userMap[String(u.pk)] = u.username);
      
      const otherUsers = users.filter(u => String(u.pk) !== myId).map(u => u.username);
      const defaultPartner = otherUsers.length > 0 ? otherUsers[0] : "unknown";

      const items = thread.items || [];
      // Instagram returns items newest first. Reverse to append chronologically.
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

        const entry = {
          saved_at: msgTime,
          app: "Instagram",
          direction: isMine ? "sent" : "received",
          sender: partnerName,
          message: text,
          thread_id: threadId,
          msg_id: msgId
        };
        
        savedMessages.unshift(entry);
        countNew++;
      }
    }

    if (countNew > 0) {
      // Cap at 300 to prevent quota limits
      if (savedMessages.length > 300) savedMessages = savedMessages.slice(0, 300);
      await browser.storage.local.set({ freemiumMessages: savedMessages, igFetchError: null });
    } else {
      await browser.storage.local.set({ igFetchError: null });
    }

    processMessagesForBadge(savedMessages);

  } catch (err) {
    console.error("IG fetch failed:", err);
    browser.storage.local.set({ igFetchError: err.message === "Not logged in" ? "not_logged_in" : err.message });
  }
}

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
    browser.action.setBadgeBackgroundColor({ color: "#ef4444" }); // Red badge
  }
}

// Listen for messages from the popup
browser.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "clearBadge") {
    browser.action.setBadgeText({ text: "" });
    if (request.latestMsgId) {
      lastSeenMsgId = request.latestMsgId;
      browser.storage.local.set({ lastSeenMsgId: request.latestMsgId });
    }
  } else if (request.action === "forceFetch") {
    checkForNewMessages().then(() => sendResponse({status: "ok"}));
    return true;
  }
});
