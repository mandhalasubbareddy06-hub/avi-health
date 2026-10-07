document.addEventListener("DOMContentLoaded", () => {
  const menu = document.getElementById("menuBtn");
  const sidebar = document.getElementById("sidebar");
  if (menu && sidebar) menu.addEventListener("click", () => sidebar.classList.toggle("open"));

  const send = document.getElementById("sendBtn");
  const input = document.getElementById("question");
  const messages = document.getElementById("messages");
  const recordList = document.getElementById("recordList");
  const modal = document.getElementById("recordModal");
  const form = document.getElementById("recordForm");
  const toast = document.getElementById("productToast");
  let records = [];
  let toastTimer;

  function showToast(message) {
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove("show"), 2600);
  }

  function updateSummary() {
    const count = records.length;
    const countElement = document.getElementById("recordCount");
    const summaryElement = document.getElementById("summaryRecordCount");
    const categoryElement = document.getElementById("categoryCount");
    if (countElement) countElement.textContent = count;
    if (summaryElement) summaryElement.textContent = count;
    if (categoryElement) categoryElement.textContent = new Set(records.map(record => record.category)).size;
  }

  function recordIcon(category) {
    const icons = { Medication: "✚", Appointment: "□", "Lab result": "▤", Tracking: "◒", Other: "▣" };
    return icons[category] || "▣";
  }

  function renderRecords() {
    if (!recordList) return;
    if (!records.length) {
      recordList.innerHTML = '<div class="empty-state"><strong>No health records yet</strong>Add your first record to begin organizing your health information.</div>';
      return;
    }
    recordList.innerHTML = records.map(record => `
      <article class="product-record" data-record-id="${record.id}">
        <div class="product-record-icon">${escapeHtml(recordIcon(record.category))}</div>
        <div>
          <h4>${escapeHtml(record.title)}</h4>
          <p>${escapeHtml(record.details)}</p>
        </div>
        <div class="product-record-meta">
          <span class="product-record-category">${escapeHtml(record.category)}</span>
          <button class="record-action edit-record" type="button" aria-label="Edit ${escapeHtml(record.title)}">✎</button>
          <button class="record-action delete-record" type="button" aria-label="Delete ${escapeHtml(record.title)}">×</button>
        </div>
      </article>
    `).join("");
  }

  async function loadRecords() {
    try {
      const response = await fetch("/records/api");
      if (!response.ok) throw new Error("Unable to load records");
      const data = await response.json();
      records = data.records;
      updateSummary();
      renderRecords();
    } catch {
      showToast("Your records could not be loaded.");
    }
  }

  function openModal(record = null) {
    if (!modal || !form) return;
    document.getElementById("recordModalTitle").textContent = record ? "Edit health record" : "Add health record";
    document.getElementById("recordId").value = record?.id || "";
    document.getElementById("recordTitle").value = record?.title || "";
    document.getElementById("recordCategory").value = record?.category || "Tracking";
    document.getElementById("recordDetails").value = record?.details || "";
    modal.classList.add("open");
    document.body.style.overflow = "hidden";
    document.getElementById("recordTitle").focus();
  }

  function closeModal() {
    if (!modal) return;
    modal.classList.remove("open");
    document.body.style.overflow = "";
    form.reset();
  }

  async function saveRecord(event) {
    event.preventDefault();
    const recordId = document.getElementById("recordId").value;
    const payload = new URLSearchParams({
      title: document.getElementById("recordTitle").value.trim(),
      category: document.getElementById("recordCategory").value,
      details: document.getElementById("recordDetails").value.trim()
    });
    const response = await fetch(recordId ? `/records/${recordId}` : "/records", {
      method: recordId ? "PATCH" : "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: payload
    });
    const data = await response.json();
    if (!response.ok) {
      showToast(data.error || "The record could not be saved.");
      return;
    }
    closeModal();
    await loadRecords();
    showToast(recordId ? "Record updated." : "Record added.");
  }

  async function deleteRecord(recordId) {
    const response = await fetch(`/records/${recordId}`, { method: "DELETE" });
    if (!response.ok) {
      showToast("The record could not be deleted.");
      return;
    }
    records = records.filter(record => record.id !== Number(recordId));
    updateSummary();
    renderRecords();
    showToast("Record deleted.");
  }

  async function ask() {
    const question = input?.value.trim();
    if (!question) return;
    messages.innerHTML += `<div class="message">${escapeHtml(question)}</div>`;
    input.value = "";
    try {
      const res = await fetch("/api/copilot", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({question})
      });
      const data = await res.json();
      messages.innerHTML += `<div class="message">${escapeHtml(data.answer || "No response.")}</div>`;
      messages.scrollTop = messages.scrollHeight;
    } catch {
      messages.innerHTML += `<div class="message">The Copilot service is not connected yet.</div>`;
    }
  }

  document.getElementById("addRecordBtn")?.addEventListener("click", () => openModal());
  document.getElementById("closeModalBtn")?.addEventListener("click", closeModal);
  document.getElementById("cancelModalBtn")?.addEventListener("click", closeModal);
  modal?.addEventListener("click", event => { if (event.target === modal) closeModal(); });
  form?.addEventListener("submit", saveRecord);
  recordList?.addEventListener("click", event => {
    const item = event.target.closest(".product-record");
    if (!item) return;
    if (event.target.closest(".edit-record")) openModal(records.find(record => record.id === Number(item.dataset.recordId)));
    if (event.target.closest(".delete-record")) deleteRecord(item.dataset.recordId);
  });
  if (send) send.addEventListener("click", ask);
  if (input) input.addEventListener("keydown", e => { if (e.key === "Enter") ask(); });
  document.addEventListener("keydown", event => { if (event.key === "Escape") closeModal(); });
  loadRecords();
});

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, c => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
  }[c]));
}
