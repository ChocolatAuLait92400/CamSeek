from urllib.parse import urlparse
import logging

def extract_ip_from_url(url):
    try:
        parsed_url = urlparse(url)
        return parsed_url.hostname
    except Exception as e:
        logging.error(f"Erreur lors de l'extraction de l'IP depuis l'URL {url}: {e}")
        return None

def get_neighboring_ips(ip):
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
