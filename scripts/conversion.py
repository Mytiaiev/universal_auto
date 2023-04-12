import requests
from app.models import RawGPS


def get_location_from_db(car_gps_imei):
    data = RawGPS.objects.filter(imei=car_gps_imei).order_by('-created_at')[:1]
    data = str(data).split(';')
    try:
        latitude, longitude = "{:.6f}".format(float(data[2])), "{:.6f}".format(float(data[2]))
    except:
        pass
    return latitude, longitude

def get_address(latitude, longitude, api_key):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={latitude},{longitude}&language=uk&key={api_key}"
    response = requests.get(url)
    data = response.json()
    if data['status'] == 'OK':
        return data['results'][0]['formatted_address']
    else:
        return None


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
