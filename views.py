from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Q, Count, Avg
from .models import ContentItem, CATEGORY_CHOICES
from .forms import RegisterForm, ContentItemForm


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to TRAKORY, {user.username}!')
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'tracker/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'tracker/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    items = ContentItem.objects.filter(user=request.user)
    stats = {
        'total': items.count(),
        'completed': items.filter(status='Completed').count(),
        'watching': items.filter(status__in=['Watching', 'Reading', 'Playing']).count(),
        'planned': items.filter(status__in=['Plan to Watch', 'Plan to Read', 'Plan to Play']).count(),
    }
    by_category = {}
    for cat_key, cat_label in CATEGORY_CHOICES:
        by_category[cat_label] = items.filter(category=cat_key).count()

    recent = items[:5]
    avg_rating = items.exclude(rating__isnull=True).aggregate(avg=Avg('rating'))['avg']
    avg_rating = round(avg_rating, 1) if avg_rating else None

    return render(request, 'tracker/dashboard.html', {
        'stats': stats,
        'by_category': by_category,
        'recent': recent,
        'avg_rating': avg_rating,
        'categories': CATEGORY_CHOICES,
    })


@login_required
def content_list(request):
    items = ContentItem.objects.filter(user=request.user)
    category = request.GET.get('category', '')
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')

    if category:
        items = items.filter(category=category)
    if status:
        items = items.filter(status=status)
    if search:
        items = items.filter(Q(title__icontains=search) | Q(genre__icontains=search))

    return render(request, 'tracker/list.html', {
        'items': items,
        'categories': CATEGORY_CHOICES,
        'selected_category': category,
        'selected_status': status,
        'search': search,
    })


@login_required
def add_content(request):
    if request.method == 'POST':
        form = ContentItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()
            messages.success(request, f'"{item.title}" added successfully!')
            return redirect('list')
    else:
        form = ContentItemForm()
    return render(request, 'tracker/form.html', {'form': form, 'action': 'Add'})


@login_required
def edit_content(request, pk):
    item = get_object_or_404(ContentItem, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ContentItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{item.title}" updated!')
            return redirect('list')
    else:
        form = ContentItemForm(instance=item)
    return render(request, 'tracker/form.html', {'form': form, 'action': 'Edit', 'item': item})


@login_required
def delete_content(request, pk):
    item = get_object_or_404(ContentItem, pk=pk, user=request.user)
    if request.method == 'POST':
        title = item.title
        item.delete()
        messages.success(request, f'"{title}" deleted.')
        return redirect('list')
    return render(request, 'tracker/confirm_delete.html', {'item': item})
