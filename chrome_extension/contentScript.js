// Backend endpoint
const LOG_ENDPOINT = "http://127.0.0.1:8000/meet-bot/log";

// Generate UUID in-memory only (no storage)
function generateUUID() {
  return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
      (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
  );
}

const sessionId = generateUUID();

// Safe logger — NO storage called here
async function sendLog(eventType, payload = {}) {
  console.log("[MeetBot] Sending log:", eventType);

  try {
    const res = await fetch(LOG_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        interview_id: sessionId,
        event_type: eventType,
        payload
      })
    });

    console.log("[MeetBot] Logged:", eventType);
  } catch (err) {
    console.error("[MeetBot] Failed to log to backend:", err);
  }
}

// ---------------- Main Logic ----------------

window.addEventListener("load", () => {
  sendLog("meet_loaded");

  // Detect Join button
  const joinInterval = setInterval(() => {
    const button =
      document.querySelector("button[aria-label*='Join']") ||
      document.querySelector("button[jsname='LgbsSe']");

    if (button) {
      button.addEventListener("click", () => {
        sendLog("meeting_started");
      });
      clearInterval(joinInterval);
    }
  }, 800);

  // Poll participants (safe)
  setInterval(() => {
    const nodes = document.querySelectorAll("div[role='listitem'] .zWGUib");
    if (!nodes) return;

    const participants = [...nodes].map(n => n.innerText.trim());
    sendLog("participants_update", { participants });

  }, 4000);
});

window.addEventListener("beforeunload", () => {
  sendLog("meeting_ended");
});
