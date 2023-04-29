$(document).ready(function () {
    var csrftoken = $('input[name="csrfmiddlewaretoken"]').val();
    // Delete FAQ
    $(document).on("click", ".delete", function () {
        // Code for handling the click event on the "delete" button
        var $listItem = $(this).closest('.list-group-item')
        var id = $listItem.attr('data-id')
        $.ajax({
            url: 'delete/' + id + "/",
            type: 'POST',
            data: {
                csrfmiddlewaretoken: csrftoken,
            },
            dataType: 'json',
            success: function (response) {
                console.log(response);
                alert("Success")
                if (response.success) { $listItem.remove() }
            },
            error: function (xhr, status, error) {
                console.log(xhr.responseText);
            }
        });
    });
});