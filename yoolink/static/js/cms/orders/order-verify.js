$(document).ready(function () {
    $('#orderForm').submit(function (event) {
        event.preventDefault(); // Prevent the default form submission

        var formData = {
            'orderId': $('#orderId').val(),
            'uuid': $('#uuid').val(),
            'address': $('#address').val(),
            'csrfmiddlewaretoken': $('[name="csrfmiddlewaretoken"]').val()
        };

        $.ajax({
            type: 'POST',
            url: '/cms/api/order/verify/',
            data: formData,
            dataType: 'json',
            success: function (data) {
                // Handle success, e.g., redirect or show a success message
                sendNotif(data.success, "success")
            },
            error: function (data) {
                // Handle errors, e.g., display error message to the user
                sendNotif(data.responseJSON.error, "error")
            }
        });
    });
});