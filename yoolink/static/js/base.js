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

/** Leistungen Dropdown – Desktop */
(function () {
  const wrapper = document.querySelector('[data-leistungen-dropdown]');
  if (!wrapper) return;
  const button = wrapper.querySelector('#leistungenDropdownButtonDesktop');
  const menu = wrapper.querySelector('#leistungenDropdownMenuDesktop');
  const chevron = wrapper.querySelector('[data-leistungen-chevron]');
  if (!button || !menu) return;

  function close() {
    menu.classList.add('hidden');
    button.setAttribute('aria-expanded', 'false');
    if (chevron) chevron.classList.remove('rotate-180');
  }
  function open() {
    menu.classList.remove('hidden');
    button.setAttribute('aria-expanded', 'true');
    if (chevron) chevron.classList.add('rotate-180');
  }
  function toggle() {
    if (menu.classList.contains('hidden')) open(); else close();
  }

  button.addEventListener('click', function (e) {
    e.stopPropagation();
    toggle();
  });
  document.addEventListener('click', function (e) {
    if (!wrapper.contains(e.target)) close();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') close();
  });
})();

/** Leistungen Dropdown – Mobile (Akkordeon) */
(function () {
  const wrapper = document.querySelector('[data-leistungen-dropdown-mobile]');
  if (!wrapper) return;
  const button = wrapper.querySelector('#leistungenDropdownButtonMobile');
  const menu = wrapper.querySelector('#leistungenDropdownMenuMobile');
  const chevron = wrapper.querySelector('[data-leistungen-chevron-mobile]');
  if (!button || !menu) return;

  button.addEventListener('click', function () {
    const isOpen = !menu.classList.contains('hidden');
    if (isOpen) {
      menu.classList.add('hidden');
      button.setAttribute('aria-expanded', 'false');
      if (chevron) chevron.classList.remove('rotate-180');
    } else {
      menu.classList.remove('hidden');
      button.setAttribute('aria-expanded', 'true');
      if (chevron) chevron.classList.add('rotate-180');
    }
  });
})();
