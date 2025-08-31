var csrftoken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;

$(document).ready(function () {
    var $editImg = null;

    $('.deleter').each(function () {
        $(this).on('click', function () {
            var elem = $(this);

            // SweetAlert Confirm
            Swal.fire({
                title: 'Bist du sicher?',
                text: 'Dieses Bild wird dauerhaft gelöscht.',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6',
                confirmButtonText: 'Ja, löschen!',
                cancelButtonText: 'Abbrechen'
            }).then((result) => {
                if (result.isConfirmed) {
                    $.ajax({
                        url: 'delete/' + elem.attr('id') + '/',
                        method: 'POST',
                        data: {
                            csrfmiddlewaretoken: csrftoken,
                        },
                        success: function (response) {
                            console.log(response);
                            sendNotif("Das ausgewählte Bild wurde erfolgreich gelöscht", "success");
                            elem.closest('.relative').remove();
                        },
                        error: function (error) {
                            console.log(error);
                            sendNotif("Beim Löschen des Bildes ist etwas schief gelaufen", "error");
                        }
                    });
                }
            });
        });
    });



    // Klick-Handler für das aktuelle Element definieren
    $('#selectImg').on('click', function () {
        var elem = $(this)
        // Hier können Sie den Klick-Handler-Code für jedes Element schreiben
        if ($editImg === null) {
            sendNotif("Etwas ist schiefgelaufen. Versuche es später erneut.", "error")
            return;
        }
        $.ajax({
            url: 'update/' + $editImg.attr('key') + '/',
            method: 'POST',  // Methode auf "POST" setzen
            data: {
                // Daten, die an den Server gesendet werden sollen
                csrfmiddlewaretoken: csrftoken,
                title: $('#imgTitle').val(),
                place: $('#imgPlace').val()
            },
            success: function (response) {
                // Funktion, die ausgeführt wird, wenn die Anfrage erfolgreich ist
                if (response.success) {
                    sendNotif("Das ausgewählte Bild wurde erfolgreich bearbeitet!", "success")
                    $editImg.attr('title', $('#imgTitle').val())
                    $editImg.attr('place', $('#imgPlace').val())
                } else {
                    sendNotif(response.error, "error")
                }
                $('#editModal').addClass('hidden')

            },
            error: function (error) {
                // Funktion, die ausgeführt wird, wenn ein Fehler auftritt
                sendNotif("Beim Speichern des Bildes ist etwas schief gelaufen", "error")
            }
        });
    });


    $('.edit-img').click(function () {
        // Find the parent div containing the image
        var parentDiv = $(this).closest('.relative');

        // Find the image element within the parent div
        var imgElement = parentDiv.find('img');

        // Get image source, title, and alt attributes
        var title = imgElement.attr('title');
        var place = imgElement.attr('place');
        $editImg = imgElement

        if (place) {
            $('#imgPlace').val(place)
        } else {
            $('#imgPlace').val("nothing")
        }
        $('#imgTitle').val(title)
        $('#editModal').removeClass('hidden')
    })

    $('#closeModal').click(function () {
        $('#editModal').addClass('hidden')
    })

    // Close the modal when clicking outside of it
    const modalContainer = $('.modal-container');
    const editModal = $('#editModal');
    $(document).mouseup(function (e) {
        if (!modalContainer.is(e.target) && modalContainer.has(e.target).length === 0) {
            editModal.addClass('hidden');
        }
    });
});