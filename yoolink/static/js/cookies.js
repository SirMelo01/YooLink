(function () {
  "use strict";

  function ready(callback) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", callback);
    } else {
      callback();
    }
  }

  ready(function () {
    const form = document.querySelector("[data-cookie-settings-form]");
    if (!form || !window.YooLinkConsent) return;

    const status = document.querySelector("[data-cookie-settings-status]");
    const toggles = form.querySelectorAll("[data-consent-toggle]");

    function sync() {
      const categories = window.YooLinkConsent.categories();
      toggles.forEach((toggle) => {
        toggle.checked = Boolean(categories[toggle.dataset.consentToggle]);
      });
    }

    function showStatus(message) {
      if (!status) return;
      status.textContent = message;
      status.classList.remove("hidden");
      window.setTimeout(() => status.classList.add("hidden"), 3500);
    }

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      const next = {};
      toggles.forEach((toggle) => {
        next[toggle.dataset.consentToggle] = toggle.checked;
      });
      window.YooLinkConsent.save(next);
      showStatus("Ihre Cookie-Auswahl wurde gespeichert.");
    });

    document.querySelectorAll("[data-cookie-settings-action]").forEach((button) => {
      button.addEventListener("click", function () {
        const action = button.dataset.cookieSettingsAction;
        if (action === "accept-all") {
          window.YooLinkConsent.acceptAll();
          sync();
          showStatus("Alle optionalen Dienste wurden akzeptiert.");
        } else if (action === "reject-all") {
          window.YooLinkConsent.rejectAll();
          sync();
          showStatus("Alle optionalen Dienste wurden abgelehnt.");
        }
      });
    });

    document.addEventListener("yoolink:consentChanged", sync);
    sync();
  });
})();
