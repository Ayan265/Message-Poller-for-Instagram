const POLL_INTERVAL_MINUTES = 0.5; // 30 seconds
const NATIVE_APP = "com.linuxayan.ig_poller";

// Store the latest message ID we have seen
let lastSeenMsgId = null;

// Initialize
browser.storage.local.get("lastSeenMsgId").then(res => {
  if (res.lastSeenMsgId) {
    lastSeenMsgId = res.lastSeenMsgId;
  }
  
  // Set up alarm to poll every 30s
  browser.alarms.create("pollNativeHost", { periodInMinutes: POLL_INTERVAL_MINUTES });
  // Also check immediately on startup
  checkForNewMessages();
});

// Run when alarm fires
browser.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "pollNativeHost") {
    checkForNewMessages();
  }
});

async function checkForNewMessages() {
  try {
    const data = await browser.runtime.sendNativeMessage(NATIVE_APP, { action: "get_data" });
    if (!data || !data.messages || data.messages.length === 0) return;

    let unreadCount = 0;
    let newLatestMsgId = null;

    // Messages are usually sorted newest first from the native host
    for (const msg of data.messages) {
      if (!newLatestMsgId) newLatestMsgId = msg.msg_id;
      
      // Stop counting if we reach the message we saw last time
      if (msg.msg_id === lastSeenMsgId) break;
      
      // Only count received messages
      if (msg.direction === "received") {
        unreadCount++;
      }
    }

    if (unreadCount > 0) {
      browser.action.setBadgeText({ text: unreadCount > 9 ? "9+" : unreadCount.toString() });
      browser.action.setBadgeBackgroundColor({ color: "#ef4444" }); // Red badge
    }
  } catch (err) {
    console.error("Background check failed:", err);
  }
}

// Listen for messages from the popup (e.g., when popup opens, it clears badge)
browser.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "clearBadge") {
    browser.action.setBadgeText({ text: "" });
    if (request.latestMsgId) {
      lastSeenMsgId = request.latestMsgId;
      browser.storage.local.set({ lastSeenMsgId: request.latestMsgId });
    }
  }
});
