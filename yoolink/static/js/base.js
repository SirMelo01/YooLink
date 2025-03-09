const cookie = document.querySelector("#menu-cookie");
const menu = document.querySelector("#navbar-cta");

function toggleMenu() {
  if (menu.classList.contains("hidden")) {
    menu.classList.remove("hidden");
  } else {
    menu.classList.add("hidden");
  }
}

function cookieRefresh() {
  if (cookieselect == null) {
    cookie.classList.add("block");
    cookie.classList.remove("hidden");
  } else {
    cookie.classList.add("hidden");
  }
}

function acceptCookie() {
  document.cookie =
    "Cookie-Consent=true; expires=" + new Date(9999, 0, 1).toUTCString() + "; path=/";
  document.cookie =
    "Cookie-Analytic=true; expires=" + new Date(9999, 0, 1).toUTCString() + "; path=/";
  document.cookie =
    "Cookie-Font=true; expires=" + new Date(9999, 0, 1).toUTCString() + "; path=/";
  location.reload();
  cookieRefresh();
}

function refuseCookie() {
  document.cookie =
    "Cookie-Consent=false; expires=" + new Date(9999, 0, 1).toUTCString() + "; path=/";
  document.cookie =
    "Cookie-Analytic=false; expires=" + new Date(9999, 0, 1).toUTCString() + "; path=/";
  document.cookie =
    "Cookie-Font=false; expires=" + new Date(9999, 0, 1).toUTCString() + "; path=/";
  location.reload();
  cookieRefresh();
}

cookieRefresh();

$(document).ready(function () {
  function setupLanguageDropdown(buttonId, menuId, flagId, textId) {
      // Dropdown anzeigen/verstecken
      $(`#${buttonId}`).click(function () {
          $(`#${menuId}`).toggleClass("hidden");
      });

      // Sprache ändern
      $(`#${menuId} .language-option`).click(function () {
          var selectedLang = $(this).attr("data-lang");
          var selectedFlag = $(this).attr("data-flag");
          var selectedText = $(this).attr("data-text");

          // AJAX-Request zur Sprachänderung
          $.ajax({
              url: `/cms/set-language/${selectedLang}/`,
              type: "GET",
              success: function (response) {
                  if (response.message) {
                      // Flagge und Text im Button aktualisieren
                      $(`#${flagId}`).attr("class", `fi fi-${selectedFlag} mr-2`);
                      $(`#${textId}`).text(selectedText);

                      location.reload(); // Seite neu laden, um die neue Sprache zu aktivieren
                  }
              },
              error: function (xhr, status, error) {
                  console.error("Fehler beim Ändern der Sprache:", error);
              }
          });
      });

      // Dropdown schließen, wenn außerhalb geklickt wird
      $(document).click(function (event) {
          if (!$(event.target).closest(`#${buttonId}, #${menuId}`).length) {
              $(`#${menuId}`).addClass("hidden");
          }
      });
  }

  // Setup für Desktop
  setupLanguageDropdown("languageDropdownButtonDesktop", "languageDropdownMenuDesktop", "selectedLangFlagDesktop", "selectedLangTextDesktop");

  // Setup für Mobile
  setupLanguageDropdown("languageDropdownButtonMobile", "languageDropdownMenuMobile", "selectedLangFlagMobile", "selectedLangTextMobile");
});

