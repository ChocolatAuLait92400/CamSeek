import json
import requests
import time

# Charger le fichier JSON avec les URLs des caméras
with open('working_cameras.json', 'r') as file:
    camera_urls = json.load(file)

camera_data = []

for index, url in enumerate(camera_urls):
    # Extraire l'adresse IP de l'URL
    ip = url.split('/')[2].split(':')[0]
    print(f"Traitement de l'IP ({index + 1}/{len(camera_urls)}): {ip}")
    
    while True:
        # Faire la requête à ip-api.com
        try:
            response = requests.get(f'http://ip-api.com/json/{ip}')
        except requests.exceptions.RequestException as e:
            print(f"Erreur de requête pour l'IP {ip}: {e}")
            break  # Passer à l'IP suivante

        # Obtenir les en-têtes de limite de débit
        x_rl = response.headers.get('X-Rl')
        x_ttl = response.headers.get('X-Ttl')
        remaining_requests = int(x_rl) if x_rl is not None else None
        wait_time = int(x_ttl) if x_ttl is not None else None

        # Gérer la limitation de débit
        if remaining_requests == 0:
            if wait_time is not None:
                print(f"Limite de requêtes atteinte. Attente de {wait_time} secondes.")
                time.sleep(wait_time)
                continue  # Réessayer après l'attente
            else:
                print("Limite de requêtes atteinte mais pas d'en-tête 'X-Ttl' trouvé. Attente de 60 secondes.")
                time.sleep(60)
                continue  # Réessayer après l'attente

        # Vérifier le code d'état HTTP 429
        if response.status_code == 429:
            if wait_time is not None:
                print(f"HTTP 429 Trop de requêtes. Attente de {wait_time} secondes.")
                time.sleep(wait_time)
                continue  # Réessayer après l'attente
            else:
                print("HTTP 429 reçu mais pas d'en-tête 'X-Ttl' trouvé. Attente de 60 secondes.")
                time.sleep(60)
                continue  # Réessayer après l'attente

        # Traiter la réponse
        data = response.json()
        if data['status'] == 'success':
            camera_info = {
                'ip': ip,
                'lat': data['lat'],
                'lon': data['lon'],
                'url': url  # Inclure l'URL de la caméra
            }
            camera_data.append(camera_info)
        else:
            print(f"Échec de l'obtention des données pour l'IP {ip}: {data.get('message', 'Pas de message d\'erreur')}")
        break  # Sortir de la boucle while et passer à l'IP suivante
    
    # Optionnel : Attendre brièvement pour éviter de dépasser la limite de débit prématurément
    time.sleep(1)

# Générer le fichier HTML avec la carte
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
        /* Style pour la légende */
        .legend {{
            background: white;
            padding: 10px;
            line-height: 1.5em;
            border-radius: 5px;
            box-shadow: 0 0 15px rgba(0,0,0,0.2);
        }}
        .leaflet-control-geocoder-icon {{
            background-image: url('https://unpkg.com/leaflet-control-geocoder@1.13.0/dist/images/geocoder.png');
            background-size: 20px 20px;
        }}
    </style>
    <!-- Charger les CSS de Leaflet et des plugins -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster/dist/MarkerCluster.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster/dist/MarkerCluster.Default.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.css" />
</head>
<body>
    <div id="mapid"></div>
    <!-- Charger les JS de Leaflet et des plugins -->
    <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
    <script src="https://unpkg.com/leaflet.markercluster/dist/leaflet.markercluster-src.js"></script>
    <script src="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.js"></script>
    <script>
        // Initialiser la carte
        var map = L.map('mapid');

        // Définir le fond de carte avec un style différent
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            maxZoom: 19,
            attribution: '© OpenStreetMap'
        }}).addTo(map);

        // Ajouter la barre de recherche
        L.Control.geocoder().addTo(map);

        // Définir une icône personnalisée pour les caméras
        var cameraIcon = L.icon({{
            iconUrl: 'https://icons.iconarchive.com/icons/iconarchive/outline-camera/256/Flat-Blue-Smooth-Camera-icon.png', // URL vers une icône de caméra
            iconSize: [30, 30],
            iconAnchor: [15, 30],
            popupAnchor: [0, -30]
        }});

        // Créer un groupe de clusters
        var markers = L.markerClusterGroup();

        // Ajouter les marqueurs des caméras
"""

for camera in camera_data:
    # Échapper l'URL et l'IP pour éviter les attaques XSS
    escaped_url = camera['url'].replace('"', '&quot;')
    escaped_ip = camera['ip'].replace('"', '&quot;')
    html_content += f"""
        var marker = L.marker([{camera['lat']}, {camera['lon']}], {{icon: cameraIcon}})
            .bindPopup(`
                <div style="text-align:center;">
                    <h3>Caméra IP</h3>
                    <p><b>Adresse :</b> {escaped_ip}</p>
                    <a href="{escaped_url}" target="_blank">🔗 Voir la caméra</a>
                </div>
            `);
        markers.addLayer(marker);
    """

html_content += """
        // Ajouter le groupe de clusters à la carte
        map.addLayer(markers);

        // Ajuster la vue de la carte pour contenir tous les marqueurs
        if (markers.getLayers().length > 0) {
            map.fitBounds(markers.getBounds());
        } else {
            map.setView([0, 0], 2); // Vue par défaut si aucun marqueur
        }

        // Ajouter une légende
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

# Sauvegarder le contenu HTML dans un fichier
with open('camera_map.html', 'w', encoding='utf-8') as file:
    file.write(html_content)

print("La carte HTML a été générée sous le nom 'camera_map.html'")
