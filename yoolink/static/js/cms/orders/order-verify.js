var csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
$(document).ready(function () {
    /**
     * Verify Cart (Send Email to buyer)
     */
    $('#verifyOrder').click(function () {
        enableSpinner($('#verifyOrder'));
        var orderItemCount = $(".order-item").length;
        if (orderItemCount === 0) {
            disableSpinner($('#verifyOrder'));
            sendNotif("Der Einkaufswagen ist leer. Bitte lade die Seite neu oder gehe zur Startseite.", "error")
            return;
        }
        // Check if Form is Valid
        var requiredFields = ['#buyerVorname', '#buyerName', '#address', '#country', '#city'];
        var isValid = isFormValid(requiredFields);
        if (!isValid) {
            disableSpinner($('#verifyOrder'));
            return;
        }

        const $payment = $(".active")
        if($payment.length < 1 || $payment.length > 1) {
            disableSpinner($('#verifyOrder'));
            sendNotif("Es wurde keine Bezahlmethode ausgewählt", "error")
            return;
        }

        // Create a new FormData object
        var formData = new FormData();
        formData.append('buyer_name', $('#buyerName').val());
        formData.append('buyer_prename', $('#buyerVorname').val());
        formData.append('address', $('#address').val());
        formData.append('city', $('#city').val());
        formData.append('country', $('#country').val());
        formData.append('token', $('#orderToken').val());
        formData.append('order_id', $('#orderId').val());
        formData.append('payment', $payment.val())

        // Verify Cart Post Request
        $.ajax({
            type: 'POST',
            url: '/cms/api/order/verify/',
            data: formData,
            contentType: false,
            processData: false,
            dataType: "json",
            beforeSend: function (xhr) {
                // Add the CSRF token to the request headers
                xhr.setRequestHeader("X-CSRFToken", csrfToken);
            },
            success: function (data) {
                // Handle success, e.g., redirect or show a success message
                sendNotif(data.success, "success")
            },
            error: function (data) {
                // Handle errors, e.g., display error message to the user
                sendNotif(data.responseJSON.error, "error")
                disableSpinner($('#verifyOrder'));
            }
        });


    });

    /**
     * Delete Item From Cart
     */
    $(".delete-item").each(function () {
        $(this).on("click", function () {
            // Hier können Sie den Code für die Löschfunktion einfügen
            // Verwenden Sie $(this), um auf das geklickte Element zuzugreifen
            console.log("Löschen geklickt für Element mit ID:", $(this).attr("id"));
            const $cartitem = $(this).closest('.order-item')
            const cartItemId = $cartitem.attr("order-item-id");

            // Delete Item
            $.ajax({
                type: 'DELETE',
                url: `/cms/api/cart/${cartItemId}/remove/`,
                data: {},
                contentType: false,
                processData: false,
                dataType: "json",
                beforeSend: function (xhr) {
                    // Add the CSRF token to the request headers
                    xhr.setRequestHeader("X-CSRFToken", csrfToken);
                },
                success: function (data) {
                    // Handle success, e.g., redirect or show a success message
                    if (data.success) {
                        $cartitem.remove();
                        sendNotif(data.success, "success")
                    } else {
                        sendNotif(data.error ? data.error : "Etwas ist schief gelaufen.", "error")
                    }

                },
                error: function (data) {
                    // Handle errors, e.g., display error message to the user
                    sendNotif(data.responseJSON.error, "error")
                }
            });
        });
    });

    $('#invoice').click(function () {
        $(this).addClass('border-2 border-orange-500 active')
        $('#pickup').removeClass('border-2 border-blue-500 active')
        console.log("invoice clicked")
    })

    $('#pickup').click(function () {
        $('invoice').removeClass('border-2 border-orange-500 active')
        $(this).addClass('border-2 border-blue-500 active')
        console.log("pickup")
    })

});

/**
 * Valid the Form
 */
function isFormValid(requiredFields) {
    var isValid = true;

    for (var i = 0; i < requiredFields.length; i++) {
        var field = $(requiredFields[i]);
        if (field.val().trim() === '') {
            sendNotif("Bitte fülle alle Pflichtfelder aus!", "error");
            isValid = false;
            break;
        }
    }
    return isValid;
}

/**
 * Check for Valid Email
 * @param {String} email 
 * @returns 
 */
function isValidEmail(email) {
    // Regular expression for validating an email address
    var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
* Disable Button Spinner
* @param {*} $elem 
*/
function disableSpinner($elem) {
    $elem.prop("disabled", false);
    $elem.find('svg').addClass('hidden');
    $elem.find('.bi').removeClass('hidden');
}

/**
 * Enable Button Spinner
 * @param {*} $elem 
 */
function enableSpinner($elem) {
    $elem.prop("disabled", true);
    $elem.find('svg').removeClass('hidden');
    $elem.find('.bi').addClass('hidden');
}