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


def reverse_geocode(latitude, longitude):
    # Did the geocoding request comes from a device with a
    # location sensor? Must be either true or false
    sensor = 'true'

    # Hit Google's reverse geocoder directly
    # NOTE: I *think* their terms state that you're supposed to
    # use google maps if you use their api for anything.
    base = "https://maps.googleapis.com/maps/api/geocode/json?"
    params = "latlng={lat},{lon}&sensor={sen}&key={key}".format(
        lat=latitude,
        lon=longitude,
        sen=sensor,
        key=os.environ["GOOGLE_API_KEY"]
    )
    url = "{base}{params}".format(base=base, params=params)
    print(url)
    response = requests.get(url).json()
    address = response['results'][0]['formatted_address']
    return address