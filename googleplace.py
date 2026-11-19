import aiohttp
import asyncio
import json

API_KEY = ""

async def post(location, radius, maxCount):

    api_key = API_KEY
    url = "https://places.googleapis.com/v1/places:searchNearby"
    my_headers = [
        ('Content-Type', 'application/json'),
        ('X-Goog-Api-Key', api_key),
        ('X-Goog-FieldMask', 'places.name,places.location,places.id,places.rating,places.types')
    ]

    payload = {
        "maxResultCount": maxCount,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": location[0],
                    "longitude": location[1]},
                "radius": radius
            }
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=my_headers) as response:
            response_json = await response.json()
    try:
        places_data = response_json["places"]
    except KeyError:
        places_data = response_json
    pretty_json_string = json.dumps(places_data, indent=4)
    return pretty_json_string


def get_latitude_longitude(input):
    
    try:
        # assumes the first character of input is the sign of latitude
        location = [0,0]
        lat_sign = input[0]
        for k in range (0, len(input) - 1):
            i = k + 1
            if input[i] == '+' or input[i] == '-':
                lon_sign = input[i]
                lon_sign_location = i

        abs_lat = float(input[1:lon_sign_location])
        abs_lon = float(input[(lon_sign_location + 1):])
        if (lat_sign == '+'):
            location[0] = abs_lat
        else:
            location[0] = -abs_lat
        if (lon_sign == '+'):
            location[1] = abs_lon
        else:
            location[1] = -abs_lon
        return location
    
    except Exception as e:
        print(e)


async def request_google_api(location_raw_string, radius, maxCount):
    location = (get_latitude_longitude(location_raw_string))
    radius *= 1000
    result = await post(location, radius, maxCount)
    result += "\n"
    return result

async def testmain():
    result = await request_google_api('+34.063700-118.445400', 1, 3)
    print(result)



