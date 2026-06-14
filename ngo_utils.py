import pandas as pd
from geopy.distance import geodesic

def load_ngo_data(file_path='data/ngo_database.csv'):
    """
    Loads the NGO dataset and processes the necessary columns.

    Parameters:
    - file_path: str, path to the CSV file

    Returns:
    - df: DataFrame, processed NGO data
    """
    df = pd.read_csv(file_path)
    df['Latitude'] = df['Latitude'].astype(float)
    df['Longitude'] = df['Longitude'].astype(float)
    df['Services Offered'] = df['Services Offered'].apply(parse_services)
    return df

def parse_services(services_str):
    """
    Parses the 'Services Offered' string into a list of services.

    Parameters:
    - services_str: str, comma-separated services

    Returns:
    - list of services
    """
    return [service.strip() for service in services_str.split(',')]

def add_distance_column(df, user_location):
    """
    Adds a 'distance' column to the DataFrame, calculating the distance from the user's location to each NGO.

    Parameters:
    - df: DataFrame, NGO data
    - user_location: tuple, (latitude, longitude)

    Returns:
    - df: DataFrame, with added 'distance' column
    """
    df['distance'] = df.apply(lambda row: geodesic(user_location, (row['Latitude'], row['Longitude'])).km, axis=1)
    return df

def get_nearby_ngos(df, user_location, radius=7):
    """
    Filters NGOs within a specified radius from the user's location.

    Parameters:
    - df: DataFrame, NGO data
    - user_location: tuple, (latitude, longitude)
    - radius: float, radius in kilometers (default is 7 km)

    Returns:
    - df: DataFrame, filtered NGOs within the radius
    """
    df = add_distance_column(df, user_location)
    return df[df['distance'] <= radius]

def filter_ngos_by_services(df, help_type):
    """
    Filters NGOs based on the help type.

    Parameters:
    - df: DataFrame, NGO data
    - help_type: str, the type of help needed ("Emergency Help", "Legal Help", "Shelter/Emotional Help")

    Returns:
    - df: DataFrame, filtered NGOs based on help type
    - service_keywords: dict, the keywords used for filtering
    """
    service_keywords= {
        "Emergency Help": [
            "Emergency Rescue", "Medical Support", "Temporary shelter",
            "Rescue and Rehabilitation of Women", "Support services for women",
            "Healthcare Programs"
        ],
        "Legal Help": [
            "Legal Aid Cell", "Legal Support for Women", "Free legal aid counseling",
            "Domestic Violence Cases"
        ],
        "Shelter/Emotional Help": [
            "Shelter", "Temporary shelter", "Counseling Center", "Mental Health Counseling",
            "Mental Health Awareness", "Family Counseling", "Support group meetings",
            "Caretaker and Support Services", "Mental Health", "Domestic Violence Support",
            "Community counselor training", "Awareness or Education"
        ]
    }

    # Get the keywords for the selected help type
    keywords = service_keywords.get(help_type, [])

    # Filter the DataFrame based on the keywords
    filtered_df = df[df['Services Offered'].apply(lambda x: any(keyword.lower() in x.lower() for keyword in keywords))]

    return filtered_df, service_keywords
