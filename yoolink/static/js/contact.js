var csrftoken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
$(document).ready(function() {
    $('#emailForm').submit(function (event) {
        event.preventDefault(); // Prevent the default form submission
        console.log("Sende email...")
        var formData = {
          name: $('#name').val(),
          email: $('#email').val(),
          title: $('#title').val(),
          message: $('#message').val(),
          csrfmiddlewaretoken: csrftoken,
        };
        // Send form data to the server using AJAX
        $.ajax({
          type: 'POST',
          url: '/cms/email/request/',
          data: formData,
          success: function (response) {
            // Handle successful response here
            if (response.success) {
              sendNotif("Ihre Nachricht wurde erfolgreich gesendet", "success")
            }
            $('#emailForm')[0].reset();
          },
          error: function (xhr, status, error) {
            // Handle error response here
            console.error('Form submission failed');
            sendNotif("Etwas ist schief gelaufen. Versuchen Sie es bitte später nochmal.", "error")
          }
        });
      });
})