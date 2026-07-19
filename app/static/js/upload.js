(function () {
  "use strict";

  const dropzone = document.querySelector("[data-dropzone]");
  if (!dropzone) return;

  const input = dropzone.querySelector('input[type="file"]');
  const fileNameEl = dropzone.querySelector("[data-file-name]");
  const promptEl = dropzone.querySelector("[data-dropzone-prompt]");

  function showFile(file) {
    if (!file) return;
    if (fileNameEl) {
      fileNameEl.textContent = `${file.name} · ${(file.size / 1024).toFixed(1)} KB`;
      fileNameEl.hidden = false;
    }
    if (promptEl) promptEl.hidden = true;
  }

  dropzone.addEventListener("click", () => input && input.click());

  ["dragenter", "dragover"].forEach((evt) => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.add("drag-over");
    });
  });
  ["dragleave", "drop"].forEach((evt) => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.remove("drag-over");
    });
  });

  dropzone.addEventListener("drop", (e) => {
    const files = e.dataTransfer.files;
    if (files && files.length && input) {
      input.files = files;
      showFile(files[0]);
    }
  });

  if (input) {
    input.addEventListener("change", () => {
      if (input.files && input.files.length) showFile(input.files[0]);
    });
  }

  const form = dropzone.closest("form");
  if (form) {
    form.addEventListener("submit", () => {
      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spin-dot"></span> Uploading…';
      }
    });
  }
})();
