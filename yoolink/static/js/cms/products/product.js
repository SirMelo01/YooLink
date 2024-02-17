$(document).ready(function () {
    $('#searchProduct').on('click', function () {
        var query = $('#searchProductInput').val();
        $.ajax({
            url: '/cms/products/search/?q=' + query,
            type: 'GET',
            success: function (data) {
                updateProductGrid(data.products);
            }
        });
    });

    function updateProductGrid(products) {
        var productGrid = $('#productGrid');
        productGrid.empty();
        for (var i = 0; i < products.length; i++) {
            var product = products[i];
            var productHtml = '<div class="flex h-full w-full rounded-2xl bg-blue-100 shadow-xl relative">';
            
            // Add the image
            productHtml += '<img class="w-36 rounded-l-2xl hidden sm:block" src="' + product.image_url + '" alt="" srcset="" />';
            
            // Add the product details
            productHtml += '<div class="space-y-2 p-3">';
            productHtml += '<h2 class="text-xl font-medium">' + product.title + '</h2>';
            productHtml += '<div class="h-16 max-h-16 overflow-y-scroll">' + product.description + '</div>';
            
            // Display the price or discount price
            if (product.discount_price !== null) {
                productHtml += '<span class="absolute top-0 left-0 inline-block px-2 py-1 text-sm font-semibold text-white bg-red-500 rounded-full z-40">' + product.discount_price + '€</span>';
            } else {
                productHtml += '<span class="absolute top-0 left-0 inline-block px-2 py-1 text-sm font-semibold text-white bg-green-500 rounded-full z-40">' + product.price + '€</span>';
            }
            
            // Add the "Verwalten" link
            productHtml += '<div class="flex justify-end px-2">';
            productHtml += '<a href="{% url "cms:images-view" %}" class="rounded bg-blue-500 px-4 py-1 font-bold text-white hover:bg-blue-700">Verwalten</a>';
            productHtml += '</div>';
            
            // Close the product container
            productHtml += '</div>';
            
            // Close the overall container
            productHtml += '</div>';
            
            // Append the product HTML to the grid
            productGrid.append(productHtml);
        }
    }
});