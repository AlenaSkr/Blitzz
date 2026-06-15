from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User  
from django.contrib import messages
from django.conf import settings
from django.db import IntegrityError
from .models import Product
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import re
from decimal import Decimal
from .models import Order, OrderItem
from django.views.decorators.http import require_POST

def home(request):
    return render(request, 'home.html', {'active_page': 'home'})

def razdel(request):
    return render(request, 'razdel.html', {'active_page': 'razdel'})

def brend(request):
    return render(request, 'brend.html', {'active_page': 'about'})

def brand2(request):
    return render(request, 'brand2.html', {'active_page': 'about'})

def kwiz(request):
    return render(request, 'kwiz.html', {'active_page': 'kwiz'})

def about(request):
    return render(request, 're.html', {'active_page': 'about'})

def contacts(request):
    return render(request, 're.html', {'active_page': 'contacts'})

def catalog(request):
    # 1. Берем все активные товары из базы
    products = Product.objects.filter(is_active=True).order_by('id')
    
    # 2. Получаем параметры из URL (?age=adult&type=dry...)
    filter_age = request.GET.getlist('age')
    filter_type = request.GET.getlist('type')
    filter_series = request.GET.getlist('series')
    filter_breed = request.GET.getlist('breed')
    filter_weight = request.GET.getlist('weight') # Тут нужно аккуратно, в БД это число
    filter_ingredient = request.GET.getlist('ingredient')
    price_from = request.GET.get('price_from')
    price_to = request.GET.get('price_to')
    
    # 3. Фильтруем базу данных (Django ORM делает это быстро)
    if filter_age:
        products = products.filter(age__in=filter_age)
    if filter_type:
        products = products.filter(type__in=filter_type)
    if filter_series:
        products = products.filter(series__in=filter_series)
    if filter_breed:
        products = products.filter(breed__in=filter_breed)
    if filter_ingredient:
        products = products.filter(ingredient__in=filter_ingredient)
    if price_from:
        products = products.filter(price__gte=price_from)
    if price_to:
        products = products.filter(price__lte=price_to)
    
    # 4. Разбивка на страницы
    per_page = int(request.GET.get('per_page', 12))
    paginator = Paginator(products, per_page)
    products_page = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'catalog.html', {
        'products': products_page,
        'per_page': per_page,
        'active_page': 'catalog',
    })

def auth_view(request):
    if request.user.is_authenticated:
        return redirect('foods:home')
    return render(request, 'auth.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('foods:home')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        remember = request.POST.get('remember') == 'on'
        
        try:
            user_obj = User.objects.get(email__iexact=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None
        
        if user is not None:
            login(request, user)
            request.session.set_expiry(settings.SESSION_COOKIE_AGE if remember else 0)
            next_url = request.POST.get('next') or request.GET.get('next') or '/'
            return redirect(next_url)
        else:
            messages.error(request, 'Неверный email или пароль')
            
    return render(request, 'auth.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('foods:home')
        
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        
        errors = []
        if len(username) < 2: errors.append('Имя минимум 2 символа')
        if not email or '@' not in email: errors.append('Введите корректный email')
        if len(password) < 6: errors.append('Пароль минимум 6 символов')
        if password != password2: errors.append('Пароли не совпадают')
        if User.objects.filter(email__iexact=email).exists(): errors.append('Email уже занят')
        if User.objects.filter(username__iexact=username).exists(): errors.append('Имя уже занято')
        
        if errors:
            for err in errors: messages.error(request, err)
            return render(request, 'register.html')
            
        try:
            user = User.objects.create_user(username=username, email=email, password=password, first_name=username)
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                request.session.set_expiry(settings.SESSION_COOKIE_AGE)
                messages.success(request, f'Добро пожаловать, {username}! ')
                return redirect('home')
        except IntegrityError:
            messages.error(request, 'Ошибка создания аккаунта')
            
    return render(request, 'register.html')

def logout_view(request):
    logout(request)
    request.session.flush()
    messages.success(request, 'Вы вышли из системы')
    return redirect('home')

# ===== КОРЗИНА: ПРОСМОТР =====
def cart_view(request):
    cart = request.session.get('cart', {})
    
    # Получаем товары из базы для актуальных данных
    cart_items = []
    total = 0
    
    for product_id, item in cart.items():
        try:
            product = Product.objects.get(id=product_id, is_active=True)
            item_total = float(product.price) * item['quantity']
            total += item_total
            cart_items.append({
                'product': product,
                'quantity': item['quantity'],
                'item_total': item_total
            })
        except Product.DoesNotExist:
            # Если товар удалён из базы — убираем из корзины
            continue
    
    # Рекомендуемые товары (случайные 4 товара, исключая те что в корзине)
    cart_product_ids = list(cart.keys())
    recommended_products = Product.objects.filter(
        is_active=True
    ).exclude(
        id__in=cart_product_ids
    ).order_by('?')[:4]
    
    # Если рекомендуемых товаров меньше 4, добавляем ещё
    if len(recommended_products) < 4:
        all_products = Product.objects.filter(is_active=True)
        recommended_products = all_products.order_by('?')[:4]
    
    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total': total,
        'discount': 0,  # Если есть система скидок
        'recommended_products': recommended_products,
        'active_page': 'cart'
    })

# ===== ДОБАВИТЬ В КОРЗИНУ =====
def add_to_cart(request, product_id):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        quantity = int(request.POST.get('quantity', 1))
        
        if product_id in cart:
            cart[product_id]['quantity'] += quantity
        else:
            product = get_object_or_404(Product, id=product_id)
            cart[product_id] = {
                'name': product.name,
                'price': float(product.price),
                'quantity': quantity,
                'image': product.image.url if product.image else ''
            }
        
        request.session['cart'] = cart
        request.session.modified = True
        messages.success(request, 'Товар добавлен в корзину! 🛒')
        
    return redirect(request.META.get('HTTP_REFERER', 'foods:catalog'))

# ===== УДАЛИТЬ ИЗ КОРЗИНЫ =====
@require_POST
def remove_from_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    product_key = str(product_id)

    if product_key in cart:
        del cart[product_key]
        request.session['cart'] = cart
        request.session.modified = True  # ⚠️ Обязательно! Без этого сессия может не сохраниться
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'}, status=404)

# ===== ОБНОВИТЬ КОЛИЧЕСТВО =====
def update_cart(request, product_id):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        quantity = int(request.POST.get('quantity', 1))
        
        if product_id in cart and quantity > 0:
            cart[product_id]['quantity'] = quantity
            request.session['cart'] = cart
            request.session.modified = True
        elif quantity <= 0 and product_id in cart:
            del cart[product_id]
            request.session['cart'] = cart
            request.session.modified = True
    
    return redirect('foods:cart')

# ===== ОФОРМИТЬ ЗАКАЗ (только для авторизованных) =====
@login_required(login_url='foods:auth')
def checkout_view(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, 'Корзина пуста')
        return redirect('foods:catalog')
    
    # 1. Создаём заказ
    total = sum(Decimal(str(item['price'])) * item['quantity'] for item in cart.values())
    order = Order.objects.create(
        user=request.user,
        total=total,
        address="Не указан",  # Позже можно добавить форму ввода адреса
        phone="Не указан"
    )
    
    # 2. Добавляем товары в заказ
    for product_id, item in cart.items():
        try:
            product = Product.objects.get(id=product_id)
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item['quantity'],
                price=item['price']
            )
        except Product.DoesNotExist:
            continue
            
    # 3. Очищаем корзину и редиректим в профиль
    request.session['cart'] = {}
    request.session.modified = True
    messages.success(request, f'Заказ #{order.id} успешно оформлен!')
    return redirect('foods:profile')

# ===== ОЧИСТИТЬ КОРЗИНУ =====
def clear_cart(request):
    if request.method == 'POST':
        request.session['cart'] = {}
        request.session.modified = True
        messages.success(request, 'Корзина очищена')
    return redirect('foods:cart')

# ===== API ДЛЯ СЧЁТЧИКА КОРЗИНЫ =====
from django.http import JsonResponse

def cart_count_api(request):
    """Возвращает количество товаров в корзине для обновления шапки"""
    cart = request.session.get('cart', {})
    total_items = sum(item['quantity'] for item in cart.values())
    return JsonResponse({'count': total_items})
def quick_buy_view(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        phone = request.POST.get('phone', '').strip()
        
        if not product_id or quantity < 1 or not phone:
            return JsonResponse({'success': False, 'error': 'Заполните все поля'})
            
        clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
        if not re.match(r'^(\+7|7|8)?[0-9]{10}$', clean_phone):
            return JsonResponse({'success': False, 'error': 'Неверный формат телефона'})
            
        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Товар не найден'})
            
        # Здесь можно создать заказ в БД
        # Order.objects.create(...)
        
        return JsonResponse({
            'success': True, 
            'message': f'Заказ на {product.name} оформлен! Мы перезвоним на {clean_phone}'
        })
        
    return JsonResponse({'success': False, 'error': 'Метод не разрешён'})
@login_required(login_url='foods:auth')
def profile_view(request):
    # Берём заказы текущего пользователя, сортируем от новых к старым
    orders = Order.objects.filter(user=request.user) \
                          .prefetch_related('items__product') \
                          .order_by('-created_at')
    
    return render(request, 'profile.html', {
        'orders': orders,
        'active_page': 'profile'
    })