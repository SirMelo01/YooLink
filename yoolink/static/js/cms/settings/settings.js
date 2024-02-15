$(document).ready(function() {
    // Handle form submission through AJAX
    const csrfToken = $('input[name="csrfmiddlewaretoken"]').val();
    $('#updateSettings').on('click', function() {
        var email = $('#email').val();
        var full_name = $('#full_name').val();
        var company_name = $('#company_name').val();
        var tel_number = $('#tel_number').val();
        var fax_number = $('#fax_number').val();
        var mobile_number = $('#mobile_number').val();
        var website = $('#website').val();
        var address = $('#address').val();

        // AJAX request to update user settings
        $.ajax({
            type: 'POST',
            url: 'update/',  // Update with the actual URL
            data: {
                'email': email,
                'full_name': full_name,
                'company_name': company_name,
                'tel_number': tel_number,
                'fax_number': fax_number,
                'mobile_number': mobile_number,
                'website': website,
                'address': address,
                'csrfmiddlewaretoken': csrfToken
            },
            success: function(response) {
                // Handle success, if needed
                console.log(response);
                if(response.success) {
                    sendNotif(response.success, 'success')
                } else {
                    sendNotif(response.error ? response.error : 'Es kam zu einem Fehler. Versuche es erneut.', 'error')
                }
            },
            error: function(error) {
                // Handle error, if needed
                sendNotif(error.error ? error.error : 'Es kam zu einem Fehler. Versuche es erneut.', 'error')
            }
        });
    });
});