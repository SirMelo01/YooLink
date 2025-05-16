$(document).ready(function () {
    const csrfToken = $('input[name="csrfmiddlewaretoken"]').val();

    function uploadFile(type) {
        const input = document.getElementById(type);
        const file = input.files[0];

        if (!file) {
            sendNotif("Keine Datei ausgewählt", "warning");
            return;
        }

        const formData = new FormData();
        formData.append(type, file);
        formData.append('csrfmiddlewaretoken', csrfToken);

        $.ajax({
            url: `/cms/settings/logo/update/`,
            method: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: res => {
                if (res.success) {
                    sendNotif(res.success, "success");
                    location.reload();
                } else {
                    sendNotif(res.error || "Fehler beim Hochladen", "error");
                }
            },
            error: () => sendNotif("Fehler beim Hochladen", "error")
        });
    }

    function deleteFile(type) {
        $.post(`/cms/settings/logo/delete/`, {
            type: type,
            csrfmiddlewaretoken: csrfToken
        }, function (res) {
            if (res.success) {
                sendNotif(res.success, "success");
                location.reload();
            } else {
                sendNotif(res.error || "Fehler beim Löschen", "error");
            }
        });
    }

    $('#uploadLogo').click(() => uploadFile('logo'));
    $('#uploadFavicon').click(() => uploadFile('favicon'));
    $('#deleteLogo').click(() => deleteFile('logo'));
    $('#deleteFavicon').click(() => deleteFile('favicon'));
});
