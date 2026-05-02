// Save Text Content
$(document).ready(function () {
    const csrfToken = $('input[name="csrfmiddlewaretoken"]').val();

    $('#saveTextData').click(function (event) {
        event.preventDefault();

        const requestData = {
            name: $(this).attr('name'),
        };
        const customText = [];

        $('.text-content').each(function () {
            const $inputs = $(this).find('input, textarea');
            const key = $(this).attr("key");
            const inputList = {};

            $inputs.each(function () {
                const inputValue = $(this).val();
                const inputType = $(this).attr('inputType');
                /**
                 * Input Types:
                 * header -> Header
                 * title -> Title
                 * description -> Description
                 * buttonText -> Button Text
                 */

                if (inputType && inputType.trim() !== '' && inputValue.trim() !== '') {
                    inputList[inputType] = inputValue;
                }
            });

            if (key) {
                customText.push({
                    "key": key,
                    "inputs": inputList
                });
            }
        });

        requestData.customText = JSON.stringify(customText);

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
        const images = [];
        $('.content-image').each(function () {
            const imgId = $(this).attr('imgId');
            const key = $(this).attr('key');
            if (imgId && key && imgId !== '-1') {
                images.push({
                    "id": imgId,
                    "key": key
                });
            }
        });
        requestData.images = JSON.stringify(images);

        const galerien = [];
        $('.galery-container').each(function () {
            const galeryId = $(this).attr('galery-id');
            const key = $(this).attr('key');
            if (galeryId && key && galeryId !== "-1") {
                galerien.push({
                    "id": galeryId,
                    "key": key
                });
            }
        });
        requestData.galerien = JSON.stringify(galerien);

        /* ---------- Add all videos ---------- */
        const videos = [];
        $('.content-video').each(function () {
            const videoId = $(this).attr('videoId');
            const key = $(this).attr('key');
            if (videoId && key && videoId !== '-1') {
                videos.push({ id: videoId, key: key });
            }
        });
        requestData.videos = JSON.stringify(videos);

        $.ajax({
            type: "POST",
            url: "/cms/seiten/save/",
            data: requestData,
            beforeSend: function (xhr) {
                xhr.setRequestHeader("X-CSRFToken", csrfToken);
            },
            success: function (response) {
                if (response.success) {
                    sendNotif(response.success, "success");
                } else {
                    sendNotif(response.error, "error");
                }
            },
            error: function (error) {
                console.error("Error occurred: " + error.statusText);
                sendNotif("Beim Speichern ist ein Fehler aufgetreten", "error");
            }
        });
    });
});
