(function () {
  "use strict";

  /* ---------------- Sidebar collapse (desktop) ---------------- */
  const shell = document.querySelector(".app-shell");
  const collapseBtn = document.querySelector("[data-sidebar-collapse]");
  if (collapseBtn && shell) {
    const stored = localStorage.getItem("yield-sidebar-collapsed") === "1";
    if (stored) shell.classList.add("sidebar-collapsed");

    collapseBtn.addEventListener("click", () => {
      shell.classList.toggle("sidebar-collapsed");
      localStorage.setItem(
        "yield-sidebar-collapsed",
        shell.classList.contains("sidebar-collapsed") ? "1" : "0"
      );
    });
  }

  /* ---------------- Mobile nav toggle ---------------- */
  const mobileBtn = document.querySelector("[data-mobile-menu]");
  const scrim = document.querySelector(".sidebar-scrim");
  function closeMobileNav() { shell && shell.classList.remove("mobile-nav-open"); }
  if (mobileBtn && shell) {
    mobileBtn.addEventListener("click", () => shell.classList.toggle("mobile-nav-open"));
  }
  if (scrim) scrim.addEventListener("click", closeMobileNav);

  /* ---------------- Dropdowns ---------------- */
  document.querySelectorAll("[data-dropdown-toggle]").forEach((btn) => {
    const dropdown = btn.closest(".dropdown");
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const wasOpen = dropdown.classList.contains("open");
      document.querySelectorAll(".dropdown.open").forEach((d) => d.classList.remove("open"));
      if (!wasOpen) dropdown.classList.add("open");
    });
  });
  document.addEventListener("click", () => {
    document.querySelectorAll(".dropdown.open").forEach((d) => d.classList.remove("open"));
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      document.querySelectorAll(".dropdown.open").forEach((d) => d.classList.remove("open"));
      document.querySelectorAll(".modal-overlay.open").forEach((m) => m.classList.remove("open"));
    }
  });

  /* ---------------- Modals ---------------- */
  document.querySelectorAll("[data-modal-open]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const modal = document.getElementById(btn.getAttribute("data-modal-open"));
      if (modal) modal.classList.add("open");
    });
  });
  document.querySelectorAll("[data-modal-close]").forEach((btn) => {
    btn.addEventListener("click", () => btn.closest(".modal-overlay").classList.remove("open"));
  });
  document.querySelectorAll(".modal-overlay").forEach((overlay) => {
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) overlay.classList.remove("open");
    });
  });

  /* ---------------- Toasts ---------------- */
  function iconFor(type) {
    const icons = {
      success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="M22 4L12 14.01l-3-3"/></svg>',
      danger: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6M9 9l6 6"/></svg>',
      warning: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><path d="M12 9v4M12 17h.01"/></svg>',
      info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>',
    };
    return icons[type] || icons.info;
  }

  function createToast(message, type) {
    type = type && ["success", "danger", "warning", "info"].includes(type) ? type : "info";
    const container = document.querySelector(".toast-container");
    if (!container) return;
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <span class="toast-icon">${iconFor(type)}</span>
      <div class="toast-body">${message}</div>
      <span class="toast-close" aria-label="Dismiss">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
      </span>`;
    container.appendChild(toast);
    const remove = () => {
      toast.classList.add("hide");
      setTimeout(() => toast.remove(), 220);
    };
    toast.querySelector(".toast-close").addEventListener("click", remove);
    setTimeout(remove, 5000);
  }
  window.showToast = createToast;

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-flash]").forEach((el) => {
      createToast(el.getAttribute("data-flash"), el.getAttribute("data-flash-type"));
    });
  });

  /* ---------------- Notification mark-as-read ---------------- */
  document.addEventListener("click", (e) => {
    const item = e.target.closest("[data-notification-id]");
    if (!item) return;
    const id = item.getAttribute("data-notification-id");
    const csrfToken = document.querySelector('meta[name="csrf-token"]');
    fetch(`/api/notifications/${id}/read`, {
      method: "POST",
      headers: csrfToken ? { "X-CSRFToken": csrfToken.content } : {},
    }).then(() => item.classList.remove("unread")).catch(() => {});
  });

  const markAllBtn = document.querySelector("[data-notifications-mark-all]");
  if (markAllBtn) {
    markAllBtn.addEventListener("click", () => {
      const csrfToken = document.querySelector('meta[name="csrf-token"]');
      fetch("/api/notifications/read-all", {
        method: "POST",
        headers: csrfToken ? { "X-CSRFToken": csrfToken.content } : {},
      }).then(() => {
        document.querySelectorAll(".notification-item.unread").forEach((n) => n.classList.remove("unread"));
        const badge = document.querySelector("[data-notification-badge]");
        if (badge) badge.remove();
      }).catch(() => {});
    });
  }

  /* ---------------- Active nav link highlighting ---------------- */
  document.querySelectorAll(".nav-link[data-path-prefix]").forEach((link) => {
    const prefix = link.getAttribute("data-path-prefix");
    if (window.location.pathname.startsWith(prefix)) link.classList.add("active");
  });
})();
