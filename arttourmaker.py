import openrouteservice as ors #for directions
import folium #for map display
import pandas as pd #for data filtering

#step 1: generate original route w/o art pieces!

#set up api, create client object
client = ors.Client(key = "5b3ce3597851110001cf6248f07ac40fcab1455d8cd1f1fb5b342905")

#ask for start and end location inputs (e.g. MIT Stata Center, Cambridge MA; Sever Hall, Cambridge MA)
print("Welcome to the Cambridge Art Tour Generator!\nStart by entering your start and end locations!")
start = input("Start Location:")
end = input("End Location:")

# use ors geocoding
geocode1 = client.pelias_search(text=start)
geocode2 = client.pelias_search(text=end)

if geocode1["features"]:
    start_coords = geocode1["features"][0]["geometry"]["coordinates"]  # ors uses long,lat
    latlon1 = start_coords[::-1]  # folium uses lat, long
    print(f"✅ Coordinates for '{start}': {latlon1}")
if geocode2["features"]:
    end_coords = geocode2["features"][0]["geometry"]["coordinates"] 
    latlon2 = end_coords[::-1]  
    print(f"✅ Coordinates for '{end}': {latlon2}")

#creating lists for folium and ors 
coords=[start_coords,end_coords]
rev_coords = [latlon1, latlon2]

#generating the first route
base_route = client.directions(coordinates = coords, profile = "foot-walking", format = "geojson")

#getting travel time and distance
summary = base_route['features'][0]['properties']['summary']
base_distance = summary['distance'] / 1000  # meters to kilometers
base_duration = summary['duration'] / 60   # seconds to minutes
print(f"Distance: {base_distance:.2f} km")
print(f"Estimated time: {base_duration:.1f} minutes")

#creating map display with folium
m = folium.Map(location = latlon1, tiles = "cartodbpositron", zoom_start=13)

#adding smooth line onto the map
folium.PolyLine(locations = [list(reversed(coord)) for coord in base_route['features'][0]['geometry']['coordinates']], color = "blue").add_to(m)

#adding travel information to the html
popup_text = f"Distance: {base_distance:.2f} km<br>Time: {base_duration:.1f} min"
folium.Marker(location=latlon1, popup="Start").add_to(m)
folium.Marker(location=latlon2, popup=popup_text).add_to(m)

#first map saved to map.html!
m.save("map.html")

#step two: filtering by art tag!
# load CSV with normalized tags
df = pd.read_csv("public_art_cleaned.csv")

# ask user to enter a list of tags and provide an category bank
available_tags = sorted(df["normalized tag"].dropna().unique()) # make a list of all normalized tags
print("Available tags:")
for tag in available_tags:
    print(f" - {tag}")
user_input = input("\nEnter a list of tags (e.g., ['animal', 'history']):\n")

try:
    selected_tags = eval(user_input)
    if not isinstance(selected_tags, list):
        raise ValueError
except Exception:
    print("❌ Invalid input. Please enter a list of tags like ['animal', 'history'].")
    exit()

# normalizing the user input
selected_tags = [tag.lower().strip() for tag in selected_tags]

# filtering by tag and creating new csv file
filtered_df = df[df["normalized tag"].isin(selected_tags)]
output_file = "filtered_art_by_tag.csv"
filtered_df.to_csv(output_file, index=False)

#step three: filtering by time constraint!
from math import radians, cos, sin, asin, sqrt

# defining the haversine formula
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    return R * c

# asking people how much extra time they have
extra_time = input("How many minutes do you have to spare in addition to your original travel time?")

# calculating max time constraint
max_total_time = base_duration + int(extra_time)

included_stops = []        # list of selected stop coordinates
included_titles = []       # list of titles of selected stops
remaining_stops = filtered_df.copy()
total_time = base_duration

while not remaining_stops.empty:
    #using the start point if no stops have been added yet; otherwise, use the last added stop
    current_coords = start_coords if not included_stops else included_stops[-1]

    #calculating haversine distance from current location to each remaining stop
    remaining_stops["dist_to_current"] = remaining_stops.apply(
        lambda row: haversine(current_coords[1], current_coords[0], row["Latitude"], row["Longitude"]), axis=1
    )

    #picking the closest stop to current location
    candidate = remaining_stops.sort_values(by="dist_to_current").iloc[0]
    candidate_coords = [candidate["Longitude"], candidate["Latitude"]]

    #building a proposed route with the new candidate included
    proposed_waypoints = [start_coords] + included_stops + [candidate_coords] + [end_coords]
    proposed_route = client.directions(proposed_waypoints, profile="foot-walking", format="geojson")
    proposed_time = proposed_route['features'][0]['properties']['summary']['duration'] / 60  # in minutes

   #checking if this route is still within the allowed time
    if proposed_time <= max_total_time:
        included_stops.append(candidate_coords)
        included_titles.append(candidate.get("List title"))
        remaining_stops = remaining_stops.drop(candidate.name)
        total_time = proposed_time
    else:
        break

# generating final route with art stops
final_waypoints = [start_coords] + included_stops + [end_coords]
scenic_route = client.directions(final_waypoints, profile="foot-walking", format="geojson")

#generating the new map with folium with markers
m = folium.Map(location=latlon1, tiles="cartodbpositron", zoom_start=14)
folium.GeoJson(scenic_route, name="Scenic Route").add_to(m)
folium.Marker(latlon1, popup="Start", icon=folium.Icon(color="green")).add_to(m)
folium.Marker(latlon2, popup=f"End<br>Total Time: {total_time:.1f} min", icon=folium.Icon(color="red")).add_to(m)

for i, stop in enumerate(included_stops, start=1):
    latlon = stop[::-1]
    folium.Marker(latlon, popup=f"Art Stop #{i}", icon=folium.Icon(color="blue", icon="paint-brush", prefix="fa")).add_to(m)

#saving the new map!!! YAYY!!!
m.save("arttour.html")
print("✅ Scenic route map saved as 'arttour.html'")
print(included_titles)
