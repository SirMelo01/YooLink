// static/js/cms-translation.js

$(document).ready(function () {
  function setupLanguageDropdown(buttonId, menuId, flagId, textId) {
    // Dropdown anzeigen/verstecken
    $(`#${buttonId}`).on("click", function () {
      $(`#${menuId}`).toggleClass("hidden");
    });

    // Sprache ändern (ALTE LOGIK mit AJAX auf /cms/set-language/<lang>/)
    $(`#${menuId} .language-option`).on("click", function () {
      var selectedLang = $(this).attr("data-lang");
      var selectedFlag = $(this).attr("data-flag");
      var selectedText = $(this).attr("data-text");

      $.ajax({
        url: `/cms/set-language/${selectedLang}/`,
        type: "GET",
        success: function (response) {
          if (response.message) {
            // Flagge und Text im Button aktualisieren
            $(`#${flagId}`).attr("class", `fi fi-${selectedFlag} mr-2`);
            $(`#${textId}`).text(selectedText);

            // Seite neu laden, damit Django die Sprache übernimmt
            location.reload();
          }
        },
        error: function (xhr, status, error) {
          console.error("Fehler beim Ändern der Sprache:", error);
        }
      });
    });

    // Dropdown schließen, wenn außerhalb geklickt wird
    $(document).on("click", function (event) {
      if (!$(event.target).closest(`#${buttonId}, #${menuId}`).length) {
        $(`#${menuId}`).addClass("hidden");
      }
    });
  }

  // CMS hat aktuell nur Desktop-Dropdown – Mobile schadet aber nicht, falls später ergänzt
  setupLanguageDropdown(
    "languageDropdownButtonDesktop",
    "languageDropdownMenuDesktop",
    "selectedLangFlagDesktop",
    "selectedLangTextDesktop"
  );

  // Falls du irgendwann auch im CMS ein mobiles Dropdown nutzt:
  setupLanguageDropdown(
    "languageDropdownButtonMobile",
    "languageDropdownMenuMobile",
    "selectedLangFlagMobile",
    "selectedLangTextMobile"
  );
});
