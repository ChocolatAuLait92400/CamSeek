import json
import logging
import os

def load_cameras(json_file):
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

def save_working_camera(vendor, ip, port, url, user, password, output_file):
    try:
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                working_cameras = json.load(f)
        else:
            working_cameras = []

        if url not in [cam["ip"] for cam in working_cameras]:
            working_cameras.append({
                "productvendor": vendor,
                "ip": ip,
                "port": port,
                "url": url,
                "user": user,
                "password": password
                })

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(working_cameras, f, ensure_ascii=False, indent=4)
        logging.info(f"Caméra fonctionnelle enregistrée: {url}")
    except Exception as e:
        logging.error(f"Erreur lors de l'écriture du fichier {output_file}: {e}")

def save_tested_camera(vendor, ip, port, tested_file):
    try:
        if os.path.exists(tested_file):
            with open(tested_file, 'r', encoding='utf-8') as f:
                tested_cameras = json.load(f)
        else:
            tested_cameras = []

        # Check if the camera with the same URL is already tested
        if ip not in [cam["ip"] for cam in tested_cameras]:
            tested_cameras.append({
                "productvendor": vendor,
                "ip": ip,
                "port": port
            })

        with open(tested_file, 'w', encoding='utf-8') as f:
            json.dump(tested_cameras, f, ensure_ascii=False, indent=4)
        logging.info(f"Caméra testée enregistrée: {ip}")
    except Exception as e:
        logging.error(f"Erreur lors de l'écriture du fichier {tested_file}: {e}")

def load_tested_cameras(tested_file):
    try:
        if os.path.exists(tested_file):
            with open(tested_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        logging.error(f"Erreur lors de la lecture du fichier {tested_file}: {e}")
        return []
