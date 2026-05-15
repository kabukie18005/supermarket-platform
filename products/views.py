from django.shortcuts import render
from .models import Product

def home(request):
    featured_products = Product.objects.all()[:6]
    total_products = Product.objects.count()
    return render(request, 'products/home.html', {
        'featured_products': featured_products,
        'total_products': total_products
    })

def product_list(request):
    products = Product.objects.all()
    categories = Product.objects.values_list('category', flat=True).distinct()
    return render(request, 'products/product_list.html', {
        'products': products,
        'categories': categories
    })