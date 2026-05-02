var imageData = null;
var newImage = false;
let categories = [];

const formConfig = document.getElementById("productFormConfig");
const categoriesUrl = formConfig?.dataset.categoriesUrl;
const productsUrl = formConfig?.dataset.productsUrl;
const createUrl = formConfig?.dataset.createUrl;
const updateUrl = formConfig?.dataset.updateUrl;
const deleteUrl = formConfig?.dataset.deleteUrl;

function normalizeBaseUrl(url) {
  if (!url) {
    return "";
  }
  return url.endsWith("/") ? url : `${url}/`;
}

function buildProductDetailUrl(productId, slug) {
  const baseUrl = normalizeBaseUrl(productsUrl);
  return `${baseUrl}${productId}/${slug}/`;
}

function getCsrfToken() {
  return $('input[name="csrfmiddlewaretoken"]').val();
}

function getAjaxErrorMessage(xhr, fallbackMessage) {
  const response = xhr.responseJSON;

  if (response) {
    if (response.error) {
      return response.error;
    }

    if (response.detail) {
      return response.detail;
    }
  }

  if (xhr.responseText) {
    try {
      const parsedResponse = JSON.parse(xhr.responseText);
      if (parsedResponse.error) {
        return parsedResponse.error;
      }
    } catch (error) {
      // Ignore non-JSON responses and use the fallback below.
    }
  }

  return fallbackMessage || "Etwas ist schief gelaufen. Versuche es erneut.";
}

function setFormDataValue(formData, key, value) {
  if (typeof formData.set === "function") {
    formData.set(key, value);
  } else {
    formData.append(key, value);
  }
}

function isFormValid(requiredFields) {
  let isValid = true;

  for (let i = 0; i < requiredFields.length; i++) {
    const field = $(requiredFields[i]);
    if (field.val().trim() === "") {
      sendNotif("Bitte fülle alle Pflichtfelder aus!", "error");
      isValid = false;
      break;
    }
  }

  return isValid;
}

function disableSpinner($elem) {
  $elem.prop("disabled", false);
  $elem.find("svg").addClass("hidden");
  $elem.find(".bi").removeClass("hidden");
}

function enableSpinner($elem) {
  $elem.prop("disabled", true);
  $elem.find("svg").removeClass("hidden");
  $elem.find(".bi").addClass("hidden");
}

function createSpecificationRow(key = "", value = "") {
  return $(`
    <div class="specification-row grid grid-cols-1 gap-3 rounded-2xl border border-gray-200 bg-gray-50 p-4 md:grid-cols-2 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto] lg:items-end">
      <div>
        <label class="mb-2 block text-xs font-semibold uppercase tracking-wide text-gray-500">Bezeichnung</label>
        <input
          type="text"
          class="specification-key w-full rounded-xl border border-gray-200 bg-white px-4 py-3 text-gray-800 focus:border-blue-500 focus:outline-none"
          placeholder="z.B. PS"
        />
      </div>

      <div>
        <label class="mb-2 block text-xs font-semibold uppercase tracking-wide text-gray-500">Wert</label>
        <input
          type="text"
          class="specification-value w-full rounded-xl border border-gray-200 bg-white px-4 py-3 text-gray-800 focus:border-blue-500 focus:outline-none"
          placeholder="z.B. 150"
        />
      </div>

      <button
        type="button"
        class="remove-specification-row rounded-xl bg-red-50 px-4 py-3 font-semibold text-red-600 transition hover:bg-red-100 md:col-span-2 lg:col-span-1 lg:min-w-[120px]"
      >
        Entfernen
      </button>
    </div>
  `)
    .find(".specification-key").val(key).end()
    .find(".specification-value").val(value).end();
}

function toggleSpecificationPlaceholder() {
  const hasRows = $("#productSpecificationsList .specification-row").length > 0;
  $("#noSpecificationsPlaceholder").toggleClass("hidden", hasRows);
}

function collectProductSpecifications() {
  const specifications = [];
  const seenKeys = new Set();
  let hasIncompleteRow = false;
  let duplicateKey = "";

  $("#productSpecificationsList .specification-row").each(function (index) {
    const key = ($(this).find(".specification-key").val() || "").trim();
    const value = ($(this).find(".specification-value").val() || "").trim();

    if (!key && !value) {
      return;
    }

    if (!key || !value) {
      hasIncompleteRow = true;
      return false;
    }

    const normalizedKey = key.toLowerCase();
    if (seenKeys.has(normalizedKey)) {
      duplicateKey = key;
      return false;
    }

    seenKeys.add(normalizedKey);

    specifications.push({
      key: key,
      value: value,
      sort_order: index
    });
  });

  return {
    specifications,
    hasIncompleteRow,
    duplicateKey
  };
}

function appendSpecificationsToFormData(formData) {
  const result = collectProductSpecifications();

  if (result.hasIncompleteRow) {
    sendNotif("Bitte fülle bei jeder Spezifikation sowohl Bezeichnung als auch Wert aus.", "error");
    return false;
  }

  if (result.duplicateKey) {
    sendNotif(`Die Spezifikation "${result.duplicateKey}" ist doppelt vorhanden.`, "error");
    return false;
  }

  formData.append("specifications", JSON.stringify(result.specifications));
  return true;
}

function syncShowcaseState() {
  const isShowcaseOnly = $("#showcaseOnlySwitch").is(":checked");
  const $onlineSwitch = $("#onlineSwitch");
  const $showPriceSwitch = $("#showPriceWhenShowcaseSwitch");

  if (isShowcaseOnly) {
    $onlineSwitch.prop("checked", false);
    $onlineSwitch.prop("disabled", true);
    $showPriceSwitch.prop("disabled", false);
    $showPriceSwitch.closest("label").removeClass("opacity-60");
  } else {
    $onlineSwitch.prop("disabled", false);
    $showPriceSwitch.prop("disabled", true);
    $showPriceSwitch.closest("label").addClass("opacity-60");
  }
}

$(document).ready(function () {
  const categoryInput = $("#autocomplete-category-input");
  const autocompleteCategoryList = $("#autocomplete-category-list");
  const addCategoryBtn = $("#addCategory");
  const addedCategoryList = $("#added-category-list");
  const addedCategories = [];

  if (categoriesUrl) {
    $.ajax({
      url: categoriesUrl,
      type: "GET",
      dataType: "json",
      success: function (response) {
        categories = response.categories || [];

        $(".added-category .category-name").each(function () {
          const categoryName = $(this).text();
          addedCategories.push(categoryName);

          const index = categories.indexOf(categoryName);
          if (index !== -1) {
            categories.splice(index, 1);
          }
        });

        updateAutocompleteCategoryList(false);
      },
      error: function (error) {
        console.error("Error fetching categories:", error);
        sendNotif("Etwas konnte nicht geladen werden. Bitte lade die Seite neu.", "error");
      }
    });
  }

  toggleSpecificationPlaceholder();
  syncShowcaseState();

  $("#addSpecificationRow").on("click", function () {
    $("#productSpecificationsList").append(createSpecificationRow());
    toggleSpecificationPlaceholder();
  });

  $("#productSpecificationsList").on("click", ".remove-specification-row", function () {
    $(this).closest(".specification-row").remove();
    toggleSpecificationPlaceholder();
  });

  $("#showcaseOnlySwitch").on("change", function () {
    syncShowcaseState();
  });

  categoryInput.on("focus click input", function () {
    updateAutocompleteCategoryList(true);
  });

  addCategoryBtn.on("click", function () {
    const selectedCategory = categoryInput.val().trim();

    if (selectedCategory && !addedCategories.includes(selectedCategory)) {
      addCategory(selectedCategory);
      removeCategoryFromAutocomplete(selectedCategory);
      categoryInput.val("");
      categoryInput.focus();
    }
  });

  addedCategoryList.on("click", ".remove-category-btn", function () {
    const categoryToRemove = $(this).parent().data("category");
    removeCategory(categoryToRemove);
    addCategoryToAutocomplete(categoryToRemove);
  });

  $(document).on("click", function (event) {
    if (!categoryInput.is(event.target) && !autocompleteCategoryList.is(event.target)) {
      autocompleteCategoryList.addClass("hidden");
    }
  });

  function updateAutocompleteCategoryList(show) {
    const query = categoryInput.val().toLowerCase();
    const matchedCategories = categories.filter((category) =>
      category.toLowerCase().includes(query)
    );

    autocompleteCategoryList.html("");

    matchedCategories.forEach((match) => {
      const option = $("<div>")
        .addClass("px-4 py-2 hover:bg-blue-100 cursor-pointer")
        .text(match);

      option.on("click", function () {
        categoryInput.val(match);
        autocompleteCategoryList.addClass("hidden");
      });

      autocompleteCategoryList.append(option);
    });

    if (show) {
      autocompleteCategoryList.toggleClass("hidden", matchedCategories.length === 0);
    }
  }

  function addCategory(category) {
    addedCategories.push(category);
    renderAddedCategories();
  }

  function removeCategory(category) {
    const index = addedCategories.indexOf(category);
    if (index !== -1) {
      addedCategories.splice(index, 1);
      renderAddedCategories();
    }
  }

  function addCategoryToAutocomplete(category) {
    categories.push(category);
    updateAutocompleteCategoryList(true);
  }

  function removeCategoryFromAutocomplete(category) {
    const index = categories.indexOf(category);
    if (index !== -1) {
      categories.splice(index, 1);
      updateAutocompleteCategoryList(true);
    }
  }

  function renderAddedCategories() {
    addedCategoryList.html("");

    addedCategories.forEach((category) => {
      const categoryItem = $("<span>").addClass(
        "mx-1 my-2 flex-shrink-0 rounded-xl bg-blue-100 p-1.5 added-category"
      );
      const categoryName = $("<span>").addClass("category-name").text(category);
      const removeBtn = $("<span>")
        .html("&times;")
        .addClass("cursor-pointer pl-2 text-lg font-semibold text-red-500 remove-category-btn");

      categoryItem.append(categoryName, removeBtn);
      categoryItem.data("category", category);
      addedCategoryList.append(categoryItem);
    });
  }

  $("#title").on("input", function () {
    $("#titleSpan").text($(this).val());
  });

  $("#titleImgUpload").on("change", function () {
    const file = this.files[0];

    if (file) {
      const reader = new FileReader();

      reader.onload = function (e) {
        $("#productImage").attr("src", e.target.result);
        imageData = e.target.result;
        newImage = true;
      };

      reader.readAsDataURL(file);
    } else {
      $("#productImage").attr("src", "");
      newImage = false;
    }
  });

  $("#createProduct").on("click", function () {
    $("#createProductForm").submit();
  });

  $("#updateProduct").on("click", function () {
    $("#updateProductForm").submit();
  });

  $("#updateProductForm").on("submit", function (event) {
    event.preventDefault();
    enableSpinner($("#updateProduct"));

    if (!updateUrl) {
      disableSpinner($("#updateProduct"));
      sendNotif("Die Update URL fehlt. Bitte lade die Seite neu.", "error");
      return;
    }

    const files = $("#titleImgUpload").prop("files");
    const requiredFields = ["#title", "#description", "#price"];
    const isValid = isFormValid(requiredFields);

    if (!isValid) {
      disableSpinner($("#updateProduct"));
      return;
    }

    const formData = new FormData(this);
    setFormDataValue(formData, "title", $("#title").val());
    setFormDataValue(formData, "description", $("#description").val());
    setFormDataValue(formData, "isActive", $("#activeSwitch").is(":checked"));
    setFormDataValue(formData, "isInStock", $("#stockSwitch").is(":checked"));
    setFormDataValue(formData, "isReduced", $("#reducedSwitch").is(":checked"));
    setFormDataValue(formData, "hersteller", $("#autocomplete-hersteller-input").val());
    setFormDataValue(formData, "price", $("#price").val());
    setFormDataValue(formData, "weight", $("#weight").val());
    setFormDataValue(formData, "isOnlineAvailable", $("#onlineSwitch").is(":checked"));
    setFormDataValue(formData, "reducedPrice", $("#reducedPrice").val());
    setFormDataValue(formData, "selected_categories", JSON.stringify(addedCategories));
    setFormDataValue(formData, "isShowcaseOnly", $("#showcaseOnlySwitch").is(":checked"));
    setFormDataValue(formData, "showPriceWhenShowcase", $("#showPriceWhenShowcaseSwitch").is(":checked"));

    if (!appendSpecificationsToFormData(formData)) {
      disableSpinner($("#updateProduct"));
      return;
    }

    const selectedFileIds = typeof window.getSelectedProductFileIds === "function"
      ? window.getSelectedProductFileIds()
      : [];

    formData.append("selected_file_ids", JSON.stringify(selectedFileIds));

    const galeryId = $("#productGalery").attr("galery-id");
    if (galeryId && parseInt(galeryId, 10) > 0) {
      formData.append("galeryId", galeryId);
    }

    if (files && files[0]) {
      formData.append("title_image", files[0], "productTitleImage");
    }

    $.ajax({
      url: updateUrl,
      type: "POST",
      data: formData,
      contentType: false,
      processData: false,
      dataType: "json",
      beforeSend: function (xhr) {
        xhr.setRequestHeader("X-CSRFToken", getCsrfToken());
      },
      success: function (response) {
        disableSpinner($("#updateProduct"));

        if (response.success) {
          sendNotif("Das Produkt wurde erfolgreich gespeichert.", "success");
        } else {
          sendNotif(response.error || "Speichern fehlgeschlagen.", "error");
        }
      },
      error: function (xhr) {
        console.error(xhr);
        disableSpinner($("#updateProduct"));
        sendNotif(getAjaxErrorMessage(xhr), "error");
      }
    });
  });

  $("#deleteProduct").on("click", function () {
  if (!deleteUrl) {
    sendNotif("Die Delete URL fehlt. Bitte lade die Seite neu.", "error");
    return;
  }

  Swal.fire({
    title: "Produkt wirklich löschen?",
    text: "Das Produkt wird dauerhaft gelöscht. Diese Aktion kann nicht rückgängig gemacht werden.",
    icon: "warning",
    showCancelButton: true,
    confirmButtonColor: "#e3342f",
    cancelButtonColor: "#6c757d",
    confirmButtonText: "Ja, löschen!",
    cancelButtonText: "Abbrechen",
  }).then((result) => {
    if (!result.isConfirmed) {
      return;
    }

    sendNotif("Das Produkt wird gelöscht...", "info");

    $.ajax({
      url: deleteUrl,
      type: "POST",
      data: {
        csrfmiddlewaretoken: getCsrfToken(),
      },
      dataType: "json",
      success: function (response) {
        if (response.error) {
          Swal.fire({
            title: "Fehler",
            text: response.error || "Das Produkt konnte nicht gelöscht werden.",
            icon: "error",
          });
          return;
        }

        Swal.fire({
          title: "Gelöscht!",
          text: "Das Produkt wurde erfolgreich entfernt.",
          icon: "success",
          timer: 1500,
          showConfirmButton: false,
        }).then(() => {
          window.location.href = productsUrl;
        });
      },
      error: function (xhr) {
        console.error(xhr.responseText);
        Swal.fire({
          title: "Fehler",
          text: "Beim Löschen ist ein Fehler aufgetreten.",
          icon: "error",
        });
      }
    });
  });
});

  $("#createProductForm").on("submit", function (event) {
    event.preventDefault();
    enableSpinner($("#createProduct"));

    if (!createUrl) {
      disableSpinner($("#createProduct"));
      sendNotif("Die Create URL fehlt. Bitte lade die Seite neu.", "error");
      return;
    }

    const files = $("#titleImgUpload").prop("files");

    if (!files || files.length === 0) {
      disableSpinner($("#createProduct"));
      sendNotif("Bitte wähle ein Titelbild aus!", "error");
      return;
    }

    const requiredFields = ["#title", "#description", "#price"];
    const isValid = isFormValid(requiredFields);

    if (!isValid) {
      disableSpinner($("#createProduct"));
      return;
    }

    const formData = new FormData(this);
    const titleImage = files[0];

    setFormDataValue(formData, "title", $("#title").val());
    setFormDataValue(formData, "description", $("#description").val());
    setFormDataValue(formData, "isActive", $("#activeSwitch").is(":checked"));
    setFormDataValue(formData, "isInStock", $("#stockSwitch").is(":checked"));
    setFormDataValue(formData, "isReduced", $("#reducedSwitch").is(":checked"));
    setFormDataValue(formData, "hersteller", $("#autocomplete-hersteller-input").val());
    setFormDataValue(formData, "price", $("#price").val());
    setFormDataValue(formData, "weight", $("#weight").val());
    setFormDataValue(formData, "isOnlineAvailable", $("#onlineSwitch").is(":checked"));
    setFormDataValue(formData, "reducedPrice", $("#reducedPrice").val());
    setFormDataValue(formData, "selected_categories", JSON.stringify(addedCategories));
    setFormDataValue(formData, "isShowcaseOnly", $("#showcaseOnlySwitch").is(":checked"));
    setFormDataValue(formData, "showPriceWhenShowcase", $("#showPriceWhenShowcaseSwitch").is(":checked"));
    formData.append("title_image", titleImage, "productTitleImage");

    if (!appendSpecificationsToFormData(formData)) {
      disableSpinner($("#createProduct"));
      return;
    }

    const selectedFileIds = typeof window.getSelectedProductFileIds === "function"
      ? window.getSelectedProductFileIds()
      : [];

    formData.append("selected_file_ids", JSON.stringify(selectedFileIds));

    const galeryId = $("#productGalery").attr("galery-id");
    if (galeryId && parseInt(galeryId, 10) > 0) {
      formData.append("galeryId", galeryId);
    }

    $.ajax({
      url: createUrl,
      type: "POST",
      data: formData,
      contentType: false,
      processData: false,
      dataType: "json",
      beforeSend: function (xhr) {
        xhr.setRequestHeader("X-CSRFToken", getCsrfToken());
      },
      success: function (response) {
        if (response.success) {
          sendNotif("Das Produkt wurde erfolgreich erstellt.", "success");
          setTimeout(function () {
            window.location.href = buildProductDetailUrl(response.productId, response.slug);
            disableSpinner($("#createProduct"));
          }, 2000);
        } else {
          disableSpinner($("#createProduct"));
          sendNotif("Etwas lief schief. " + (response.error || ""), "error");
        }
      },
      error: function (xhr) {
        console.error(xhr);
        disableSpinner($("#createProduct"));
        sendNotif(getAjaxErrorMessage(xhr), "error");
      }
    });
  });
});
