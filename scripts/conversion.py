import requests
import os


def convertion(coordinates: str):
    # ex from (5045.4321 or 05045.4321) to 50.123456
    flag = False
    if coordinates[0] == '-':
        coordinates = coordinates[1:]
        flag = True
    if len(coordinates) == 9:
        index = 2
    elif len(coordinates) == 10:
        index = 3

    degrees, minutes = coordinates[:index], coordinates[index:]
    result = float(degrees) + float(minutes)/60
    result = round(result, 6)
    if flag:
        result = float(f'-{str(result)}')

    return result


def get_address(latitude, longitude, api_key):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={latitude},{longitude}&language=uk&key={api_key}"
    response = requests.get(url)
    data = response.json()
    if data['status'] == 'OK':
        return data['results'][0]['formatted_address']
    else:
        return None

