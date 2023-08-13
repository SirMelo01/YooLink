// Load images from backend
$editImg = null;
$(document).ready(function () {
    $('.edit-img').click(function() {
        
        $editImg = $(this).siblings('img');
        $('#imageModal').removeClass("hidden");
    });

    $('#closeImageModal').click(function() {
        $('#imageModal').addClass("hidden");
    })

    $('#reloadImages').click(function() {
        loadImages(true)
    })

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
