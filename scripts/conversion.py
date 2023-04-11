import requests
import os


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

