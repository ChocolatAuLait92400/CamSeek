import logging
import requests
from requests.auth import HTTPBasicAuth
from .file_utils import save_working_camera, save_tested_camera

def test_camera_connection(vendor, ip, port, output_file, tested_file):
    logging.info(f"Test de connexion à {ip}")
    ip = ip.replace("http://", "").replace("https://", "")
    url = f"http://{ip}:{port}"

    video_endpoints = [
        '/axis-cgi/mjpg/video.cgi'
    ]

    camera_found = False
    passwords_found = []

    credentials = [
        HTTPBasicAuth('root', 'pass'),
        HTTPBasicAuth('admin', 'admin')
    ]

    for endpoint in video_endpoints:
        full_url = url.rstrip('/') + endpoint
        print(full_url)
        try:
            response = requests.get(full_url, timeout=5, stream=True)
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'image/jpeg' in content_type or 'multipart/x-mixed-replace' in content_type:
                    logging.info(f"[SUCCÈS] Flux vidéo accessible sans mot de passe à {full_url}")
                    save_working_camera(vendor, ip, port, full_url, None, None, output_file)
                    camera_found = True
                    break
            elif response.status_code == 401:
                for auth in credentials:
                    try:
                        auth_response = requests.get(full_url, timeout=5, stream=True, auth=auth)
                        if auth_response.status_code == 200:
                            logging.info(f"[SUCCÈS] Accès avec authentification {auth.username}:{auth.password}")
                            save_working_camera(vendor, ip, port, full_url, auth.username, auth.password, output_file)
                            passwords_found.append(f"{auth.username}:{auth.password}")
                            camera_found = True
                            break
                    except requests.RequestException:
                        pass
        except requests.RequestException as e:
            logging.error(f"Erreur lors de la connexion à {full_url} : {e}")

    save_tested_camera(vendor, ip, port, tested_file)

    return [camera_found, passwords_found]
