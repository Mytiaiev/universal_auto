import requests
from app.models import RawGPS
import os
import re


def get_location_from_db(car_gps_imei):
    data = RawGPS.objects.filter(imei=car_gps_imei).order_by('-created_at')[:1]
    data = str(data).split(';')
    try:
        latitude, longitude = "{:.6f}".format(float(data[2])), "{:.6f}".format(float(data[2]))
    except:
        pass
    return latitude, longitude

def get_address(latitude, longitude, api_key) -> str or None:
    """
        Returns address using Google Geocoding API
    """
    # URL for request to API
    url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={latitude},{longitude}&language=uk&key={api_key}"
    response = requests.get(url)
    data = response.json()
    # Checking for results and address
    if data['status'] == 'OK':
        return data['results'][0]['formatted_address']
    else:
        return None


def geocode(address, api_key) -> tuple or None:
    """
    Returns lat, lon address using Google Geocoding API
    """
    # URL for request to API
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}"

    # Sending request and get response
    response = requests.get(url).json()

    # Checking for results and coordinates
    if response['status'] == 'OK':
        result = response['results'][0]
        latitude = result['geometry']['location']['lat']
        longitude = result['geometry']['location']['lng']
        return latitude, longitude
    else:
        return None


def get_addresses_by_radius(address, center_lat, center_lng, center_radius: int, api_key) -> list or None:
    """"Returns addresses by pattern {CITY_PARK} """

    url = f"https://maps.googleapis.com/maps/api/place/autocomplete/json?input={address}&language=uk&" \
        f"location={center_lat},{center_lng}&radius={center_radius}&key={api_key}"

    response = requests.get(url)
    data = response.json()
    city_park = f"{ParkSettings.get_value('CITY_PARK')}"
    addresses = []
    pattern = re.compile(rf".*({city_park}).*", re.IGNORECASE)

    if data['status'] == 'OK':
        results = data['predictions']
        for result in results:
            match = pattern.search(result['description'])
            if match:
                addresses.append(result['description'])
    else:
        return None

    return addresses


def get_route_distance(from_lat, from_lng, to_lat, to_lng, driver_lat, driver_lng, api_key):
    url = f"""
    https://maps.googleapis.com/maps/api/directions/json?
    origin={driver_lat},{driver_lng}&
    destination={to_lat},{to_lng}&
    waypoints=via:{from_lat},{from_lng}&mode=driving&key={api_key}"""
    response = requests.get(url)
    data = response.json()
    if data['status'] == 'OK':
        distance_meters = data["routes"][0]["legs"][0]["distance"]["value"]
        distance_km = distance_meters / 1000
        return distance_km
    else:
        return None
