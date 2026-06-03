from django.urls import path
from . import views

urlpatterns = [
    path('cart/',        views.view_cart,       name='cart-view'),
    path('cart/add',     views.add_to_cart,     name='cart-add'),
    path('cart/update',  views.update_cart,     name='cart-update'),
    path('cart/remove',  views.remove_from_cart, name='cart-remove'),
    path('cart/clear',   views.clear_cart,      name='cart-clear'),
]
