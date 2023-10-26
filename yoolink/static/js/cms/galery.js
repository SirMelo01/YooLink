var csrftoken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;


$(document).ready(function () {
    var $editImg = null;

    // Click on Galery Save
    $('#saveGalery').click(function () {
        $('#galeryForm').submit();
    });
    
    // Delete the Galery and redirect
    $('#deleteGalery').click(function () {
        sendNotif('Die Galerie wird gelöscht...', 'info')
        $.ajax({
            type: 'post',
            url: 'delete/',
            data: { csrfmiddlewaretoken: csrftoken, },
            success: function (response) {
                console.log(response)
                if (response.error) {
                    sendNotif('Die Galerie konnte nicht gelöscht werden', 'error')
                    return;
                }
                sendNotif('Die Galerie wurde erfolgreich gelöscht!', 'success')
                window.location.href = '/cms/galerien/';
            }
        });
    })
    
    // Save the Galery (Update)
    $('#galeryForm').submit(function (e) {
        e.preventDefault()
        data = {
            csrfmiddlewaretoken: csrftoken,
            "title": $('#title').val(),
            "description": $('#description').val(),
            "place": $('#place').val()
        }
        $.ajax({
            type: 'post',
            url: 'save/',
            data: data,
            success: function (response) {
                if (response.error) {
                    sendNotif('Die Galerie konnte nicht gespeichert werden', 'error')
                    return;
                }
                sendNotif('Die Galerie wurde erfolgreich gespeichert', 'success')
                $('#titleSpan').text($('#title').val())
            }
        });
    })

    // Delete single Image of Galery
    $('.deleter').each(function () {
        // Klick-Handler für das aktuelle Element definieren
        $(this).on('click', function () {
            var elem = $(this)
            // Hier können Sie den Klick-Handler-Code für jedes Element schreiben
            $.ajax({
                url: '/cms/galery/delete-img/' + $(this).attr('id') + '/',
                method: 'POST',  // Methode auf "POST" setzen
                data: {
                    // Daten, die an den Server gesendet werden sollen
                    csrfmiddlewaretoken: csrftoken,
                },
                success: function (response) {
                    // Funktion, die ausgeführt wird, wenn die Anfrage erfolgreich ist
                    console.log(response);
                    sendNotif("Das ausgewählte Bild wurde erfolgreich gelöscht", "success")
                    elem.closest('.relative').remove();
                },
                error: function (error) {
                    // Funktion, die ausgeführt wird, wenn ein Fehler auftritt
                    console.log(error);
                    sendNotif("Beim Löschen des Bildes ist etwas schief gelaufen", "error")
                }
            });
        });
    });
    
    // Click on Edit Image (to change title)
    $('.edit-img').click(function () {
        // Find the parent div containing the image
        var parentDiv = $(this).closest('.relative');
    
        // Find the image element within the parent div
        var imgElement = parentDiv.find('img');
    
        // Get image source, title, and alt attributes
        var title = imgElement.attr('title');
        $editImg = imgElement
    
        $('#imgTitle').val(title)
        $('#editModal').removeClass('hidden')
    });
    
    $('#selectImg').on('click', function () {
        // Hier können Sie den Klick-Handler-Code für jedes Element schreiben
        if ($editImg === null) {
            sendNotif("Etwas ist schiefgelaufen. Versuche es später erneut.", "error")
            return;
        }
        if($('#imgTitle').val() == '') {
            sendNotif("Bitte gebe einen Titel ein!", "error")
            return;
        }

        $.ajax({
            url: '/cms/galery/images/update/' + $editImg.attr('key') + '/',
            method: 'POST',  // Methode auf "POST" setzen
            data: {
                // Daten, die an den Server gesendet werden sollen
                csrfmiddlewaretoken: csrftoken,
                title: $('#imgTitle').val()
            },
            success: function (response) {
                // Funktion, die ausgeführt wird, wenn die Anfrage erfolgreich ist
                if(response.success) {
                    sendNotif("Das ausgewählte Bild wurde erfolgreich bearbeitet!", "success")
                    $editImg.attr('title', $('#imgTitle').val())
                } else {
                    sendNotif(response.error, "error")
                }
                $('#editModal').addClass('hidden')
                
            },
            error: function (error) {
                // Funktion, die ausgeführt wird, wenn ein Fehler auftritt
                sendNotif("Beim Löschen des Bildes ist etwas schief gelaufen", "error")
            }
        });
    });

    // Close Image Edit Modal
    $('#closeModal').click(function () {
        $('#editModal').addClass('hidden')
    });

    const modalContainer = $('.modal-container');
    const editModal = $('#editModal');
    $(document).mouseup(function (e) {
        if (!modalContainer.is(e.target) && modalContainer.has(e.target).length === 0) {
            editModal.addClass('hidden');
        }
    });
});
