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