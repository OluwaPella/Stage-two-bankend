import requests
import random
from django.utils import timezone
from .models import Country, RefreshLog

def fetch_countries_data():
    """Fetch country data from restcountries API"""
    url = "https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise Exception(f"Could not fetch data from Countries API: {str(e)}")

def fetch_exchange_rates():
    """Fetch exchange rates from open.er-api.com"""
    url = "https://open.er-api.com/v6/latest/USD"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        if data.get('result') == 'success':
            return data['rates']
        else:
            raise Exception("Exchange rate API returned error")
    except requests.RequestException as e:
        raise Exception(f"Could not fetch data from Exchange Rates API: {str(e)}")

def calculate_estimated_gdp(population, exchange_rate):
    """Calculate estimated GDP using random multiplier"""
    if not exchange_rate:
        return 0  # Set to 0 as per requirements
    
    random_multiplier = random.randint(1000, 2000)
    return (population * random_multiplier) / exchange_rate

def refresh_countries_data():
    """Main function to refresh all countries data"""
    # Fetch external data
    countries_data = fetch_countries_data()
    exchange_rates = fetch_exchange_rates()
    
    updated_count = 0
    created_count = 0
    
    for country_data in countries_data:
        # Extract currency code (take first one if multiple)
        currency_code = None
        currencies = country_data.get('currencies', [])
        if currencies and len(currencies) > 0:
            currency_code = currencies[0].get('code')
        
        # Get exchange rate
        exchange_rate = None
        if currency_code and currency_code in exchange_rates:
            exchange_rate = exchange_rates[currency_code]
        
        # Calculate estimated GDP
        estimated_gdp = calculate_estimated_gdp(
            country_data.get('population', 0), 
            exchange_rate
        )
        
        # Prepare country data
        country_fields = {
            'capital': country_data.get('capital', ''),
            'region': country_data.get('region', ''),
            'population': country_data.get('population', 0),
            'currency_code': currency_code,
            'exchange_rate': exchange_rate,
            'estimated_gdp': estimated_gdp,
            'flag_url': country_data.get('flag', '')
        }
        
        # Update or create country
        country, created = Country.objects.update_or_create(
            name=country_data['name'],
            defaults=country_fields
        )
        
        if created:
            created_count += 1
        else:
            updated_count += 1
    
    # Log the refresh
    total_countries = Country.objects.count()
    RefreshLog.objects.create(total_countries=total_countries)
    
    return {
        'total_countries': total_countries,
        'created': created_count,
        'updated': updated_count
    }
def generate_summary_image():
    """Generate summary image with country data - simplified version without Pillow"""
    import os
    from django.conf import settings
    
    # Create cache directory if it doesn't exist
    cache_dir = os.path.join(settings.BASE_DIR, 'cache')
    os.makedirs(cache_dir, exist_ok=True)
    
    image_path = os.path.join(cache_dir, 'summary.png')
    
    try:
        # Try to use Pillow if available
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a simple image
        img = Image.new('RGB', (600, 400), color='white')
        draw = ImageDraw.Draw(img)
        
        # Get data
        total_countries = Country.objects.count()
        top_countries = Country.objects.exclude(estimated_gdp__isnull=True).order_by('-estimated_gdp')[:5]
        latest_refresh = RefreshLog.objects.first()
        
        # Use default font
        try:
            font = ImageFont.load_default()
        except:
            font = None
        
        y_position = 20
        draw.text((20, y_position), f"Total Countries: {total_countries}", fill='black', font=font)
        y_position += 30
        draw.text((20, y_position), "Top 5 Countries by GDP:", fill='black', font=font)
        y_position += 30
        
        for i, country in enumerate(top_countries, 1):
            gdp_text = f"{country.estimated_gdp:,.2f}" if country.estimated_gdp else "N/A"
            text = f"{i}. {country.name}: ${gdp_text}"
            draw.text((40, y_position), text, fill='black', font=font)
            y_position += 25
        
        if latest_refresh:
            y_position += 20
            refresh_text = f"Last Refresh: {latest_refresh.refreshed_at.strftime('%Y-%m-%d %H:%M:%S')}"
            draw.text((20, y_position), refresh_text, fill='black', font=font)
        
        img.save(image_path)
        return True
        
    except ImportError:
        # Pillow not available - create a simple text file instead
        with open(image_path.replace('.png', '.txt'), 'w') as f:
            f.write("Country API Summary\n")
            f.write("===================\n")
            f.write(f"Total Countries: {Country.objects.count()}\n\n")
            f.write("Top 5 Countries by GDP:\n")
            for i, country in enumerate(Country.objects.exclude(estimated_gdp__isnull=True).order_by('-estimated_gdp')[:5], 1):
                gdp_text = f"{country.estimated_gdp:,.2f}" if country.estimated_gdp else "N/A"
                f.write(f"{i}. {country.name}: ${gdp_text}\n")
        
        # Create a placeholder PNG file
        try:
            # Create a very basic image using alternative methods if possible
            pass
        except:
            pass
            
        return False
