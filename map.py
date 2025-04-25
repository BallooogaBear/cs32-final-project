import openrouteservice  
import folium            

api_key = "5b3ce3597851110001cf6248ad43bca6b7504220ad3d487037a6eb7a"

client = openrouteservice.Client(key=api_key)

start = [-71.1169, 42.3745]   # Sever Hall, Cambridge
end = [-71.1151, 42.3683]     # Leverett House, Cambridge

# Asking ORS for a walking route between these points
route = client.directions(
    coordinates=[start, end],
    profile='foot-walking',
    format='geojson'
)

# Getting the travel time and distance from the route info
summary = route['features'][0]['properties']['summary']
time_minutes = summary['duration'] / 60
distance_km = summary['distance'] / 1000

print("Walking route information:")
print("Time: {:.1f} minutes".format(time_minutes))
print("Distance: {:.2f} kilometers".format(distance_km))

# Creating a map centered between the two points
center_lat = (start[1] + end[1]) / 2
center_lon = (start[0] + end[0]) / 2
my_map = folium.Map(location=[center_lat, center_lon], zoom_start=16)

# Drawing the route and add start/end markers
folium.GeoJson(route).add_to(my_map)
folium.Marker([start[1], start[0]], popup="Start").add_to(my_map)
folium.Marker([end[1], end[0]], popup="End").add_to(my_map)

# Saving the map to an HTML file
my_map.save("simple_route_map.html")
print("Map saved as simple_route_map.html")