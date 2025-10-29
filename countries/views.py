from django.http import JsonResponse, HttpResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
import os
from django.conf import settings
from .models import Country, RefreshLog
from .utils import refresh_countries_data, generate_summary_image

@method_decorator(csrf_exempt, name='dispatch')
class RefreshCountriesView(View):
    def post(self, request):
        try:
            result = refresh_countries_data()
            
            # Generate summary image after refresh
            generate_summary_image()
            
            return JsonResponse({
                'message': 'Countries data refreshed successfully',
                **result
            })
        except Exception as e:
            return JsonResponse({
                'error': 'External data source unavailable',
                'details': str(e)
            }, status=503)

class CountriesListView(View):
    def get(self, request):
        countries = Country.objects.all()
        
        # Apply filters
        region = request.GET.get('region')
        currency = request.GET.get('currency')
        sort_by = request.GET.get('sort')
        
        if region:
            countries = countries.filter(region__iexact=region)
        if currency:
            countries = countries.filter(currency_code__iexact=currency)
        
        # Apply sorting
        if sort_by == 'gdp_desc':
            countries = countries.order_by('-estimated_gdp')
        elif sort_by == 'gdp_asc':
            countries = countries.order_by('estimated_gdp')
        elif sort_by == 'population_desc':
            countries = countries.order_by('-population')
        elif sort_by == 'population_asc':
            countries = countries.order_by('population')
        elif sort_by == 'name_asc':
            countries = countries.order_by('name')
        elif sort_by == 'name_desc':
            countries = countries.order_by('-name')
        else:
            countries = countries.order_by('name')
        
        data = []
        for country in countries:
            data.append({
                'id': country.id,
                'name': country.name,
                'capital': country.capital,
                'region': country.region,
                'population': country.population,
                'currency_code': country.currency_code,
                'exchange_rate': country.exchange_rate,
                'estimated_gdp': country.estimated_gdp,
                'flag_url': country.flag_url,
                'last_refreshed_at': country.last_refreshed_at.isoformat()
            })
        
        return JsonResponse(data, safe=False)

class CountryDetailView(View):
    def get(self, request, name):
        try:
            country = Country.objects.get(name__iexact=name)
            data = {
                'id': country.id,
                'name': country.name,
                'capital': country.capital,
                'region': country.region,
                'population': country.population,
                'currency_code': country.currency_code,
                'exchange_rate': country.exchange_rate,
                'estimated_gdp': country.estimated_gdp,
                'flag_url': country.flag_url,
                'last_refreshed_at': country.last_refreshed_at.isoformat()
            }
            return JsonResponse(data)
        except Country.DoesNotExist:
            return JsonResponse({'error': 'Country not found'}, status=404)
    
    def delete(self, request, name):
        try:
            country = Country.objects.get(name__iexact=name)
            country.delete()
            return JsonResponse({'message': f'Country {name} deleted successfully'})
        except Country.DoesNotExist:
            return JsonResponse({'error': 'Country not found'}, status=404)

class StatusView(View):
    def get(self, request):
        try:
            latest_refresh = RefreshLog.objects.first()
            total_countries = Country.objects.count()
            
            data = {
                'total_countries': total_countries,
                'last_refreshed_at': latest_refresh.refreshed_at.isoformat() if latest_refresh else None
            }
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({'error': 'Internal server error'}, status=500)

class CountriesImageView(View):
    def get(self, request):
        image_path = os.path.join(settings.BASE_DIR, 'cache', 'summary.png')
        text_path = os.path.join(settings.BASE_DIR, 'cache', 'summary.txt')
        
        if not os.path.exists(image_path):
            if os.path.exists(text_path):
                # Return text summary if image not available
                with open(text_path, 'r') as f:
                    return JsonResponse({
                        'message': 'Image not available, but text summary exists',
                        'summary': f.read()
                    })
            return JsonResponse({'error': 'Summary image not found'}, status=404)
        
        try:
            with open(image_path, 'rb') as f:
                return HttpResponse(f.read(), content_type='image/png')
        except Exception as e:
            return JsonResponse({'error': 'Could not read image'}, status=500)
