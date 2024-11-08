$(document).ready(function() {
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
        var global_font = $('#global_font').val();

        // AJAX-Anfrage zum Aktualisieren der Benutzereinstellungen
        $.ajax({
            type: 'POST',
            url: 'update/',  // Die URL aktualisieren
            data: {
                'email': email,
                'full_name': full_name,
                'company_name': company_name,
                'tel_number': tel_number,
                'fax_number': fax_number,
                'mobile_number': mobile_number,
                'website': website,
                'address': address,
                'global_font': global_font,
                'csrfmiddlewaretoken': csrfToken
            },
            success: function(response) {
                if(response.success) {
                    sendNotif(response.success, 'success');
                } else {
                    sendNotif(response.error ? response.error : 'Es kam zu einem Fehler. Versuche es erneut.', 'error');
                }
            },
            error: function(error) {
                sendNotif(error.error ? error.error : 'Es kam zu einem Fehler. Versuche es erneut.', 'error');
            }
        });
    });
});
