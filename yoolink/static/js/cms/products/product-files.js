const filesConfig = document.getElementById("productFormConfig");
const anyFilesUrl = filesConfig?.dataset.anyfilesUrl;

const selectedProductFiles = new Map();

function getSelectedProductFileIds() {
  return Array.from(selectedProductFiles.keys());
}

window.getSelectedProductFileIds = getSelectedProductFileIds;

$(document).ready(function () {
  const $anyFileModal = $("#anyFileModal");
  const $modalContainer = $anyFileModal.find(".modal-container");
  const $possibleAnyFiles = $("#possibleAnyFiles");
  const $selectedProductFiles = $("#selectedProductFiles");
  const $searchInput = $("#anyFileSearch");

  initSelectedFilesFromDom();
  renderSelectedFiles();

  $(".edit-files").on("click", function () {
    $anyFileModal.removeClass("hidden").addClass("flex");
    loadAnyFiles();
  });

  $("#closeAnyFileModal").on("click", function () {
    $anyFileModal.addClass("hidden").removeClass("flex");
  });

  $("#confirmAnyFiles").on("click", function () {
    $anyFileModal.addClass("hidden").removeClass("flex");
    renderSelectedFiles();
  });

  $("#reloadAnyFiles").on("click", function () {
    loadAnyFiles(true);
  });

  $(document).mouseup(function (e) {
    if (
      !$modalContainer.is(e.target) &&
      $modalContainer.has(e.target).length === 0
    ) {
      $anyFileModal.addClass("hidden").removeClass("flex");
    }
  });

  $searchInput.on("input", function () {
    filterAnyFiles($(this).val().trim().toLowerCase());
  });

  $selectedProductFiles.on("click", ".remove-product-file", function () {
    const fileId = String($(this).closest(".selected-product-file").data("file-id"));
    selectedProductFiles.delete(fileId);
    renderSelectedFiles();
  });

  function initSelectedFilesFromDom() {
    $(".selected-product-file").each(function () {
      const $item = $(this);
      const fileId = String($item.data("file-id"));

      selectedProductFiles.set(fileId, {
        id: fileId,
        url: $item.data("file-url") || "",
        title: $item.data("file-title") || "Datei",
        ext: $item.data("file-ext") || "",
      });
    });
  }

  function loadAnyFiles(showMessage = false) {
    if (!anyFilesUrl) {
      sendNotif("Die Datei URL fehlt. Bitte lade die Seite neu.", "error");
      return;
    }

    $.ajax({
      url: anyFilesUrl,
      type: "GET",
      dataType: "json",
      success: function (response) {
        const files = response.files || [];
        renderAnyFiles(files);

        if (showMessage) {
          sendNotif("Dateien wurden geladen.", "success");
        }
      },
      error: function (xhr) {
        console.error(xhr);
        sendNotif("Dateien konnten nicht geladen werden.", "error");
      }
    });
  }

  function renderAnyFiles(files) {
    $possibleAnyFiles.empty();

    if (!files.length) {
      $possibleAnyFiles.append(
        '<div class="col-span-full rounded-xl border border-dashed border-gray-300 p-4 text-sm text-gray-500">Keine Dateien gefunden</div>'
      );
      return;
    }

    files.forEach(function (file) {
      const fileId = String(file.id);
      const isSelected = selectedProductFiles.has(fileId);

      const card = $(`
        <div class="anyfile-option rounded-2xl border p-4 shadow-sm transition hover:shadow-md ${isSelected ? "border-blue-500 bg-blue-50" : "border-gray-200 bg-white"}" data-file-id="${fileId}">
          <div class="mb-3 flex items-start justify-between gap-3">
            <div class="min-w-0">
              <p class="truncate font-semibold text-gray-900">${escapeHtml(file.title || "Datei")}</p>
              <p class="truncate text-sm text-gray-500">${escapeHtml(file.ext || "")}</p>
            </div>
            <button type="button" class="toggle-anyfile rounded-lg px-3 py-1 text-sm font-semibold ${isSelected ? "bg-red-100 text-red-700" : "bg-blue-100 text-blue-700"}">
              ${isSelected ? "Entfernen" : "Hinzufügen"}
            </button>
          </div>
          <a href="${file.url}" target="_blank" class="text-sm font-medium text-blue-600 hover:underline">Datei öffnen</a>
        </div>
      `);

      card.find(".toggle-anyfile").on("click", function () {
        toggleFile(file);
      });

      $possibleAnyFiles.append(card);
    });
  }

  function toggleFile(file) {
    const fileId = String(file.id);

    if (selectedProductFiles.has(fileId)) {
      selectedProductFiles.delete(fileId);
    } else {
      selectedProductFiles.set(fileId, {
        id: fileId,
        url: file.url || "",
        title: file.title || "Datei",
        ext: file.ext || "",
      });
    }

    renderSelectedFiles();
    loadAnyFiles();
  }

  function renderSelectedFiles() {
    $selectedProductFiles.empty();

    if (!selectedProductFiles.size) {
      $selectedProductFiles.append(
        '<div class="rounded-xl border border-dashed border-gray-300 p-4 text-sm text-gray-500">Noch keine Dateien zugeordnet</div>'
      );
      return;
    }

    selectedProductFiles.forEach(function (file) {
      const item = $(`
        <div
          class="selected-product-file flex items-center justify-between rounded-xl border border-gray-200 bg-gray-50 px-4 py-3"
          data-file-id="${file.id}"
          data-file-url="${file.url}"
          data-file-title="${escapeHtml(file.title)}"
          data-file-ext="${escapeHtml(file.ext)}"
        >
          <div class="min-w-0">
            <p class="truncate font-medium text-gray-900">${escapeHtml(file.title)}</p>
            <p class="text-sm text-gray-500">${escapeHtml(file.ext)}</p>
          </div>
          <button
            type="button"
            class="remove-product-file rounded-lg px-3 py-1 text-sm font-semibold text-red-600 hover:bg-red-50"
          >
            Entfernen
          </button>
        </div>
      `);

      $selectedProductFiles.append(item);
    });
  }

  function filterAnyFiles(query) {
    $("#possibleAnyFiles .anyfile-option").each(function () {
      const text = $(this).text().toLowerCase();
      $(this).toggle(text.includes(query));
    });
  }

  function escapeHtml(value) {
    return $("<div>").text(value || "").html();
  }
});