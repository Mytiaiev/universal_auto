import requests
import os
import re


def get_address(latitude, longitude, api_key):
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


def geocode(address, api_key):
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


def get_addresses_by_radius(address, center_lat, center_lng, center_radius, api_key):
    """"Returns addresses by pattern {CITY_PARK}"""

    url = f"https://maps.googleapis.com/maps/api/place/autocomplete/json?input={address}&language=uk&" \
        f"location={center_lat},{center_lng}&radius={center_radius}&key={api_key}"

    response = requests.get(url)
    data = response.json()
    city_park = os.environ["CITY_PARK"]
    addresses = []
    pattern = re.compile(rf"\b{city_park}\b", re.IGNORECASE)

    if data['status'] == 'OK':
        results = data['predictions']
        for result in results:
            match = pattern.search(result['description'])
            if match:
                addresses.append(result['description'])
    else:
        return None

    return addresses

