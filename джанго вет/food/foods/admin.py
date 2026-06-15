from django.contrib import admin
from .models import Category, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)} # Автозаполнение URL при вводе названия
    list_display = ('name', 'slug')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'weight', 'is_active')
    list_filter = ('category', 'age', 'type', 'is_active', 'breed') # Удобные фильтры справа
    search_fields = ('name',) # Поиск по названию