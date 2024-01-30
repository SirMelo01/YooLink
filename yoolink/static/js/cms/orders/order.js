$(document).ready(function () {
    const csrfToken = $('input[name="csrfmiddlewaretoken"]').val();
    $('#updateStatus').click(function () {
        $.ajax({
            url: 'update_order_status/',
            type: 'POST',
            data: { 'status': 'OPEN' },
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
                disableSpinner($('#updateProduct'));
                sendNotif("Etwas ist schief gelaufen. Versuche es erneut!", "error")

            }
        })
    })
});