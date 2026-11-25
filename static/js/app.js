(function () {
  const app = document.querySelector(".app");
  const aiPanel = document.getElementById("ai-panel");
  const modal = document.getElementById("event-modal");
  const form = document.getElementById("event-form");
  const deleteBtn = document.getElementById("event-delete");
  const deleteForm = document.getElementById("event-delete-form");

  function pad(n) {
    return String(n).padStart(2, "0");
  }

  function toLocalInput(date) {
    return (
      date.getFullYear() +
      "-" +
      pad(date.getMonth() + 1) +
      "-" +
      pad(date.getDate()) +
      "T" +
      pad(date.getHours()) +
      ":" +
      pad(date.getMinutes())
    );
  }

  function openAi() {
    app.classList.add("ai-open");
    localStorage.setItem("calai_ai_open", "1");
  }

  function closeAi() {
    app.classList.remove("ai-open");
    localStorage.setItem("calai_ai_open", "0");
  }

  if (localStorage.getItem("calai_ai_open") === "1") {
    openAi();
  }

  document.getElementById("toggle-ai")?.addEventListener("click", function () {
    if (app.classList.contains("ai-open")) closeAi();
    else openAi();
  });
  document.getElementById("close-ai")?.addEventListener("click", closeAi);

  function resetForm() {
    form.action = "/events";
    document.getElementById("event-modal-title").textContent = "Create event";
    form.reset();
    document.getElementById("event-id").value = "";
    deleteBtn.hidden = true;
  }

  function openCreate(start, end) {
    resetForm();
    if (start) document.getElementById("event-start").value = toLocalInput(start);
    if (end) document.getElementById("event-end").value = toLocalInput(end);
    modal.hidden = false;
  }

  async function openEdit(eventId) {
    resetForm();
    const res = await fetch("/api/events/" + eventId);
    if (!res.ok) return;
    const e = await res.json();
    document.getElementById("event-modal-title").textContent = "Edit event";
    form.action = "/events/" + e.id + "/update";
    document.getElementById("event-id").value = e.id;
    document.getElementById("event-title").value = e.title || "";
    document.getElementById("event-description").value = e.description || "";
    document.getElementById("event-start").value = e.start_time;
    document.getElementById("event-end").value = e.end_time;
    document.getElementById("event-attendees").value = e.attendees || "";
    document.getElementById("event-category").value = e.category || "meeting";
    document.getElementById("event-location").value = e.location || "";
    document.getElementById("event-priority").value = e.priority || "medium";
    document.getElementById("event-link").value = e.meeting_link || "";
    document.getElementById("event-notes").value = e.notes || "";
    deleteBtn.hidden = false;
    deleteForm.action = "/events/" + e.id + "/delete";
    modal.hidden = false;
  }

  function closeModal() {
    modal.hidden = true;
  }

  document.getElementById("open-create-event")?.addEventListener("click", function () {
    const start = new Date();
    start.setMinutes(0, 0, 0);
    start.setHours(start.getHours() + 1);
    const end = new Date(start.getTime() + 60 * 60 * 1000);
    openCreate(start, end);
  });

  document.querySelectorAll("[data-close-modal]").forEach(function (btn) {
    btn.addEventListener("click", closeModal);
  });

  modal?.addEventListener("click", function (ev) {
    if (ev.target === modal) closeModal();
  });

  deleteBtn?.addEventListener("click", function () {
    if (confirm("Delete this event?")) deleteForm.submit();
  });

  document.addEventListener("click", function (ev) {
    const eventBtn = ev.target.closest("[data-event-id]");
    if (eventBtn) {
      ev.preventDefault();
      ev.stopPropagation();
      openEdit(eventBtn.getAttribute("data-event-id"));
      return;
    }

    const slot = ev.target.closest("[data-create-slot], .timeline-row, .timeline-track");
    if (!slot) return;
    if (ev.target.closest("[data-event-id]")) return;

    const date = slot.getAttribute("data-date") || slot.closest("[data-date]")?.getAttribute("data-date");
    const hour = slot.getAttribute("data-hour") || slot.closest("[data-hour]")?.getAttribute("data-hour");
    if (!date) return;

    const start = new Date(date + "T00:00:00");
    start.setHours(hour ? parseInt(hour, 10) : 9, 0, 0, 0);
    const end = new Date(start.getTime() + 60 * 60 * 1000);
    openCreate(start, end);
  });

  // Scroll AI messages to bottom
  const msgs = document.getElementById("ai-messages");
  if (msgs) msgs.scrollTop = msgs.scrollHeight;

  function appendBubble(role, text) {
    if (!msgs) return;
    const empty = msgs.querySelector(".ai-empty");
    if (empty) empty.remove();
    const wrap = document.createElement("div");
    wrap.className = "ai-msg " + role;
    const bubble = document.createElement("div");
    bubble.className = "ai-bubble";
    bubble.innerHTML = String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\n/g, "<br>");
    wrap.appendChild(bubble);
    msgs.appendChild(wrap);
    msgs.scrollTop = msgs.scrollHeight;
    return wrap;
  }

  const aiForm = document.getElementById("ai-form");
  aiForm?.addEventListener("submit", async function (ev) {
    // Use fetch so real LLM latency shows a thinking state without full page reload.
    ev.preventDefault();
    const input = document.getElementById("ai-input");
    const sendBtn = document.getElementById("ai-send");
    const message = (input?.value || "").trim();
    if (!message) return;

    appendBubble("user", message);
    input.value = "";
    const thinking = appendBubble("assistant thinking", "Thinking… reading your calendar…");
    if (sendBtn) sendBtn.disabled = true;

    try {
      const body = new FormData();
      body.append("message", message);
      body.append("redirect_to", window.location.pathname);
      const res = await fetch("/ai/chat", {
        method: "POST",
        headers: {
          Accept: "application/json",
          "x-requested-with": "fetch",
        },
        body,
      });
      const data = await res.json();
      thinking.remove();
      appendBubble(
        "assistant",
        (data.reply || "Done.") + (data.mode ? "\n\n_(" + data.mode + " AI)_" : "")
      );

      if (data.proposal_id) {
        let pending = document.getElementById("ai-pending");
        if (!pending) {
          pending = document.createElement("div");
          pending.className = "ai-pending";
          pending.id = "ai-pending";
          aiForm.parentElement.insertBefore(pending, aiForm);
        }
        const item = document.createElement("div");
        item.className = "ai-pending-item";
        item.innerHTML =
          "<strong>" +
          (data.summary || "AI proposal") +
          '</strong><div class="btn-row">' +
          '<form method="post" action="/ai/proposals/' +
          data.proposal_id +
          '/confirm"><input type="hidden" name="redirect_to" value="' +
          window.location.pathname +
          '" /><button class="btn btn-primary" type="submit">Confirm</button></form>' +
          '<form method="post" action="/ai/proposals/' +
          data.proposal_id +
          '/dismiss"><input type="hidden" name="redirect_to" value="' +
          window.location.pathname +
          '" /><button class="btn" type="submit">Dismiss</button></form></div>';
        pending.prepend(item);
      }
    } catch (err) {
      thinking.remove();
      appendBubble("assistant", "Something went wrong talking to the AI. Please try again.");
    } finally {
      if (sendBtn) sendBtn.disabled = false;
    }
  });
})();
