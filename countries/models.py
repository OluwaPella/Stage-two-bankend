from django.db import models
from django.core.exceptions import ValidationError

class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)
    capital = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=50, blank=True, null=True)
    population = models.BigIntegerField()
    currency_code = models.CharField(max_length=10, blank=True, null=True)
    exchange_rate = models.DecimalField(max_digits=20, decimal_places=6, blank=True, null=True)
    estimated_gdp = models.DecimalField(max_digits=30, decimal_places=2, blank=True, null=True)
    flag_url = models.URLField(blank=True, null=True)
    last_refreshed_at = models.DateTimeField(auto_now=True)

    def clean(self):
        errors = {}
        if not self.name:
            errors['name'] = 'is required'
        if self.population is None:
            errors['population'] = 'is required'
        
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'countries'
        ordering = ['name']
