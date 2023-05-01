var csrftoken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;

$('#saveGalery').click(function () {
    $('#galeryForm').submit();
})

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

$('#galeryForm').submit(function (e) {
    e.preventDefault()
    data = {
        csrfmiddlewaretoken: csrftoken,
        "title": $('#title').val(),
        "description": $('#description').val(),
        "active": $('#activeSwitch').prop('checked')
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
})