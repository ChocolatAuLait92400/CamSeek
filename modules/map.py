import json
import requests
import time

def generate_map(camera_file, output_html_file):
    """
    Generate an HTML map of IP cameras using their geolocation.

    Args:
        camera_file (str): Path to the JSON file containing camera information.
        output_html_file (str): Path to save the generated HTML file.
    """
    # Load the JSON file with camera data
    with open(camera_file, 'r', encoding='utf-8') as file:
        cameras = json.load(file)

    camera_data = []

    for index, camera in enumerate(cameras):
        # Extract all the fields from the camera object
        productvendor = camera.get("productvendor")
        ip = camera.get("ip")
        port = camera.get("port")
        url = camera.get("url")
        user = camera.get("user")
        password = camera.get("password")
        print(f"Processing IP ({index + 1}/{len(cameras)}): {ip}")

        while True:
            try:
                # Make a request to ip-api.com
                response = requests.get(f'http://ip-api.com/json/{ip}')
            except requests.exceptions.RequestException as e:
                print(f"Request error for IP {ip}: {e}")
                break

            # Get rate limit headers
            x_rl = response.headers.get('X-Rl')
            x_ttl = response.headers.get('X-Ttl')
            remaining_requests = int(x_rl) if x_rl is not None else None
            wait_time = int(x_ttl) if x_ttl is not None else None

            # Handle rate limiting
            if remaining_requests == 0:
                if wait_time is not None:
                    print(f"Rate limit reached. Waiting for {wait_time} seconds.")
                    time.sleep(wait_time)
                    continue
                else:
                    print("Rate limit reached but no 'X-Ttl' header found. Waiting for 60 seconds.")
                    time.sleep(60)
                    continue

            # Handle HTTP 429 (Too Many Requests)
            if response.status_code == 429:
                if wait_time is not None:
                    print(f"HTTP 429 Too Many Requests. Waiting for {wait_time} seconds.")
                    time.sleep(wait_time)
                    continue
                else:
                    print("HTTP 429 received but no 'X-Ttl' header found. Waiting for 60 seconds.")
                    time.sleep(60)
                    continue

            # Process the response
            data = response.json()
            if data['status'] == 'success':
                camera_info = {
                    'productvendor': productvendor,
                    'ip': ip,
                    'port': port,
                    'user': user,
                    'password': password,
                    'lat': data['lat'],
                    'lon': data['lon'],
                    'url': url
                }
                camera_data.append(camera_info)
            else:
                print(f"Failed to retrieve data for IP {ip}: {data.get('message', 'No error message')}")
            break  # Exit the while loop and proceed to the next IP

        # Optional: Wait briefly to avoid exceeding rate limits
        time.sleep(1)

    # Generate the HTML map
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Carte des Caméras IP</title>
        <meta charset="utf-8" />
        <style>
            html, body {{
                height: 100%;
                margin: 0;
            }}
            #mapid {{
                height: 100%;
                width: 100%;
            }}
            .legend {{
                background: white;
                padding: 10px;
                line-height: 1.5em;
                border-radius: 5px;
                box-shadow: 0 0 15px rgba(0,0,0,0.2);
            }}
        </style>
        <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
        <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster/dist/MarkerCluster.css" />
        <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster/dist/MarkerCluster.Default.css" />
        <link rel="stylesheet" href="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.css" />
    </head>
    <body>
        <div id="mapid"></div>
        <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
        <script src="https://unpkg.com/leaflet.markercluster/dist/leaflet.markercluster-src.js"></script>
        <script src="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.js"></script>
        <script>
            var map = L.map('mapid');
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                maxZoom: 19,
                attribution: '© OpenStreetMap'
            }}).addTo(map);
            L.Control.geocoder().addTo(map);
            var cameraIcon = L.icon({{
                iconUrl: 'https://icons.iconarchive.com/icons/iconarchive/outline-camera/256/Flat-Blue-Smooth-Camera-icon.png',
                iconSize: [30, 30],
                iconAnchor: [15, 30],
                popupAnchor: [0, -30]
            }});
            var markers = L.markerClusterGroup();
    """

    for camera in camera_data:
        escaped_productvendor = camera['productvendor'].replace('"', '&quot;') if camera['productvendor'] else 'Unknown'
        escaped_ip = camera['ip'].replace('"', '&quot;') if camera['ip'] else 'Unknown'
        escaped_port = str(camera['port']).replace('"', '&quot;') if camera['port'] else 'Unknown'
        escaped_url = camera['url'].replace('"', '&quot;') if camera['url'] else '#'
        escaped_user = camera['user'].replace('"', '&quot;') if camera['user'] else 'None'
        escaped_password = camera['password'].replace('"', '&quot;') if camera['password'] else 'None'

        # Create the popup content
        popup_content = f"""
            <div style="text-align:center;">
                <h3>Caméra IP</h3>
                <p><b>Adresse :</b> {escaped_ip}:{escaped_port}</p>
                <p><b>Product Vendor:</b> {escaped_productvendor}</p>
        """

        if camera['user']:
            popup_content += f"<p><b>User:</b> {escaped_user}</p>"
        if camera['password']:
            popup_content += f"<p><b>Password:</b> {escaped_password}</p>"

        popup_content += f'<a href="{escaped_url}" target="_blank">🔗 Voir la caméra</a></div>'

        # Add the marker to the map
        html_content += f"""
            var marker = L.marker([{camera['lat']}, {camera['lon']}], {{icon: cameraIcon}})
                .bindPopup(`{popup_content}`);
            markers.addLayer(marker);
        """

    html_content += """
            map.addLayer(markers);
            if (markers.getLayers().length > 0) {
                map.fitBounds(markers.getBounds());
            } else {
                map.setView([0, 0], 2);
            }
            var legend = L.control({position: 'bottomright'});
            legend.onAdd = function (map) {
                var div = L.DomUtil.create('div', 'legend');
                div.innerHTML += '<img src="https://icons.iconarchive.com/icons/iconarchive/outline-camera/256/Flat-Blue-Smooth-Camera-icon.png" width="20"> Caméra IP';
                return div;
            };
            legend.addTo(map);
        </script>
    </body>
    </html>
    """

    with open(output_html_file, 'w', encoding='utf-8') as file:
        file.write(html_content)

    print(f"The HTML map has been generated and saved to '{output_html_file}'")

if __name__=="__main__":
    generate_map("../data/working_cameras.json", "../map/camera_map.html")
