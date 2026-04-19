from django.contrib import admin
from .models import ContentItem

@admin.register(ContentItem)
class ContentItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'category', 'status', 'rating', 'progress', 'updated_at']
    list_filter = ['category', 'status', 'rating']
    search_fields = ['title', 'user__username']
