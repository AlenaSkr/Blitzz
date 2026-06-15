from django.urls import path
from . import views

app_name = 'foods'  # Пространство имен для URL

urlpatterns = [
    # Главная страница
    path('', views.home, name='home'),  # re.html
    
    # Раздел/каталог
    path('razdel/', views.razdel, name='razdel'),  # razdel.html
    
    # О бренде
    path('brend/', views.brend, name='brend'),  # brend.html
    path('brand2/', views.brand2, name='brand2'),  # brand2.html
    
    # Квиз
    path('kwiz/', views.kwiz, name='kwiz'),  # kwiz.html
    
    path('catalog/', views.catalog, name='catalog'),
    path('auth/', views.auth_view, name='auth'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

        # КОРЗИНА
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:product_id>/', views.update_cart, name='update_cart'),
    path('cart/checkout/', views.checkout_view, name='checkout'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    path('quick-buy/', views.quick_buy_view, name='quick_buy'),
    path('profile/', views.profile_view, name='profile'),
]