from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from django.http import FileResponse, Http404
import os
from django.conf import settings

from .models import Country
from .serializers import CountrySerializer
from .utils import refresh_countries_data, generate_summary_image

@api_view(['POST'])
def refresh_countries(request):
    """POST /countries/refresh - Fetch all countries and exchange rates, then cache them in the database"""
    try:
        stats = refresh_countries_data()
        return Response({
            'message': 'Countries data refreshed successfully',
            'stats': stats
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': 'External data source unavailable', 'details': str(e)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

class CountryListView(ListAPIView):
    """GET /countries - Get all countries from the DB (support filters and sorting)"""
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['region', 'currency_code']
    ordering_fields = ['name', 'population', 'estimated_gdp']
    ordering = ['name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        sort = self.request.query_params.get('sort')
        if sort == 'gdp_desc':
            queryset = queryset.exclude(estimated_gdp__isnull=True).order_by('-estimated_gdp')
        elif sort == 'gdp_asc':
            queryset = queryset.exclude(estimated_gdp__isnull=True).order_by('estimated_gdp')
        
        return queryset

@api_view(['GET', 'DELETE'])
def country_by_name(request, name):
    """
    Handle both:
    - GET /countries/:name → Get one country by name
    - DELETE /countries/:name → Delete a country record
    """
    try:
        country = Country.objects.get(name__iexact=name)
    except Country.DoesNotExist:
        return Response(
            {'error': 'Country not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    if request.method == 'GET':
        serializer = CountrySerializer(country)
        return Response(serializer.data)
    
    elif request.method == 'DELETE':
        country.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
def status_view(request):
    """GET /status - Show total countries and last refresh timestamp"""
    total_countries = Country.objects.count()
    
    latest_country = Country.objects.order_by('-last_refreshed_at').first()
    last_refreshed_at = latest_country.last_refreshed_at if latest_country else None
    
    return Response({
        'total_countries': total_countries,
        'last_refreshed_at': last_refreshed_at
    })

@api_view(['GET'])
def countries_image(request):
    """GET /countries/image - Serve the generated summary image"""
    image_path = os.path.join(settings.CACHE_DIR, 'summary.png')
    
    if not os.path.exists(image_path):
        return Response(
            {'error': 'Summary image not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        return FileResponse(
            open(image_path, 'rb'),
            content_type='image/png',
            filename='summary.png'
        )
    except Exception as e:
        return Response(
            {'error': 'Could not serve image', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
