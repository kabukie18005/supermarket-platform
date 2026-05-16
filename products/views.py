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
    query = request.GET.get('q', '')
    products = Product.objects.all()
    
    if query:
        products = products.filter(
            name__icontains=query
        ) | products.filter(
            category__icontains=query
        ) | products.filter(
            description__icontains=query
        )
    
    categories = Product.objects.values_list('category', flat=True).distinct()
    return render(request, 'products/product_list.html', {
        'products': products,
        'categories': categories,
        'query': query
    })