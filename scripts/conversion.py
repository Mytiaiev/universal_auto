import requests
import os


def get_address(latitude, longitude, api_key):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={latitude},{longitude}&language=uk&key={api_key}"
    response = requests.get(url)
    data = response.json()
    if data['status'] == 'OK':
        return data['results'][0]['formatted_address']
    else:
        return None


def get_route_distance(from_lat, from_lng, to_lat, to_lng, driv_lat, driv_lng, api_key):
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={driv_lat},{driv_lng}&destination={to_lat},{to_lng}&waypoints=via:{from_lat},{from_lng}&mode=driving&key={api_key}"
    response = requests.get(url)
    data = response.json()
    if data['status'] == 'OK':
        distance_meters = data["routes"][0]["legs"][0]["distance"]["value"]
        distance_km = distance_meters / 1000
        return distance_km
    else:
        return None

