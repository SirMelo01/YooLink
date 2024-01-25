// Load images from backend
const $productGalery = $('#productGalery');
$(document).ready(function () {
    
    const $galeryModal = $('#galeryModal');

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
        $galeryModal.removeClass("hidden");
    });

    const $galeryModalContainer = $galeryModal.find('.modal-container');

    $(document).mouseup(function (e) {
        if (
            !$galeryModalContainer.is(e.target) &&
            $galeryModalContainer.has(e.target).length === 0
          ) {
            $galeryModal.addClass('hidden');
          }
    });

})

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
                const c = $productGalery.find('.slick-slide:not(.slick-cloned)')
                for (let i = c.length - 1; i >= 0; i--) {
                    $productGalery.slick("slickRemove", i)
                }
            
                data.images.forEach(function (image) {
                    const img = '<img src="' + image.upload_url + '" class="w-full rounded-xl" style="height: 16rem;">'
                    $productGalery.slick('slickAdd', '<div>' + img + '</div>');
                })
                $productGalery.attr('galery-id', id)
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
