from django.urls import path

from . import views

urlpatterns = [
    # CMS shop dashboard
    path("", views.shop, name="shop"),

    # CMS products
    path("products/", views.product_view, name="products"),
    path("products/search/", views.product_search, name="product_search"),
    path("products/create/", views.product_create_view, name="product-create"),
    path("products/create/upload", views.product_create, name="product-create-upload"),
    path("products/get_categories/", views.get_categories, name="get-categories"),
    path("products/get_brands/", views.get_brands, name="get-brands"),
    path("products/<int:product_id>/<slug:slug>/", views.product_detail, name="product-detail"),
    path("products/<int:product_id>/<slug:slug>/update", views.product_update, name="product-detail-update"),
    path("products/<int:product_id>/<slug:slug>/delete", views.product_delete, name="product-detail-delete"),

    # CMS orders
    path("orders/", views.order_view, name="order-overview"),
    path("orders/filter/", views.get_orders, name="order-api"),
    path("orders/<int:order_id>/", views.order_detail_view, name="order-detail-view"),
    path("orders/<int:order_id>/update_order_status/", views.update_order_status_admin, name="update_order_status"),
    path("orders/<int:order_id>/delete/", views.delete_order, name="delete_order"),

    # CMS order API
    path("api/orders/<int:order_id>/", views.get_order_by_id, name="get_order_by_id"),

    # CMS reviews
    path("reviews/<int:review_id>/delete_reviews/", views.delete_review, name="delete_review"),
]