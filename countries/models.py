from django.db import models
from django.utils import timezone

class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)
    capital = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=50, blank=True, null=True)
    population = models.BigIntegerField()
    currency_code = models.CharField(max_length=10, blank=True, null=True)
    exchange_rate = models.FloatField(null=True, blank=True)
    estimated_gdp = models.FloatField(null=True, blank=True)
    flag_url = models.URLField(blank=True, null=True)
    last_refreshed_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class RefreshLog(models.Model):
    total_countries = models.IntegerField()
    refreshed_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-refreshed_at']
    
    def __str__(self):
        return f"Refresh at {self.refreshed_at} - {self.total_countries} countries"
