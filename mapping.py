import folium


def plot_coordinates_on_map(coordinates, start_zoom=5):
    """
    Plot a list of (latitude, longitude) tuples on a map and return the HTML to display it.

    Parameters:
    - coordinates: List of (latitude, longitude) tuples

    Returns:
    - HTML string to display the map
    """

    # Check if there are any coordinates to plot
    if not coordinates:
        return "No coordinates provided."

    # Create a map object and set the location to the first set of coordinates
    map_center = coordinates[0]
    map_obj = folium.Map(
        location=map_center,
        zoom_start=start_zoom,
        tiles='https://api.maptiler.com/maps/streets/{z}/{x}/{y}.png?key=T7oylVccpKp3wwJCxmkp',
        # Example for MapTiler tiles in English
        attr='Map data © OpenStreetMap contributors'
    )

    # Add markers for each coordinate
    for coord in coordinates:
        folium.Marker(coord).add_to(map_obj)

    # Return HTML representation of the map
    return map_obj._repr_html_()


def save_map_as_html(html_map, file_name='map.html'):
    with open(file_name, 'w') as f:
        f.write(html_map)

# Example Usage
coords = [(35.6895, 139.6917), (34.0522, -118.2437), (51.5074, -0.1278)]  # Replace with your coordinates
html_map = plot_coordinates_on_map(coords)

save_map_as_html(html_map, 'my_map.html')
