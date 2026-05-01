(function () {
  "use strict";

  const CONSENT_COOKIE = "yoolink_cookie_consent";
  const CONSENT_VERSION = 1;
  const CONSENT_MAX_AGE = 60 * 60 * 24 * 180;
  const GA_ID = "G-ZYQPVZ3REE";
  const GOOGLE_FONT_URL =
    "https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&family=Raleway:ital,wght@0,100..900;1,100..900&display=swap";

  const defaultPreferences = {
    necessary: true,
    preferences: false,
    analytics: false,
    external: false,
  };

  window["ga-disable-" + GA_ID] = true;

  function getCookie(name) {
    const cookieArr = document.cookie ? document.cookie.split(";") : [];
    for (let i = 0; i < cookieArr.length; i += 1) {
      const cookiePair = cookieArr[i].split("=");
      if (name === cookiePair[0].trim()) {
        return decodeURIComponent(cookiePair.slice(1).join("="));
      }
    }
    return null;
  }

  function setCookie(name, value, maxAge) {
    const secure = window.location.protocol === "https:" ? "; Secure" : "";
    document.cookie = `${name}=${encodeURIComponent(value)}; max-age=${maxAge}; path=/; SameSite=Lax${secure}`;
  }

  function deleteCookie(name) {
    const secure = window.location.protocol === "https:" ? "; Secure" : "";
    const hostname = window.location.hostname;
    const parts = hostname.split(".").filter(Boolean);
    const domains = new Set([hostname, `.${hostname}`]);

    if (parts.length > 2) {
      domains.add(`.${parts.slice(-2).join(".")}`);
    }

    document.cookie = `${name}=; max-age=0; path=/; SameSite=Lax${secure}`;
    domains.forEach((domain) => {
      document.cookie = `${name}=; max-age=0; path=/; domain=${domain}; SameSite=Lax${secure}`;
    });
  }

  function parseConsentCookie() {
    const raw = getCookie(CONSENT_COOKIE);
    if (!raw) return null;

    try {
      const parsed = JSON.parse(raw);
      if (parsed.version !== CONSENT_VERSION || !parsed.categories) return null;
      return {
        version: CONSENT_VERSION,
        decidedAt: parsed.decidedAt || new Date().toISOString(),
        categories: Object.assign({}, defaultPreferences, parsed.categories, { necessary: true }),
      };
    } catch (error) {
      return null;
    }
  }

  function readLegacyConsent() {
    const legacyConsent = getCookie("Cookie-Consent");
    if (legacyConsent === null) return null;

    return {
      version: CONSENT_VERSION,
      decidedAt: new Date().toISOString(),
      categories: {
        necessary: true,
        preferences: getCookie("Cookie-Font") === "true",
        analytics: getCookie("Cookie-Analytic") === "true",
        external: getCookie("Cookie-Map") === "true",
      },
    };
  }

  function getConsent() {
    return parseConsentCookie() || readLegacyConsent();
  }

  function hasDecision() {
    return getConsent() !== null;
  }

  function categories() {
    const consent = getConsent();
    return consent ? consent.categories : defaultPreferences;
  }

  function syncLegacyGlobals() {
    const consent = getConsent();
    window.cookieselect = consent ? String(Object.values(consent.categories).some(Boolean)) : null;
    window.cookiefontselect = String(Boolean(consent && consent.categories.preferences));
    window.cookieanalyticselect = String(Boolean(consent && consent.categories.analytics));
    window.cookiemapselect = String(Boolean(consent && consent.categories.external));
  }

  function syncLegacyCookies(consent) {
    const anyOptional =
      consent.categories.preferences || consent.categories.analytics || consent.categories.external;
    setCookie("Cookie-Consent", String(anyOptional), CONSENT_MAX_AGE);
    setCookie("Cookie-Font", String(consent.categories.preferences), CONSENT_MAX_AGE);
    setCookie("Cookie-Analytic", String(consent.categories.analytics), CONSENT_MAX_AGE);
    setCookie("Cookie-Map", String(consent.categories.external), CONSENT_MAX_AGE);
  }

  function cleanupAnalyticsCookies() {
    ["_ga", "_gid", "_gat", `_ga_${GA_ID.replace("G-", "")}`].forEach(deleteCookie);
    window["ga-disable-" + GA_ID] = true;
  }

  function ensureGoogleFonts() {
    if (document.querySelector('link[data-cookie-service="google-fonts"]')) return;

    const preconnectFonts = document.createElement("link");
    preconnectFonts.rel = "preconnect";
    preconnectFonts.href = "https://fonts.googleapis.com";
    preconnectFonts.dataset.cookieService = "google-fonts";

    const preconnectStatic = document.createElement("link");
    preconnectStatic.rel = "preconnect";
    preconnectStatic.href = "https://fonts.gstatic.com";
    preconnectStatic.crossOrigin = "";
    preconnectStatic.dataset.cookieService = "google-fonts";

    const stylesheet = document.createElement("link");
    stylesheet.rel = "stylesheet";
    stylesheet.href = GOOGLE_FONT_URL;
    stylesheet.dataset.cookieService = "google-fonts";

    document.head.append(preconnectFonts, preconnectStatic, stylesheet);
    document.body.classList.add("font-poppins");
  }

  function unloadGoogleFonts() {
    document.querySelectorAll('[data-cookie-service="google-fonts"]').forEach((node) => node.remove());
    document.body.classList.remove("font-poppins");
  }

  function ensureAnalytics() {
    if (document.querySelector(`script[data-cookie-service="ga4"]`)) return;

    window["ga-disable-" + GA_ID] = false;
    window.dataLayer = window.dataLayer || [];
    window.gtag = function gtag() {
      window.dataLayer.push(arguments);
    };
    window.gtag("consent", "update", {
      analytics_storage: "granted",
      ad_storage: "denied",
      ad_user_data: "denied",
      ad_personalization: "denied",
    });
    window.gtag("js", new Date());
    window.gtag("config", GA_ID, { anonymize_ip: true });

    const script = document.createElement("script");
    script.async = true;
    script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_ID}`;
    script.dataset.cookieService = "ga4";
    document.head.appendChild(script);
  }

  function unloadAnalytics() {
    document.querySelectorAll('script[data-cookie-service="ga4"]').forEach((node) => node.remove());
    cleanupAnalyticsCookies();
  }

  function hydrateExternalEmbeds() {
    document.querySelectorAll("[data-cookie-src]").forEach((node) => {
      if (!node.getAttribute("src")) {
        node.setAttribute("src", node.dataset.cookieSrc);
      }
      node.classList.remove("hidden");
    });

    document.querySelectorAll("[data-cookie-placeholder]").forEach((node) => {
      node.classList.add("hidden");
    });

    renderRecaptcha();
  }

  function blockExternalEmbeds() {
    document.querySelectorAll("[data-cookie-src]").forEach((node) => {
      if (node.getAttribute("src")) {
        node.dataset.cookieSrc = node.getAttribute("src");
        node.removeAttribute("src");
      }
      node.classList.add("hidden");
    });

    document.querySelectorAll("[data-cookie-placeholder]").forEach((node) => {
      node.classList.remove("hidden");
    });

    unloadRecaptcha();
  }

  function renderRecaptcha() {
    const container = document.querySelector("[data-recaptcha-container]");
    if (!container || container.dataset.rendered === "true") return;

    const siteKey = container.dataset.sitekey;
    if (!siteKey) return;

    if (window.grecaptcha && typeof window.grecaptcha.render === "function") {
      window.grecaptcha.render(container, { sitekey: siteKey });
      container.dataset.rendered = "true";
      document.dispatchEvent(new CustomEvent("yoolink:recaptcha-ready"));
      return;
    }

    if (document.querySelector('script[data-cookie-service="recaptcha"]')) return;

    window.yoolinkOnRecaptchaLoad = function yoolinkOnRecaptchaLoad() {
      renderRecaptcha();
    };

    const script = document.createElement("script");
    script.src = "https://www.google.com/recaptcha/api.js?onload=yoolinkOnRecaptchaLoad&render=explicit";
    script.async = true;
    script.defer = true;
    script.dataset.cookieService = "recaptcha";
    document.head.appendChild(script);
  }

  function unloadRecaptcha() {
    document.querySelectorAll('script[data-cookie-service="recaptcha"]').forEach((node) => node.remove());
    document.querySelectorAll("[data-recaptcha-container]").forEach((container) => {
      container.innerHTML = "";
      delete container.dataset.rendered;
    });
    delete window.yoolinkOnRecaptchaLoad;
    window.grecaptcha = undefined;
    document.dispatchEvent(new CustomEvent("yoolink:recaptcha-reset"));
  }

  function applyConsent() {
    const selected = categories();

    if (selected.preferences) ensureGoogleFonts();
    else unloadGoogleFonts();

    if (selected.analytics) ensureAnalytics();
    else unloadAnalytics();

    if (selected.external) hydrateExternalEmbeds();
    else blockExternalEmbeds();

    syncLegacyGlobals();
  }

  function saveConsent(nextCategories) {
    const consent = {
      version: CONSENT_VERSION,
      decidedAt: new Date().toISOString(),
      categories: Object.assign({}, defaultPreferences, nextCategories, { necessary: true }),
    };

    setCookie(CONSENT_COOKIE, JSON.stringify(consent), CONSENT_MAX_AGE);
    syncLegacyCookies(consent);
    syncLegacyGlobals();
    applyConsent();
    document.dispatchEvent(new CustomEvent("yoolink:consentChanged", { detail: consent }));
    return consent;
  }

  function acceptAll() {
    return saveConsent({
      preferences: true,
      analytics: true,
      external: true,
    });
  }

  function rejectAll() {
    return saveConsent({
      preferences: false,
      analytics: false,
      external: false,
    });
  }

  function bindBanner() {
    const modal = document.getElementById("cookie-consent-modal");
    if (!modal) return;

    const details = modal.querySelector("[data-consent-details]");
    const summary = modal.querySelector("[data-consent-summary]");
    const toggles = modal.querySelectorAll("[data-consent-toggle]");
    let reloadTimer = null;

    function syncToggles() {
      const selected = categories();
      toggles.forEach((toggle) => {
        toggle.checked = Boolean(selected[toggle.dataset.consentToggle]);
      });
    }

    function showDetails() {
      details && details.classList.remove("hidden");
      summary && summary.classList.add("hidden");
      syncToggles();
    }

    function hideDetails() {
      details && details.classList.add("hidden");
      summary && summary.classList.remove("hidden");
    }

    function open(customMode) {
      modal.classList.remove("hidden");
      if (customMode) showDetails();
      else hideDetails();
    }

    function close() {
      if (!hasDecision()) rejectAll();
      modal.classList.add("hidden");
    }

    function showConsentFeedback(message) {
      let feedback = modal.querySelector("[data-consent-feedback]");
      if (!feedback) {
        feedback = document.createElement("div");
        feedback.dataset.consentFeedback = "";
        feedback.className = "mx-5 mb-4 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm font-semibold text-green-800";
        feedback.setAttribute("role", "status");
        const description = modal.querySelector("#cookie-consent-description");
        if (description && description.parentNode) {
          description.insertAdjacentElement("afterend", feedback);
        }
      }

      feedback.textContent = message;
      feedback.classList.remove("hidden");
    }

    function saveConsentAndReload(saveCallback, message) {
      saveCallback();
      showConsentFeedback(message);

      if (reloadTimer) window.clearTimeout(reloadTimer);
      reloadTimer = window.setTimeout(() => {
        window.location.reload();
      }, 1300);
    }

    window.YooLinkConsent.openSettings = function () {
      open(true);
    };

    document.addEventListener("click", (event) => {
      const actionTarget = event.target.closest("[data-consent-action]");
      if (!actionTarget) return;

      const action = actionTarget.dataset.consentAction;
      if (action === "accept-all") {
        saveConsentAndReload(
          acceptAll,
          "Ihre Cookie-Auswahl wurde gespeichert. Die Seite wird neu geladen, damit die Einstellungen aktiv werden."
        );
      } else if (action === "reject-all") {
        saveConsentAndReload(
          rejectAll,
          "Ihre Cookie-Auswahl wurde gespeichert. Die Seite wird neu geladen, damit die Einstellungen aktiv werden."
        );
      } else if (action === "customize") {
        showDetails();
      } else if (action === "save") {
        const custom = {};
        toggles.forEach((toggle) => {
          custom[toggle.dataset.consentToggle] = toggle.checked;
        });
        saveConsentAndReload(
          () => saveConsent(custom),
          "Ihre Cookie-Auswahl wurde gespeichert. Die Seite wird neu geladen, damit die Einstellungen aktiv werden."
        );
      } else if (action === "open-settings") {
        open(true);
      } else if (action === "close") {
        close();
      }
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") close();
    });

    if (!hasDecision()) open(false);
    else {
      modal.classList.add("hidden");
    }
  }

  window.getCookie = getCookie;
  syncLegacyGlobals();

  window.YooLinkConsent = {
    acceptAll,
    rejectAll,
    save: saveConsent,
    get: getConsent,
    categories,
    hasDecision,
    openSettings: function () {
      const button = document.querySelector('[data-consent-action="open-settings"]');
      if (button) button.click();
    },
    renderRecaptcha,
    apply: applyConsent,
  };

  document.addEventListener("DOMContentLoaded", () => {
    syncLegacyGlobals();
    applyConsent();
    bindBanner();
  });
})();
