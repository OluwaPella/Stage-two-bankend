from django.contrib import admin
from .models import Country, RefreshLog

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name', 'region', 'population', 'currency_code', 'estimated_gdp', 'last_refreshed_at']
    list_filter = ['region', 'currency_code']
    search_fields = ['name', 'capital']
    readonly_fields = ['last_refreshed_at']

@admin.register(RefreshLog)
class RefreshLogAdmin(admin.ModelAdmin):
    list_display = ['refreshed_at', 'total_countries']
    readonly_fields = ['refreshed_at', 'total_countries']
