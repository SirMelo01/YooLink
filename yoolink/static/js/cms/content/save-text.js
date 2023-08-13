// Save Text Content
$(document).ready(function () {
    var csrfToken = $('input[name="csrfmiddlewaretoken"]').val();
    $('#saveTextData').click(function () {
        var requestData = {
            name: $(this).attr('name'),
        };
        
        // Check if the element with ID 'header' exists before adding it to requestData
        if ($('#header').length > 0) {
            requestData.header = $('#header').val();
        }
        
        // Check if the element with ID 'title' exists before adding it to requestData
        if ($('#title').length > 0) {
            requestData.title = $('#title').val();
        }
        
        // Check if the element with ID 'description' exists before adding it to requestData
        if ($('#description').length > 0) {
            requestData.description = $('#description').val();
        }
        
        // Check if the element with ID 'buttonText' exists before adding it to requestData
        if ($('#buttonText').length > 0) {
            requestData.buttonText = $('#buttonText').val();
        }

        // Check images
        images = []
        $('.content-image').each(function() {
            // Check id
            imgId = $(this).attr('imgId');
            key = $(this).attr('key');
            if(imgId && key) {
                images.push({
                    "id": imgId,
                    "key": key
                })
            }
        });
        requestData.images = JSON.stringify(images);
        
        // Make the AJAX call
        $.ajax({
            type: "POST", // or "GET" depending on your server-side script
            url: "/cms/seiten/save/", // Replace this with your server-side script URL
            data: requestData,
            beforeSend: function (xhr) {
                // Add the CSRF token to the request headers
                xhr.setRequestHeader("X-CSRFToken", csrfToken);
            },
            success: function (response) {
                // Handle the response from the server
                if (response.success) {
                    sendNotif(response.success, "success")
                } else {
                    sendNotif(response.error, "error")
                }
            },
            error: function (error) {
                // Handle errors, if any
                console.error("Error occurred: " + error.statusText);
            }
        });
    })
})