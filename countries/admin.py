from django.contrib import admin
from .models import Country

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name', 'capital', 'region', 'population', 'currency_code', 'estimated_gdp']
    list_filter = ['region', 'currency_code']
    search_fields = ['name', 'capital']
