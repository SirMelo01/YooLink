$(document).ready(function () {
    var csrftoken = $('input[name="csrfmiddlewaretoken"]').val();
    // Delete FAQ
    $(document).on("click", ".delete", function () {
        // Code for handling the click event on the "delete" button
        var $listItem = $(this).closest('.list-group-item')
        var id = $listItem.attr('data-id')
        sendNotif("Blog wird gelöscht...Bitte warten", "notice")
        $.ajax({
            url: id + "/delete/",
            type: 'POST',
            data: {
                csrfmiddlewaretoken: csrftoken,
            },
            dataType: 'json',
            success: function (response) {
                console.log(response);
                if (response.success) { 
                    $listItem.remove() 
                    sendNotif('Dieser Blog wurde erfolgreich gelöscht', 'success')
                }
            },
            error: function (xhr, status, error) {
                console.log(xhr.responseText);
                sendNotif('Es kam zu einem Fehler beim Löschen. Versuche es später nochmal', 'error')
            }
        });
    });
});