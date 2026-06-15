from django.db import models
from django.contrib.auth.models import User


# Категория (например: Сухой корм, Лакомства)
class Category(models.Model):
    name = models.CharField("Название категории", max_length=100)
    slug = models.SlugField("URL (напр. dry-food)", max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

# Товар
class Product(models.Model):
    name = models.CharField("Название товара", max_length=200)
    # Цена будет храниться как число (например, 1020.00)
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2)
    
    # Связь с категорией (если есть)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Категория")
    
    # === ПОЛЯ ДЛЯ ФИЛЬТРАЦИИ (как в твоем старом коде) ===
    # age: puppy, adult, senior
    age = models.CharField("Возраст", max_length=20, blank=True, choices=[
        ('puppy', 'Щенок'), ('adult', 'Взрослый'), ('senior', 'Пожилой')
    ])
    
    # type: dry, wet, treat
    type = models.CharField("Тип", max_length=20, blank=True, choices=[
        ('dry', 'Сухой'), ('wet', 'Влажный'), ('treat', 'Лакомство')
    ])
    
    # Остальные параметры (строки)
    series = models.CharField("Линейка (напр. Sensitive)", max_length=50, blank=True)
    breed = models.CharField("Порода (напр. large)", max_length=50, blank=True, choices=[
        ('all', 'Все породы'), ('small', 'Мелкие'), ('large', 'Крупные')
    ])
    ingredient = models.CharField("Ингредиент (напр. lamb)", max_length=50, blank=True, choices=[
        ('chicken', 'Курица'), ('lamb', 'Ягненок'), ('salmon', 'Лосось'), ('turkey', 'Индейка'), ('duck', 'Утка')
    ])
    
    weight = models.DecimalField("Вес (кг)", max_digits=5, decimal_places=1)
    
    # Картинка товара
    image = models.ImageField("Фото товара", upload_to='products/', blank=True)
    is_active = models.BooleanField("Показывать на сайте?", default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

# ===== МОДЕЛИ ДЛЯ ЗАКАЗОВ =====

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Обрабатывается'),
        ('shipped', 'В пути'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменён'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total = models.DecimalField(max_digits=10, decimal_places=2)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
    
    def __str__(self):
        return f"Заказ #{self.id} от {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    class Meta:
        verbose_name = 'Товар в заказе'
        verbose_name_plural = 'Товары в заказе'