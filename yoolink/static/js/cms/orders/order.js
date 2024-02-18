var csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
$(document).ready(function () {

  $('#updateStatus').click(function () {
    var formData = new FormData();
    const status = $('#status').val()
    if (!status) {
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
        console.log("DONE")
        console.log(response.success)
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

  $('#deleteOrder').click(function () {
    $('#deleteModal').removeClass('hidden')
  })

  $('.close-delete-modal').click(() => {
    $('#deleteModal').addClass('hidden')
  })

  // Delete Product
  $('#deleteConfirm').click(function () {
    $('#deleteOrder').prop('disabled', true);
    $.ajax({
      url: "delete/",
      type: 'DELETE',
      data: {},
      beforeSend: function (xhr) {
        // Add the CSRF token to the request headers
        xhr.setRequestHeader("X-CSRFToken", csrfToken);
      },
      contentType: false,
      processData: false,
      dataType: 'json',
      success: function (response) {
        console.log(response);
        if (response.error) {
          sendNotif(response.error, 'error')
          $('#deleteOrder').prop('disabled', false);
        } else {
          sendNotif(response.success, 'success')
          $('#deleteModal').addClass('hidden')
          setTimeout(() => {
            window.location.href = '/cms/orders/';
          }, 1300)

        }
      },
      error: function (xhr, status, error) {
        console.log(xhr.responseText);
        $('#deleteOrder').prop('disabled', false);
        sendNotif('Es kam zu einem Fehler beim Löschen. Versuche es später nochmal', 'error')
      }
    });
  })

});