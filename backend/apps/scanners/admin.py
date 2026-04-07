from django.contrib import admin
from .models import Location, ActiveScanner, ScannerLocationMapping


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'marketplace_url_slug']
    search_fields = ['name', 'marketplace_url_slug']
    ordering = ['name']


class ScannerLocationMappingInline(admin.TabularInline):
    model = ScannerLocationMapping
    extra = 1


@admin.register(ActiveScanner)
class ActiveScannerAdmin(admin.ModelAdmin):
    list_display = ['query', 'category', 'status']
    list_filter = ['status', 'category']
    search_fields = ['query', 'category']
    ordering = ['query']
    inlines = [ScannerLocationMappingInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('locations')


@admin.register(ScannerLocationMapping)
class ScannerLocationMappingAdmin(admin.ModelAdmin):
    list_display = ['scanner', 'location', 'is_active']
    list_filter = ['is_active']
    search_fields = ['scanner__query', 'location__name']
