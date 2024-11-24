var csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;


$(document).ready(function () {
    // Ajax call to save opening hours
    $('#saveOpeningHours').on('click', function () {
        var openingHours = [];
        var days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'];
        var valid = true;

        days.forEach(function (day) {
            var isOpen = $('#' + day + ' .open-switch').prop('checked');
            var startTime = $('#' + day + ' .start-date').val();
            var endTime = $('#' + day + ' .end-date').val();
            var hasLunchBreak = $('#' + day + ' .lunch-break-switch').prop('checked');
            var lunchStart = $('#' + day + ' .lunch-start').val();
            var lunchEnd = $('#' + day + ' .lunch-end').val();

            if($('#' + day).length) {
                if (isOpen && (!startTime || !endTime || !/^([01]?[0-9]|2[0-3]):[0-5][0-9]$/.test(startTime) || !/^([01]?[0-9]|2[0-3]):[0-5][0-9]$/.test(endTime))) {
                    sendNotif('Bitte füllen Sie die Start- und Endzeit für ' + day + ' im richtigen Format (XX:XX) aus.', 'error');
                    valid = false;
                    return false; // Break loop
                }
                if (hasLunchBreak && (!lunchStart || !lunchEnd || !/^([01]?[0-9]|2[0-3]):[0-5][0-9]$/.test(lunchStart) || !/^([01]?[0-9]|2[0-3]):[0-5][0-9]$/.test(lunchEnd))) {
                    sendNotif('Bitte füllen Sie die Mittagszeiten für ' + day + ' im richtigen Format (XX:XX) aus.', 'error');
                    valid = false;
                    return false; // Break loop
                }
    
                openingHours.push({
                    day: day.toUpperCase(),
                    isOpen: isOpen,
                    startTime: isOpen ? startTime : null,
                    endTime: isOpen ? endTime : null,
                    hasLunchBreak: hasLunchBreak,
                    lunchBreakStart: lunchStart,
                    lunchBreakEnd: lunchEnd,
                });
            } else {
                console.log("Day Element does not exists - #" + day)
            }
 
        });

        if (!valid) return; // Abort if data is not valid
 
        var formData = new FormData();
        formData.append('opening_hours', JSON.stringify(openingHours))
        formData.append('vacation', $('#vacationSwitch').is(':checked')); // Convert boolean to string
        const vacationText = $('#vacationText').val();
        formData.append('vacationText', vacationText);

        $.ajax({
            type: 'POST',
            url: 'update/',
            data: formData,
            processData: false, // Prevent jQuery from processing the data
            contentType: false, // Prevent jQuery from setting the content type
            dataType: 'json',
            beforeSend: function (xhr) {
                // Add the CSRF token to the request headers
                xhr.setRequestHeader("X-CSRFToken", csrfToken);
            },
            success: function (response) {
                if(response.success) {
                    sendNotif(response.success, "success")
                } else {
                    sendNotif(response.error ? response.error : "Etwas ist schief gelaufen. Versuche es erneut.", "error")
                }
                // Handle success response
            },
            error: function (xhr, errmsg, err) {
                sendNotif("Etwas ist schief gelaufen. Versuche es erneut.", "error")
                // Handle error response
            }
        });
    });
});