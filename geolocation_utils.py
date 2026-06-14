import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

def get_user_location():
    """
    Gets the user's location based on their IP address using the ipinfo.io service.

    Returns:
    - tuple: (latitude, longitude) if successful, otherwise (None, None)
    """
    try:
        response = requests.get("https://ipinfo.io/json")
        response.raise_for_status()
        data = response.json()
        loc = data.get("loc", "").split(",")
        if len(loc) == 2:
            lat, lon = float(loc[0]), float(loc[1])
            return lat, lon
        else:
            print("Error: Invalid location data received.")
            return None, None
    except requests.RequestException as e:
        print("Error getting location from IP:", e)
        return None, None

def reverse_geocode(lat, lon):
    """
    Reverse geocodes the given latitude and longitude to get the address.

    Parameters:
    - lat: float, latitude
    - lon: float, longitude

    Returns:
    - str: Address if successful, otherwise "Unknown location"
    """
    try:
        geolocator = Nominatim(user_agent="rakshadeep_geo")
        location = geolocator.reverse((lat, lon), exactly_one=True, timeout=10)
        return location.address if location else "Unknown location"
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        print("Reverse geocoding failed:", e)
        return "Unknown location"
    except Exception as e:
        print("Unexpected error in reverse geocoding:", e)
        return "Unknown location"
