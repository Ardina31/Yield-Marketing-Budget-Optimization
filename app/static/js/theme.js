(function () {
  "use strict";

  function getStoredTheme() {
    return window.__INITIAL_THEME__ || localStorage.getItem("yield-theme") || "light";
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("yield-theme", theme);
    document.querySelectorAll("[data-theme-toggle]").forEach((el) => {
      el.checked = theme === "dark";
    });
  }

  // Apply immediately (this script is loaded synchronously in <head>)
  applyTheme(getStoredTheme());

  window.YieldTheme = {
    toggle: function () {
      const current = document.documentElement.getAttribute("data-theme") || "light";
      const next = current === "dark" ? "light" : "dark";
      applyTheme(next);

      // Persist to the user's account if they're signed in
      const csrfToken = document.querySelector('meta[name="csrf-token"]');
      if (window.__USER_AUTHENTICATED__) {
        fetch(`/settings/theme/${next}`, {
          method: "POST",
          headers: csrfToken ? { "X-CSRFToken": csrfToken.content } : {},
        }).catch(() => {});
      }
      return next;
    },
  };

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-theme-toggle]").forEach((toggle) => {
      toggle.addEventListener("change", () => window.YieldTheme.toggle());
    });
  });
})();
