document.getElementById("start-btn").addEventListener("click", () => {
  const meetUrl = document.getElementById("meet-url").value.trim();
  const interviewId = document.getElementById("interview-id").value.trim() || null;
  const backendBaseUrl =
    document.getElementById("backend-url").value.trim() || "http://localhost:8000";

  if (!meetUrl) {
    alert("Please enter a Google Meet URL");
    return;
  }

  chrome.runtime.sendMessage(
    {
      type: "START_MEET_BOT",
      meetUrl,
      interviewId,
      backendBaseUrl
    },
    (resp) => {
      if (!resp || !resp.ok) {
        alert("Failed to start bot: " + (resp && resp.error ? resp.error : "Unknown error"));
      } else {
        window.close();
      }
    }
  );
});


