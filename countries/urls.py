from django.urls import path
from . import views

urlpatterns = [
    # EXACT endpoints as specified in requirements
    path('refresh', views.refresh_countries, name='refresh-countries'),  # POST /countries/refresh
    path('', views.CountryListView.as_view(), name='country-list'),      # GET /countries
    path('image', views.countries_image, name='countries-image'),        # GET /countries/image
    path('<str:name>', views.country_by_name, name='country-detail'),    # GET/DELETE /countries/:name
]
