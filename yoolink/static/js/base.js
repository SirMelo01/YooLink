const menu = document.querySelector("#navbar-cta");

function toggleMenu() {
  if (menu.classList.contains("hidden")) {
    menu.classList.remove("hidden");
  } else {
    menu.classList.add("hidden");
  }
}

function acceptCookie() {
  window.YooLinkConsent && window.YooLinkConsent.acceptAll();
}

function refuseCookie() {
  window.YooLinkConsent && window.YooLinkConsent.rejectAll();
}

/** Notifications Button */

(function () {
  const $btn = $('#notif-button');
  const $menu = $('#notif-menu');

  function closeMenu() {
    $menu.addClass('hidden');
    $btn.attr('aria-expanded', 'false');
  }
  function openMenu() {
    $menu.removeClass('hidden');
    $btn.attr('aria-expanded', 'true');
  }
  function toggleMenu() {
    if ($menu.hasClass('hidden')) openMenu(); else closeMenu();
  }

  // Toggle on click
  $btn.on('click', function (e) {
    e.stopPropagation();
    toggleMenu();
  });

  // Click outside schließt
  $(document).on('click', function (e) {
    // Alles schließen, wenn Klick nicht im Wrapper ist
    if ($(e.target).closest('#notif-wrapper').length === 0) {
      closeMenu();
    }
  });

  // Esc schließt
  $(document).on('keydown', function (e) {
    if (e.key === 'Escape') closeMenu();
  });

  // Optional: Schließen beim Tab-Focus raus
  $menu.on('keydown', function (e) {
    if (e.key === 'Tab') {
      // Wenn letzter Fokus rausfällt, schließen
      // (einfach: immer schließen)
      closeMenu();
    }
  });
})();
