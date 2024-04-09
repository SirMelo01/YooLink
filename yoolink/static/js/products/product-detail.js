var csrftoken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
$(document).ready(function() {
    const $productImage = $("#productImage");

    $(".product-image").on("click", (event) => {
        $productImage.attr("src", $(event.target).attr("src"));
    });
    $('#addToCart').click(function() {
        var productId = $(this).attr('productId');
        var amount = $('#amount').val();

        if (!productId) {
            console.error('Product ID is missing.');
            sendNotif("Die Produkt-ID fehlt. Bitte neuladen.")
            return;
        }
        
        if (!amount || parseInt(amount) < 1) {
            console.error('Die Anzahl muss mindestens 1 sein.');
            return;
        }
        
        $.ajax({
            url: '/cms/api/cart/add/' + productId + '/',
            type: 'POST',
            data: {
                amount: parseInt(amount),
                csrfmiddlewaretoken: csrftoken,
            },
            success: function(response) {
                console.log(response);
                // Handle success response here
                if(response.success) {
                    sendNotif("Das Produkt wurde zum Warenkorb hinzugefügt", "success")
                } else {
                    sendNotif(response.error, "error")
                }
                

            },
            error: function(xhr, status, error) {
                var errorMessage = xhr.responseJSON.error;
                console.error(errorMessage);
                sendNotif(errorMessage, "error")
                // Handle error response here
            }
        });
    });
});