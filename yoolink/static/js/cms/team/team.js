var csrfTokenInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
$(document).ready(function () {
    let memberIdToDelete = null;
    const $imageModal = $('#imageModal');

    $('#closeImageModal').click(function() {
        $imageModal.addClass("hidden");
    });

    $('#reloadImages').click(function() {
        loadImages(true)
    });

    $('#bImageSelect').click(function() {
        $imageModal.removeClass("hidden");
    });

    const $imageModalContainer = $imageModal.find('.modal-container');

    $(document).mouseup(function (e) {
        if (
            !$imageModalContainer.is(e.target) &&
            $imageModalContainer.has(e.target).length === 0
          ) {
            $imageModal.addClass('hidden');
          }
    });

    // Funktion zum Erstellen eines neuen Teammitglieds
    $('#bCreateNewMember').click(function () {
        $('#teamMemberForm')[0].reset();  // Formular zurücksetzen
        $('#memberId').val('');  // Member ID löschen
        $('#modalTitle').text('Neues Teammitglied erstellen');
        $('#teamMemberModal').find('button[type="submit"]').text('Erstellen');
        $('#imagePreview').attr('src', '').addClass('hidden');  // Bildvorschau zurücksetzen
        $('#teamMemberModal').removeClass('hidden');  // Modal anzeigen
    });

    // Funktion zum Bearbeiten eines bestehenden Teammitglieds
    $('.edit-member').click(function () {
        const memberId = $(this).closest('div').siblings('.member-id').text().trim();

        // AJAX-GET-Request, um die Daten des Teammitglieds zu laden
        $.ajax({
            url: `${memberId}/`,
            type: 'GET',
            success: function (data) {
                $('#memberId').val(memberId);
                $('#full_name').val(data.full_name);
                $('#position').val(data.position);
                $('#years_with_team').val(data.years_with_team);
                $('#age').val(data.age);
                $('#email').val(data.email);
                $('#notes').val(data.note);
                $('#activeSwitch').prop('checked', data.active);
                $('#imagePreview').attr('src', data.image).removeClass('hidden');

                $('#modalTitle').text('Teammitglied bearbeiten');
                $('#teamMemberModal').find('button[type="submit"]').text('Speichern');
                $('#teamMemberModal').removeClass('hidden');
            },
            error: function () {
                sendNotif('Fehler beim Laden der Teammitglied-Daten.', 'error');
            }
        });
    });

    // AJAX-Request zum Erstellen oder Aktualisieren eines Teammitglieds
    $('#teamMemberForm').submit(function (event) {
        event.preventDefault();  // Verhindert die Standard-Formularübermittlung

        const memberId = $('#memberId').val();
        const isNewMember = !memberId;
        const url = isNewMember ? 'create/' : `${memberId}/update/`;
        const method = isNewMember ? 'POST' : 'PUT';

        const formData = {
            full_name: $('#full_name').val(),
            position: $('#position').val(),
            years_with_team: $('#years_with_team').val(),
            age: $('#age').val(),
            email: $('#email').val(),
            note: $('#notes').val(),
            active: $('#activeSwitch').is(':checked'),
            image: $('#imagePreview').attr('src'),  // Bildquelle
            csrfmiddlewaretoken: csrftoken,
        };

        // AJAX-Request
        $.ajax({
            url: url,
            type: method,
            data: JSON.stringify(formData),
            contentType: 'application/json',
            success: function (response) {
                sendNotif(response.success || 'Daten erfolgreich verarbeitet', "success")
                $('#teamMemberModal').addClass('hidden');  // Modal schließen
                location.reload();  // Seite neu laden, um die aktualisierten Daten anzuzeigen
            },
            error: function (error) {
                sendNotif(error.responseJSON.error || 'Fehler beim Speichern der Daten.', "error");
            }
        });
    });

    // Klick-Event für das Löschen-Symbol (X)
    $('.delete-member').click(function () {
        memberIdToDelete = $(this).closest('div').siblings('.member-id').text().trim();
        $('#confirmDeleteModal').removeClass('hidden');  // Bestätigungs-Modal anzeigen
    });

    // Klick-Event für Bestätigungs-Button im Bestätigungs-Modal
    $('#bConfirmDelete').click(function () {
        if (memberIdToDelete) {
            $.ajax({
                url: `/team/${memberIdToDelete}/delete/`,
                type: 'DELETE',
                success: function (response) {
                    sendNotif(response.success || 'Teammitglied erfolgreich gelöscht', "success");
                    $('#confirmDeleteModal').addClass('hidden');  // Bestätigungs-Modal schließen
                    location.reload();  // Seite neu laden, um die aktualisierte Teamliste zu sehen
                },
                error: function () {
                    sendNotif('Fehler beim Löschen des Teammitglieds', "error");
                    $('#confirmDeleteModal').addClass('hidden');  // Bestätigungs-Modal schließen
                }
            });
        }
    });

    // Klick-Event für den Abbrechen-Button im Bestätigungs-Modal
    $('#bDeclineDelete').click(function () {
        $('#confirmDeleteModal').addClass('hidden');  // Bestätigungs-Modal schließen
        memberIdToDelete = null;  // memberId zurücksetzen
    });

    loadImages(false);
});

// Modal schließen
function closeModal() {
    $('#teamMemberModal').addClass('hidden');
}

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
                const $imagePreview = $('#imagePreview')
                $('#possibleImages').empty()
                response.image_urls.forEach(function (url) {
                    const $elem = $('<img src="' + url.url + '" imgId="' + url.id + '" class="h-28 w-full rounded-2xl col-span-1 mb-4 hover:shadow-2xl hover:cursor-pointer hover:scale-105">')
                    // Add Event Handler for selection
                    $elem.click(function () {
                        if ($imagePreview) {
                            $imagePreview.attr('src', $(this).attr('src'));
                            $imagePreview.attr('imgId', $(this).attr('imgId'))
                            $('#imageModal').toggleClass("hidden");
                            $($imagePreview).removeClass("hidden");
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

