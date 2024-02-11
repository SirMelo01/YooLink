var csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
$(document).ready(function () {

    $('#updateStatus').click(function () {
        var formData = new FormData();
        const status = $('#status').val()
        if(!status) {
            sendNotif("Status konnte nicht gefunden werden.", "error")
            return;
        }
        formData.append('status', status)
        $.ajax({
            url: 'update_order_status/',
            type: 'PATCH',
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
                    sendNotif(response.success, "success")
                } else {
                    sendNotif(response.error ? response.error : 'Es ist ein Fehler aufgetreten, versuche es erneut!', "error")
                }


            },
            error: function (error) {
                // Handle error
                console.error(error);
                sendNotif("Etwas ist schief gelaufen. Versuche es erneut!", "error")

            }
        })
    })
});