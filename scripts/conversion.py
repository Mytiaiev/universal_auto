import requests
from app.models import VehicleGPS, ParkSettings
import re
from shapely.geometry import Point, Polygon, LineString, MultiLineString
from shapely.ops import split
import os
from math import radians, sin, cos, sqrt, atan2


def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of the Earth in kilometers
    dLat = radians(lat2 - lat1)
    dLon = radians(lon2 - lon1)
    lat1 = radians(lat1)
    lat2 = radians(lat2)

    a = sin(dLat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dLon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


city_boundaries = Polygon([(50.482433, 30.758250), (50.491685, 30.742045), (50.517374, 30.753721),
                           (50.529704, 30.795370), (50.537806, 30.824810), (50.557504, 30.816837),
                           (50.579778, 30.783808), (50.583684, 30.766494), (50.590833, 30.717995),
                           (50.585827, 30.721184), (50.575221, 30.709590), (50.555702, 30.713665),
                           (50.534572, 30.653589), (50.572107, 30.472565), (50.571557, 30.464734),
                           (50.584574, 30.464120), (50.586367, 30.373054), (50.573406, 30.373049),
                           (50.570661, 30.307423), (50.557272, 30.342127), (50.554324, 30.298128),
                           (50.533394, 30.302445), (50.423057, 30.244148), (50.446055, 30.348753),
                           (50.381271, 30.442675), (50.372075, 30.430830), (50.356963, 30.438040),
                           (50.360358, 30.468252), (50.333520, 30.475291), (50.302393, 30.532814),
                           (50.213270, 30.593929), (50.226755, 30.642478), (50.291609, 30.590369),
                           (50.335279, 30.628839), (50.389522, 30.775925), (50.394966, 30.776293),
                           (50.397798, 30.790669), (50.392594, 30.806395), (50.404878, 30.825881),
                           (50.458385, 30.742751), (50.481657, 30.748158), (50.482454, 30.758345)])


def get_route_price(from_lat, from_lng, to_lat, to_lng, driver_lat, driver_lng, api_key):
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={driver_lat},{driver_lng}&" \
          f"destination={to_lat},{to_lng}&waypoints={from_lat},{from_lng}|{to_lat},{to_lng}&mode=driving&key={api_key}"
    response = requests.get(url)
    data = response.json()
    if data['status'] == 'OK':
        legs = [] # Ride to client(within,outside) and with client(within,outside)
        points = data["routes"][0]["legs"]
        ride_to_client = points[0]["distance"]["value"] / 1000
        for route in data["routes"]:
            for leg in route["legs"]:
                distance_within_city = 0
                distance_outside_city = 0
                for step in leg["steps"]:
                    start_location = Point(step["start_location"]["lat"], step["start_location"]["lng"])
                    end_location = Point(step["end_location"]["lat"], step["end_location"]["lng"])
                    step_distance = step["distance"]["value"]/1000
                    # Check if the step intersects the city boundaries
                    if city_boundaries.intersects(start_location.buffer(0.000001)) or city_boundaries.intersects(
                            end_location.buffer(0.000001)):
                        line = LineString([start_location, end_location])
                        intersection = split(line, city_boundaries)
                        lines = [i for i in intersection.geoms]
                        start = lines[0].coords[:][0]
                        bound = lines[0].coords[:][1]
                        # Check if step intersect boundary of city and calc distance
                        if not city_boundaries.intersects(start_location.buffer(0.000001)):
                            distance_outside_city += haversine(*start, *bound)
                            distance_within_city += step_distance - haversine(*start, *bound)
                        elif not city_boundaries.intersects(end_location.buffer(0.000001)):
                            distance_within_city += haversine(*start, *bound)
                            distance_outside_city += step_distance - haversine(*start, *bound)
                        else:
                            distance_within_city += step_distance
                    else:
                        # Calculate the distance outside the city
                        distance_outside_city += step_distance
                legs.append((distance_within_city, distance_outside_city))
        if ride_to_client > int(ParkSettings.get_value("FREE_CAR_SENDING_DISTANCE")):
            sending_price = (legs[0][0] - int(ParkSettings.get_value("FREE_CAR_SENDING_DISTANCE"))) * \
                            int(ParkSettings.get_value("TARIFF_CAR_DISPATCH")) + \
                            legs[0][1] * int(ParkSettings.get_value("TARIFF_CAR_OUTSIDE_DISPATCH", 15))
        else:
            sending_price = 0
        price = sending_price + legs[1][0] * int(ParkSettings.get_value("TARIFF_IN_THE_CITY")) + legs[1][1] * int(ParkSettings.get_value("TARIFF_OUTSIDE_THE_CITY"))

        return int(price)


def get_location_from_db(licence_plate):
    gps = VehicleGPS.objects.filter(vehicle=licence_plate).first()
    latitude, longitude = str(gps.lat), str(gps.lon)
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


def geocode(place_id, api_key) -> tuple or None:
    """
    Returns lat, lon address using Google Places API
    """

    url = f"https://maps.googleapis.com/maps/api/place/details/json?placeid={place_id}&language=uk&key={api_key}"
    response = requests.get(url).json()

    if response['status'] == 'OK':
        result = response['result']
        latitude = result['geometry']['location']['lat']
        longitude = result['geometry']['location']['lng']
        return str(latitude)[:10], str(longitude)[:10]
    else:
        return None


def get_addresses_by_radius(address, center_lat, center_lng, center_radius: int, api_key) -> list or None:
    """"Returns addresses by pattern {CITY_PARK} """

    url = f"https://maps.googleapis.com/maps/api/place/autocomplete/json?input={address}&language=uk&" \
        f"location={center_lat},{center_lng}&radius={center_radius}&key={api_key}"

    response = requests.get(url)
    data = response.json()
    city_park = f"{ParkSettings.get_value('CITY_PARK')}"
    addresses = {}
    pattern = re.compile(rf".*({city_park}).*", re.IGNORECASE)

    if data['status'] == 'OK':
        results = data['predictions']
        for result in results:
            match = pattern.search(result['description'])
            if match:
                addresses.update({result['description']: result['place_id']})
    else:
        return None

    return addresses