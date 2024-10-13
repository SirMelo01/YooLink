
$(document).ready(function() {
    $('#emailForm').submit(function (event) {
        event.preventDefault(); // Prevent the default form submission
        console.log("Sende email...")
        // Send form data to the server using AJAX
        $.ajax({
          type: 'POST',
          url: '/cms/email/request/',
          data: $("#emailForm").serialize(),
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