import requests
import random
from decimal import Decimal
import os
from django.core.exceptions import ValidationError
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from PIL import Image, ImageDraw, ImageFont
from django.conf import settings
from .models import Country

def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns consistent JSON error responses
    """
    response = exception_handler(exc, context)
    
    if response is not None:
        if response.status_code == status.HTTP_404_NOT_FOUND:
            response.data = {'error': 'Country not found'}
        elif response.status_code == status.HTTP_400_BAD_REQUEST:
            if 'error' not in response.data:
                response.data = {'error': 'Validation failed', 'details': response.data}
        elif response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
            response.data = {'error': 'Internal server error'}
    else:
        if isinstance(exc, ValidationError):
            response = Response(
                {'error': 'Validation failed', 'details': exc.message_dict},
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            response = Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    return response

def fetch_countries_data():
    """Fetch country data from restcountries API"""
    try:
        print("Fetching countries data from REST Countries API...")
        response = requests.get(
            'https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies',
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        print(f"Successfully fetched {len(data)} countries")
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching countries data: {str(e)}")
        raise Exception(f"Could not fetch data from countries API: {str(e)}")

def fetch_exchange_rates():
    """Fetch exchange rates from open.er-api.com"""
    try:
        print("Fetching exchange rates from Open Exchange Rates API...")
        response = requests.get('https://open.er-api.com/v6/latest/USD', timeout=30)
        response.raise_for_status()
        data = response.json()
        if data.get('result') == 'success':
            print("Successfully fetched exchange rates")
            return data['rates']
        else:
            raise Exception("Exchange rate API returned error")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching exchange rates: {str(e)}")
        raise Exception(f"Could not fetch data from exchange rates API: {str(e)}")

def calculate_estimated_gdp(population, exchange_rate):
    """Calculate estimated GDP using EXACT formula: population × random(1000–2000) ÷ exchange_rate"""
    if not exchange_rate or exchange_rate == 0 or not population:
        return None
    
    try:
        random_multiplier = random.randint(1000, 2000)
        gdp = (Decimal(population) * Decimal(random_multiplier)) / Decimal(exchange_rate)
        return gdp.quantize(Decimal('0.01'))
    except:
        return None

def refresh_countries_data():
    """Main function to refresh countries data - FOLLOWING EXACT REQUIREMENTS"""
    print("Starting countries data refresh...")
    
    countries_data = fetch_countries_data()
    exchange_rates = fetch_exchange_rates()
    
    refresh_stats = {
        'updated': 0,
        'created': 0,
        'skipped': 0
    }
    
    for country_data in countries_data:
        try:
            country_name = country_data['name']
            
            # Extract currency code (first currency if available)
            currency_code = None
            currencies = country_data.get('currencies', [])
            
            if currencies and len(currencies) > 0:
                currency_code = currencies[0].get('code')
                print(f"Country {country_name}: currency_code = {currency_code}")
            else:
                currency_code = None
            
            # Get exchange rate based on requirements
            exchange_rate = None
            if currency_code:
                if currency_code in exchange_rates:
                    exchange_rate = Decimal(str(exchange_rates[currency_code]))
                else:
                    exchange_rate = None
            else:
                exchange_rate = None
            
            # Calculate estimated GDP based on EXACT requirements
            estimated_gdp = None
            if currency_code and exchange_rate:
                estimated_gdp = calculate_estimated_gdp(country_data.get('population'), exchange_rate)
            elif not currency_code:
                estimated_gdp = Decimal('0')
            else:
                estimated_gdp = None
            
            # Prepare country data
            country_dict = {
                'capital': country_data.get('capital'),
                'region': country_data.get('region'),
                'population': country_data.get('population', 0),
                'currency_code': currency_code,
                'exchange_rate': exchange_rate,
                'estimated_gdp': estimated_gdp,
                'flag_url': country_data.get('flag'),
            }
            
            if country_dict['population'] is None:
                country_dict['population'] = 0
            
            # Create or update country (case-insensitive name matching)
            existing_country = Country.objects.filter(name__iexact=country_name).first()
            
            if existing_country:
                for key, value in country_dict.items():
                    setattr(existing_country, key, value)
                existing_country.save()
                refresh_stats['updated'] += 1
                print(f"Updated: {country_name}")
            else:
                Country.objects.create(name=country_name, **country_dict)
                refresh_stats['created'] += 1
                print(f"Created: {country_name}")
                
        except Exception as e:
            print(f"Error processing country {country_data.get('name', 'Unknown')}: {str(e)}")
            refresh_stats['skipped'] += 1
            continue
    
    print(f"Refresh completed: {refresh_stats}")
    
    generate_summary_image()
    
    return refresh_stats

def generate_summary_image():
    """Generate summary image with countries data"""
    try:
        print("Generating summary image...")
        total_countries = Country.objects.count()
        top_countries = Country.objects.exclude(estimated_gdp__isnull=True).order_by('-estimated_gdp')[:5]
        
        img_width, img_height = 800, 500
        img = Image.new('RGB', (img_width, img_height), color=(240, 240, 240))
        draw = ImageDraw.Draw(img)
        
        try:
            font_large = ImageFont.truetype("arial.ttf", 28)
            font_medium = ImageFont.truetype("arial.ttf", 20)
            font_small = ImageFont.truetype("arial.ttf", 16)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        draw.rectangle([0, 0, img_width, 60], fill=(70, 130, 180))
        draw.text((20, 20), "COUNTRIES SUMMARY", fill='white', font=font_large)
        
        draw.text((50, 80), f"Total Countries: {total_countries}", fill='black', font=font_medium)
        
        draw.text((50, 120), "Top 5 Countries by Estimated GDP:", fill='black', font=font_medium)
        
        y_position = 160
        for i, country in enumerate(top_countries, 1):
            gdp_str = f"${country.estimated_gdp:,.2f}" if country.estimated_gdp else "N/A"
            text = f"{i}. {country.name}: {gdp_str}"
            draw.text((70, y_position), text, fill='black', font=font_small)
            y_position += 30
        
        from django.utils.timezone import now
        timestamp = now().strftime("%Y-%m-%d %H:%M:%S UTC")
        draw.text((50, 450), f"Last updated: {timestamp}", fill='gray', font=font_small)
        
        draw.rectangle([0, 0, img_width-1, img_height-1], outline='black', width=2)
        
        image_path = os.path.join(settings.CACHE_DIR, 'summary.png')
        img.save(image_path)
        print(f"Summary image saved to: {image_path}")
        
        return image_path
    except Exception as e:
        print(f"Error generating summary image: {str(e)}")
        return None
