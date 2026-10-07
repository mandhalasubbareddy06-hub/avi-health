document.addEventListener("DOMContentLoaded", () => {
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const revealElements = document.querySelectorAll(".feature-card, .steps article, .workspace-feature, .privacy-copy, .workflow-copy, .section-heading");
  if (reducedMotion || !("IntersectionObserver" in window)) {
    revealElements.forEach(element => element.classList.add("is-visible"));
  } else {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -30px" });
    revealElements.forEach(element => {
      element.classList.add("reveal");
      observer.observe(element);
    });
  }

  const sidebar = document.getElementById("sidebar");
  const menu = document.getElementById("menuBtn");
  const sidebarLinks = sidebar?.querySelectorAll("a") || [];
  const closeSidebar = () => {
    sidebar?.classList.remove("open");
    menu?.setAttribute("aria-expanded", "false");
  };

  menu?.addEventListener("click", () => {
    const isOpen = sidebar.classList.toggle("open");
    menu.setAttribute("aria-expanded", String(isOpen));
  });
  sidebarLinks.forEach(link => link.addEventListener("click", closeSidebar));
  document.addEventListener("click", event => {
    if (sidebar?.classList.contains("open") && !sidebar.contains(event.target) && !menu?.contains(event.target)) {
      closeSidebar();
    }
  });

  const modal = document.getElementById("recordModal");
  const recordForm = document.getElementById("recordForm");
  let lastFocusedElement = null;

  const focusableSelector = "button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [href]";
  const getFocusable = () => [...modal.querySelectorAll(focusableSelector)].filter(element => !element.hasAttribute("hidden"));

  function openModal(record = null) {
    if (!modal || !recordForm) return;
    lastFocusedElement = document.activeElement;
    document.getElementById("recordModalTitle").textContent = record ? "Edit health record" : "Add health record";
    document.getElementById("recordId").value = record?.id || "";
    document.getElementById("recordTitle").value = record?.title || "";
    document.getElementById("recordCategory").value = record?.category || "Tracking";
    document.getElementById("recordDetails").value = record?.details || "";
    modal.classList.add("open");
    document.body.style.overflow = "hidden";
    window.setTimeout(() => document.getElementById("recordTitle")?.focus(), 40);
  }

  function closeModal() {
    if (!modal) return;
    modal.classList.remove("open");
    document.body.style.overflow = "";
    recordForm?.reset();
    lastFocusedElement?.focus();
  }

  modal?.addEventListener("click", event => {
    if (event.target === modal) closeModal();
  });
  modal?.addEventListener("keydown", event => {
    if (event.key !== "Tab") return;
    const focusable = getFocusable();
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  });

  window.openRecordModal = openModal;
  window.closeRecordModal = closeModal;
});
