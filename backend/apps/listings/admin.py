from django.contrib import admin
from .models import Listing, Keyword


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ['title', 'price', 'location', 'query', 'search_location', 'watchlist', 'created_at']
    list_filter = ['watchlist', 'search_location', 'created_at']
    search_fields = ['title', 'query', 'location', 'search_location']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    list_display = ['keyword', 'filterID']
    list_filter = ['filterID']
    search_fields = ['keyword']
    ordering = ['filterID', 'keyword']
