// Load images from backend
$editImg = null;
$editSlider = null;
$(document).ready(function () {

    const $imageModal = $('#imageModal');
    const $galeryModal = $('#galeryModal');

    $('.edit-img').click(function() {
        
        $editImg = $(this).siblings('img');
        $imageModal.removeClass("hidden");
    });

    $('#closeImageModal').click(function() {
        $imageModal.addClass("hidden");
    });

    $('#reloadImages').click(function() {
        loadImages(true)
    });

    /**
     * Galery Functions
     */

    $('#reloadGalerien').click(function() {
        loadGalerien(true)
    });

    $('#closeGaleryModal').click(function() {
        $galeryModal.addClass("hidden");
    });

    $('.edit-galery').click(function() {
        $editSlider = $(this).siblings('.carousel');
        $galeryModal.removeClass("hidden");
    });

    const $imageModalContainer = $imageModal.find('.modal-container');
    const $galeryModalContainer = $galeryModal.find('.modal-container');

    $(document).mouseup(function (e) {
        if (
            !$imageModalContainer.is(e.target) &&
            $imageModalContainer.has(e.target).length === 0 &&
            !$galeryModalContainer.is(e.target) &&
            $galeryModalContainer.has(e.target).length === 0
          ) {
            $imageModal.addClass('hidden');
            $galeryModal.addClass('hidden');
          }
    });

})

/**
 * Loads images into <possibleImages> div
 * and on click to placeId
 * @param {string} placeId 
 * @param {boolean} sendLoadMsg 
 */
function loadImages(sendLoadMsg) {
    $.ajax({
        url: '/cms/images/all/',
        type: 'GET',
        dataType: 'json',
        success: function (response) {
            // Erfolgreiche Anfrage
            if (response.image_urls && response.image_urls.length != 0) {
                $('#possibleImages').empty()
                response.image_urls.forEach(function (url) {
                    const $elem = $('<img src="' + url.url + '" imgId="' + url.id + '" class="h-28 w-full rounded-2xl col-span-1 mb-4 hover:shadow-2xl hover:cursor-pointer hover:scale-105">')
                    // Add Event Handler for selection
                    $elem.click(function () {
                        if ($editImg) {
                            $editImg.attr('src', $(this).attr('src'));
                            $editImg.attr('imgId', $(this).attr('imgId'))
                            $('#imageModal').toggleClass("hidden");
                            sendNotif('Neues Bild ausgewählt', 'success');
                        }
                    });
                    $('#possibleImages').append($elem)
                    if (sendLoadMsg) sendNotif("Alle Bilder wurden geladen", "success");
                });
            } else {
                if (sendLoadMsg) sendNotif("Keine Bilder wurden gefunden", "error");
            }
        },
        error: function (xhr, status, error) {
            // Fehler bei der Anfrage
            if (sendLoadMsg) sendNotif("Es kam zu einem unerwarteten Fehler, versuche es später nochmal", "error");
        }
    });
}

/**
 * Load all galerys and show them in the Modal
 * @param {*} sendLoadMsg 
 */
function loadGalerien(sendLoadMsg) {
    $.ajax({
        url: '/cms/galerien/all/',
        type: 'GET',
        dataType: 'json',
        success: function (response) {
            // Erfolgreiche Anfrage
            if (response.galerien && response.galerien.length != 0) {
                $('#possibleGalerien').empty()
                response.galerien.forEach(function (gallery) {
                    const $galleryItem = addTitleAndDescription(gallery.title, gallery.description, gallery.id);
                    $galleryItem.click(function() {
                        const galeryId = $(this).attr("galeryId")
                        // Ajax Call To get Galery Details and add to slick
                        sendNotif("Diese Galerie wird geladen...", "notice")
                        selectGalery(galeryId);
                    })
                    $('#possibleGalerien').append($galleryItem)
                    if (sendLoadMsg)sendNotif("Alle Galerien wurden geladen", "success");
                });
            } else {
                if (sendLoadMsg)sendNotif("Es wurden keine Galerien gefunden", "error");
            }
        },
        error: function (xhr, status, error) {
            // Fehler bei der Anfrage
            if (sendLoadMsg)sendNotif("Es kam zu einem unerwarteten Fehler, versuche es später nochmal", "error");
        }
    });
}

/**
 * Creates Galery Components for the Modal
 * TODO: Change to a nicer/more efficient design
 * @param {*} title 
 * @param {*} description 
 * @param {*} id 
 * @returns 
 */
function addTitleAndDescription(title, description, id) {
    var $div = $('<div>').addClass('border border-gray-200 shadow-xl rounded-2xl h-full w-full p-4 hover:cursor-pointer hover:shadow-blue-300');
    $div.attr('galeryId', id)
    var $title = $('<h1>').addClass('text-xl font-semibold mb-2').text(title);
    var $description = $('<p>').addClass('max-h-[8rem] overflow-auto').text(description);

    $div.append($title);
    $div.append($description);

    return $div;
}

/**
 * Select specific galery and load it
 * @param {*} id 
 */
function selectGalery(id) {
    $.ajax({
        url: "/cms/galery/getImages/", // Replace this with your API endpoint
        type: "GET",
        data: { "galeryId": id },
        dataType: "json", // The data type you expect to receive from the server
        success: function (data) {
            // This function will be executed if the request is successful
            if (data.images.length > 0) {
                const c = $editSlider.find('.slick-slide:not(.slick-cloned)')
                for (let i = c.length - 1; i >= 0; i--) {
                    $editSlider.slick("slickRemove", i)
                }
                const height = $('#galeryHeight').val()
                const width = $('#galeryWidth').val()
                data.images.forEach(function (image) {
                    const img = '<img src="' + image.upload_url + '" class="w-full rounded-xl" style="height: ' + height + '; width: ' + width + '">'
                    $editSlider.slick('slickAdd', '<div>' + img + '</div>');
                })
                $editSlider.closest(".relative").attr('galery-id', id)
                $('#galeryModal').addClass("hidden");
                sendNotif("Galerie wurde erfolgreich geladen", "success")
            } else {
                sendNotif("Diese Galerie ist leer. Bitte befülle sie erst!", "error")
            }
            // You can now process the received data
        },
        error: function (xhr, status, error) {
            // This function will be executed if the request fails
            console.error("Error:", error);
            sendNotif("Etwas hat nicht funktioniert. Versuche es später erneut", "error")
        }
    });
}
