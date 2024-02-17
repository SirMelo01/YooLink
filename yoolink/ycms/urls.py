from django.urls import path, include
from . import views


app_name = "cms"
urlpatterns = [
    path("", views.upload, name="cms"),
    path("login/", views.Login_Cms, name="login"),
    path('logout/', views.custom_logout, name='logout'),
    # Images
    path('upload/', views.upload_view, name='upload'),
    path('upload/delete/<str:name>/', views.delete_file_by_name, name='upload-delete'),
    path('upload/post', views.file_upload_view, name='post-upload'),
    path('images/', views.images_view, name='images-view'),
    path('images/delete/<int:id>/', views.delete_file, name='image-delete'),
    path('images/update/<int:id>/', views.update_file, name='image-update'),
    path('images/all/', views.all_images, name="all-images"),
    # FAQ
    path('faq/sort/', views.update_faq_order, name='faq-sort'),
    path('faq/', views.faq_view, name='faq-view'),
    path('faq/update/', views.update_faq, name='faq-update'),
    path('faq/delete/<int:id>/', views.del_faq, name='faq-update'),
    # Blog
    path('blog/', views.blog_view, name='blog-view'),
    path('blog/add/', views.add_blog, name='blog-add'),
    path('blog/create/', views.create_blog, name='blog-create'),
    path('blog/<int:id>/', views.blog_details, name='blog-details'),
    path('blog/<int:id>/getCode/', views.blog_code, name='blog-code'),
    path('blog/<int:id>/delete/', views.delete_blog, name='blog-delete'),
    path('blog/<int:id>/update/', views.update_blog, name='blog-update'),
    # Galery
    path('galerien/', views.galerien, name='galerien'),
    path('galery/images/update/<int:id>/', views.update_galery_image, name='galery-update-img'),
    path('galery/create/', views.create_galery, name='galery-create'),
    path('galery/getImages/', views.get_galery_images, name='galery-get-images'),
    path('galery/delete-img/<int:id>/', views.delete_galery_img, name='delete-galery-img'),
    path('galery/<int:id>/', views.galery_view, name='galery-view'),
    path('galery/<int:id>/upload/', views.upload_galery_img, name='upload-galery-img'),
    path('galery/<int:id>/save/', views.save_galery, name='galery-save'),
    path('galery/<int:id>/delete/', views.delete_galery, name='galery-delete'),
    path('galerien/all/', views.all_galerien, name="all-galerien"),
    # Seiten
    path('seiten/', views.content_view, name='sites'),
    path('seiten/save/', views.saveTextContent, name='save_text_content'),
    path('seiten/hauptseite/', views.site_view_main, name='site_hauptseite'),
    path('seiten/hauptseite/Hero/', views.site_view_main_hero, name='site_hauptseite_hero'),
    path('seiten/hauptseite/Reponsive/', views.site_view_main_responsive, name='site_hauptseite_responsive'),
    path('seiten/hauptseite/CMS/', views.site_view_main_cms, name='site_hauptseite_cms'),
    path('seiten/hauptseite/Preis/', views.site_view_main_price, name='site_hauptseite_price'),
    path('seiten/hauptseite/Team/', views.site_view_main_team, name='site_hauptseite_team'),
    # Products
    path('products/', views.product_view, name='products'),
    path('products/search/', views.product_search, name='product_search'),
    # USER API Based search
    path('products/client/search/', views.search_products, name='product_client_search'),
    path('products/create/', views.product_create_view, name='product-create'),
    path('products/create/upload', views.product_create, name='product-create-upload'),
    path('products/<int:product_id>/<slug:slug>/', views.product_detail, name='product-detail'),
    path('products/<int:product_id>/<slug:slug>/update', views.product_update, name='product-detail-update'),
    path('products/<int:product_id>/<slug:slug>/delete', views.product_delete, name='product-detail-delete'),
    path('products/get_categories/', views.get_categories, name='get-categories'),
    path('products/get_brands/', views.get_brands, name='get-brands'),
    
    # ** START - Orders **

    path('api/cart/add/<int:product_id>/', views.add_to_cart, name='api-cart-add'),
    path('api/cart/', views.cart_items, name='api-cart'),
    path('api/cart/<int:order_item_id>/remove/', views.remove_from_cart, name='api-cart-remove'),
    path('api/cart/<int:order_item_id>/update-quantity/', views.update_quantity, name='api-cart-update-quantity'),
    path('api/cart/update/', views.update_cart_items, name='api-cart-update'),
    path('api/cart/verify/', views.verify_cart, name='api-cart-verify'),
    
    # PAYPAL endpoints
    path('cart/', views.cart_view, name='cart-view'),
    path('cart/success/', views.cart_verify_success_view, name='cart-verify-success-view'),

    # Other Order Stuff
    path('api/order/verify/', views.verify_order, name='api-order-verify'),
    path('order/verify/', views.order_verify_view, name='order-verify'),
    path('order/success/', views.order_verify_success_view, name='order-verify-success-view'),

    path('orders/', views.order_view, name='order-overview'),
    path('orders/<int:order_id>/', views.order_detail_view, name='order-detail-view'),
    # GET all orders by filter (as JSON)
    path('orders/filter/', views.get_orders, name='order-api'),
    # TODO: Still JSON Response. Change it to render view response
    path('api/orders/<int:order_id>/', views.get_order_by_id, name='get_order_by_id'),
    path('orders/<int:order_id>/update_order_status/', views.update_order_status_admin, name='update_order_status'),
    path('orders/<int:order_id>/delete/', views.delete_order, name='delete_order'),

    path('shop/', views.shop, name='shop'),
    # ** END - Orders **

    # Reviews
    path('reviews/<int:review_id>/delete_reviews/', views.delete_review, name='delete_review'),

    # Email
    path('email/request/', views.email_send, name='send-email'),
    
    # Settings
    path('settings/', views.user_settings_view, name='settings-view'),
    path('settings/update/', views.user_settings_update, name='settings-update'),
    
    # Opening Hours
    path('openinghours/', views.opening_hours_view, name='openinghours-view'),
    path('openinghours/update/', views.opening_hours_update, name='openinghours-update'),

]