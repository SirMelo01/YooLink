var imageData = null;
var newImage = false;
let categories = [
  /* ... add more options ... */
];
// Update the function to fetch categories
$(document).ready(function () {
  $.ajax({
    url: '/cms/products/get_categories/',  // Update with your actual URL
    type: 'GET',
    dataType: 'json',
    success: function (response) {
      categories = response.categories;
      $('.added-category .category-name').each(function () {
        const categoryName = $(this).text();
        addedCategories.push(categoryName)
        const index = categories.indexOf(categoryName);
        if (index !== -1) {
          categories.splice(index, 1);
        }
      });
      updateAutocompleteCategoryList(false);
    },
    error: function (error) {
      console.error('Error fetching categories:', error);
      sendNotif("Etwas konnte nicht geladen werden. Bitte lade die Seite neu")
    }
  });
  const categoryInput = $('#autocomplete-category-input');
  const autocompleteCategoryList = $('#autocomplete-category-list');
  const addCategoryBtn = $('#addCategory');
  const addedCategoryList = $('#added-category-list');

  // Event listener for input focus, click, and input change
  categoryInput.on('focus click input', function () {
    updateAutocompleteCategoryList(true);
  });

  // Event listener for add category button
  addCategoryBtn.on('click', function () {
    const selectedCategory = categoryInput.val().trim();
    console.log(selectedCategory)
    console.log(categories.includes(selectedCategory))
    if (selectedCategory && !addedCategories.includes(selectedCategory)) {
      if (!categories.includes(selectedCategory)) {
        // Add it to backend !

      }
      // Add the category to the added categories list
      addCategory(selectedCategory);
      // Remove the category from the autocomplete list
      removeCategoryFromAutocomplete(selectedCategory);
      categoryInput.val('');
      // Reset focus to the input field
      categoryInput.focus();
    }
  });

  // Event delegation for removing categories
  addedCategoryList.on('click', '.remove-category-btn', function () {
    const categoryToRemove = $(this).parent().data('category');
    // Remove the category from the added categories list
    console.log("Remove 1")
    removeCategory(categoryToRemove);
    // Add the category back to the autocomplete list
    addCategoryToAutocomplete(categoryToRemove);
  });

  $(document).on('click', function (event) {
    if (!categoryInput.is(event.target) && !autocompleteCategoryList.is(event.target)) {
      autocompleteCategoryList.addClass('hidden');
    }
  });

  function updateAutocompleteCategoryList(show) {
    const query = categoryInput.val().toLowerCase();
    console.log(categories)
    const matchedCategories = categories.filter(category => category.toLowerCase().includes(query.toLowerCase())
    );
    // Clear previous options
    autocompleteCategoryList.html('');

    // Display matched options
    matchedCategories.forEach(match => {
      const option = $('<div>').addClass('px-4 py-2 hover:bg-blue-100 cursor-pointer').text(match);

      option.on('click', function () {
        categoryInput.val(match);
        autocompleteCategoryList.addClass('hidden');
      });

      autocompleteCategoryList.append(option);
    });

    // Show/hide the autocomplete list
    if (show) autocompleteCategoryList.toggleClass('hidden', matchedCategories.length === 0);
  }

  function addCategory(category) {
    addedCategories.push(category);
    renderAddedCategories();
  }

  function removeCategory(category) {
    const index = addedCategories.indexOf(category);
    console.log("Remove Category: " + index)
    if (index !== -1) {
      addedCategories.splice(index, 1);
      console.log("Render Added Categories")
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
    addedCategoryList.html('');
    addedCategories.forEach(category => {
      const categoryItem = $('<span>').addClass('mx-1 my-2 flex-shrink-0 rounded-xl bg-blue-100 p-1.5 added-category');
      const categoryName = $('<span>').text(category);
      const removeBtn = $('<span>').html('&times;').addClass('cursor-pointer pl-2 text-lg font-semibold text-red-500 remove-category-btn');

      categoryItem.append(categoryName, removeBtn);
      categoryItem.data('category', category);
      addedCategoryList.append(categoryItem);
    });
  }

  // Initial empty array for added categories
  const addedCategories = [];

  $('#title').on('input', function () {
    const newTitle = $(this).val();
    $('#titleSpan').text(newTitle);
  });

  /** Image Uploader */
  $('#titleImgUpload').change(function () {
    console.log("Title Image Upload")
    // Get the uploaded file
    var file = this.files[0];

    console.log(file)

    // Check if a file is selected
    if (file) {
      // Create a FileReader
      var reader = new FileReader();

      // Set up the FileReader onload event
      reader.onload = function (e) {
        console.log("load it")
        // Set the source of the preview image to the FileReader result
        $('#productImage').attr('src', e.target.result);
        // Show the preview image
        imageData = e.target.result
        newImage = true;
      };

      // Read the uploaded file as a data URL
      reader.readAsDataURL(file);
    } else {
      // Hide the preview image if no file is selected
      $('#productImage').attr('src', "");
      newImage = false;

    }
  });

  // Create Product
  $('#createProduct').on("click", function () {
    $('#createProductForm').submit();
  })

  // Create Product
  $('#updateProduct').on("click", function () {
    $('#updateProductForm').submit();
  })

  const csrfToken = $('input[name="csrfmiddlewaretoken"]').val();
  // Update Product Form
  $('#updateProductForm').on("submit", function (event) {
    enableSpinner($('#updateProduct'))
    event.preventDefault();
    console.log("Update Product Form");

    var files = $('#titleImgUpload').prop("files");

    var requiredFields = ['#title', '#description', '#price'];
    var isValid = isFormValid(requiredFields);

    if (!isValid) {
      disableSpinner($('#updateProduct'));
      return;
    }

    var formData = new FormData(this);
    // Add additional fields to FormData
    formData.append('title', $('#title').val());
    formData.append('description', $('#description').val());
    formData.append('isActive', $('#activeSwitch').is(':checked'));
    formData.append('isInStock', $('#stockSwitch').is(':checked'));
    formData.append('isReduced', $('#reducedSwitch').is(':checked'));
    formData.append('hersteller', $('#autocomplete-hersteller-input').val())
    formData.append('price', $('#price').val());
    formData.append('weight', $('#weight').val());
    formData.append('isOnlineAvailable', $('#onlineSwitch').is(':checked'));
    formData.append('reducedPrice', $('#reducedPrice').val());
    formData.append('selected_categories', JSON.stringify(addedCategories));
    console.log(JSON.stringify(addedCategories))
    const galeryId = $('#productGalery').attr('galery-id')
    if (galeryId && parseInt(galeryId) > 0) {
      formData.append('galeryId', galeryId)
    }
    if (files && files[0]) {
      formData.append('title_image', files[0], "productTitleImage");
    }

    console.log(formData);

    $.ajax({
      url: 'update',
      type: 'POST',
      data: formData,
      contentType: false,
      processData: false,
      dataType: "json",
      beforeSend: function (xhr) {
        // Add the CSRF token to the request headers
        xhr.setRequestHeader("X-CSRFToken", csrfToken);
      },
      success: function (response) {
        // Handle success
        console.log(response);
        // redirect to detail page
        disableSpinner($('#updateProduct'));
        if (response.success) {
          sendNotif("Das Produkt wurde erfolgreich gespeichert", "success")
        } else {
          sendNotif(response.error, "error")
        }


      },
      error: function (error) {
        // Handle error
        console.error(error);
        disableSpinner($('#updateProduct'));
        sendNotif("Etwas ist schief gelaufen. Versuche es erneut!", "error")

      }
    });

  })

  $('#deleteProduct').click(function () {
    $('#deleteModal').removeClass('hidden')
  })

  $('.close-delete-modal').click(() => {
    $('#deleteModal').addClass('hidden')
  })

  // Delete Product
  $('#deleteConfirm').click(function () {
    $.ajax({
      url: "delete",
      type: 'POST',
      data: {
        csrfmiddlewaretoken: csrfToken,
      },
      dataType: 'json',
      success: function (response) {
        console.log(response);
        if (response.error) {
          sendNotif(response.error, 'error')
        } else {
          sendNotif("Das Produkt wurde erfolgreich gelöscht. Warte aufs Umleiten...", 'success')
          window.location.href = '/cms/products/';
          setTimeout(() => {
            window.location.href = '/cms/products/';
          }, 2000)
        }
      },
      error: function (xhr, status, error) {
        console.log(xhr.responseText);
        sendNotif('Es kam zu einem Fehler beim Löschen. Versuche es später nochmal', 'error')
      }
    });
  })

  // Create Product Form
  $('#createProductForm').on("submit", function (event) {
    enableSpinner($('#createProduct'))
    event.preventDefault();
    console.log("Create Product Form");

    var files = $('#titleImgUpload').prop("files");

    if (files.length == 0) {
      disableSpinner($('#createProduct'));
      sendNotif("Bitte wähle ein Titelbild aus!", "error")
      return;
    }

    // Validate required fields
    var requiredFields = ['#title', '#description', '#price'];
    var isValid = isFormValid(requiredFields);

    if (!isValid) {
      disableSpinner($('#createProduct'));
      return;
    }

    // Using FormData to gather form data
    var formData = new FormData(this);
    const title_image = files[0]
    // Add additional fields to FormData
    formData.append('title', $('#title').val());
    formData.append('description', $('#description').val());
    formData.append('isActive', $('#activeSwitch').is(':checked'));
    formData.append('isInStock', $('#stockSwitch').is(':checked'));
    formData.append('isReduced', $('#reducedSwitch').is(':checked'));
    formData.append('hersteller', $('#autocomplete-hersteller-input').val())
    formData.append('price', $('#price').val());
    formData.append('weight', $('#weight').val());
    formData.append('isOnlineAvailable', $('#onlineSwitch').is(':checked'));
    formData.append('reducedPrice', $('#reducedPrice').val());
    formData.append('title_image', title_image, "productTitleImage");
    formData.append('selected_categories', JSON.stringify(addedCategories));
    const galeryId = $('#productGalery').attr('galery-id')
    if (galeryId && parseInt(galeryId) > 0) {
      formData.append('galeryId', galeryId)
    }
    console.log(JSON.stringify(addedCategories))

    console.log(formData);

    // Use Ajax to send the FormData
    $.ajax({
      url: 'upload',
      type: 'POST',
      data: formData,
      contentType: false,
      processData: false,
      dataType: "json",
      beforeSend: function (xhr) {
        // Add the CSRF token to the request headers
        xhr.setRequestHeader("X-CSRFToken", csrfToken);
      },
      success: function (response) {
        // Handle success
        console.log(response);
        // redirect to detail page
        if (response.success) {
          sendNotif("Das Produkt wurde erfolgreich erstellt", "success");
          setTimeout(() => {
            window.location.href = '/cms/products/' + response.productId + "/" + response.slug + "/";
            disableSpinner($('#createProduct'));
          }, 2000)
        } else {
          sendNotif("Etwas lief schief. " + response.error, "error");
        }

      },
      error: function (error) {
        // Handle error
        console.error(error);
        disableSpinner($('#createProduct'));
        sendNotif(response.error, "error")
      }
    });
  });

});

/**
 * Valid the Form
 */
function isFormValid(requiredFields) {
  var isValid = true;

  for (var i = 0; i < requiredFields.length; i++) {
    var field = $(requiredFields[i]);
    if (field.val().trim() === '') {
      sendNotif("Bitte fülle alle Pflichtfelder aus!", "error");
      isValid = false;
      break;
    }
  }
  return isValid;
}

/**
* Disable Button Spinner
* @param {*} $elem 
*/
function disableSpinner($elem) {
  $elem.prop("disabled", false);
  $elem.find('svg').addClass('hidden');
  $elem.find('.bi').removeClass('hidden');
}

/**
 * Enable Button Spinner
 * @param {*} $elem 
 */
function enableSpinner($elem) {
  $elem.prop("disabled", true);
  $elem.find('svg').removeClass('hidden');
  $elem.find('.bi').addClass('hidden');
}
