from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from products.models import Product
from .models import CartItem
import requests

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product
    )
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    messages.success(request, f'{product.name} added to cart!')
    return redirect('product_list')

@login_required
def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.get_total() for item in cart_items)
    return render(request, 'cart/cart.html', {
        'cart_items': cart_items,
        'total': total
    })

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
    cart_item.delete()
    messages.success(request, 'Item removed from cart.')
    return redirect('view_cart')

@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items:
        return redirect('view_cart')
    
    total = sum(item.get_total() for item in cart_items)
    total_kobo = int(total * 100)  # Paystack uses pesewas (smallest unit)
    
    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json',
    }
    data = {
        'email': request.user.email or 'customer@freshmart.com',
        'amount': total_kobo,
        'currency': 'GHS',
        'callback_url': 'http://127.0.0.1:8000/cart/payment-success/',
        'metadata': {
            'user_id': request.user.id,
            'cart_items': [
                {'product': item.product.name, 'quantity': item.quantity}
                for item in cart_items
            ]
        }
    }
    
    response = requests.post(
        'https://api.paystack.co/transaction/initialize',
        headers=headers,
        json=data
    )
    
    result = response.json()
    
    if result['status']:
        payment_url = result['data']['authorization_url']
        return redirect(payment_url)
    else:
        messages.error(request, 'Payment initialization failed. Please try again.')
        return redirect('view_cart')

@login_required
def payment_success(request):
    reference = request.GET.get('reference')
    if reference:
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        }
        response = requests.get(
            f'https://api.paystack.co/transaction/verify/{reference}',
            headers=headers
        )
        result = response.json()
        
        if result['status'] and result['data']['status'] == 'success':
            # Clear the cart
            CartItem.objects.filter(user=request.user).delete()
            messages.success(request, 'Payment successful! Your order has been placed.')
            return render(request, 'cart/payment_success.html')
    
    messages.error(request, 'Payment verification failed.')
    return redirect('view_cart')