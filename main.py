import os
import json
from collections import deque
import modules.camera_logger as camera_logger
from modules.file_utils import load_cameras, load_tested_cameras
from modules.ip_utils import extract_ip_from_url, get_neighboring_ips
from modules.camera_tester import test_camera_connection
from modules.map import generate_map

def generate_camera_key(camera):
    """
    Generates a consistent JSON key for a camera dictionary.
    This is used to identify cameras uniquely and avoid duplicates.
    """
    return json.dumps(camera, sort_keys=True)


def add_to_queue(camera, queue, tested_keys, existing_keys):
    """
    Adds a camera to the processing queue if it's not already tested or in the queue.
    """
    cam_key = generate_camera_key(camera)
    if cam_key not in tested_keys and cam_key not in existing_keys:
        queue.append(camera)
        existing_keys.add(cam_key)


def process_camera_queue(cams_queue, tested_keys, tested_cameras, output_file, tested_file):
    """
    Processes the camera queue, testing each camera and adding neighbors of valid ones to the queue.
    """
    existing_keys = {generate_camera_key(cam) for cam in cams_queue}

    while cams_queue:
        working_cam = cams_queue.popleft()
        cam_key = generate_camera_key(working_cam)

        # Skip if already tested
        if cam_key in tested_keys:
            continue

        # Test the camera
        is_valid = test_camera_connection(
            working_cam["productvendor"],
            working_cam["ip"],
            working_cam["port"],
            output_file,
            tested_file
        )[0]

        # Mark the camera as tested
        tested_keys.add(cam_key)
        tested_cameras.append(working_cam)

        if is_valid:
            # Add neighbors of valid cameras to the queue
            neighbors = get_neighboring_ips(working_cam["ip"])
            for neighbor_ip in neighbors:
                neighbor_cam = {
                    "ip": neighbor_ip,
                    "port": working_cam["port"],
                    "productvendor": working_cam["productvendor"]
                }
                add_to_queue(neighbor_cam, cams_queue, tested_keys, existing_keys)


def main():
    # Define file paths
    base_dir = os.path.dirname(__file__)
    json_file = os.path.join(base_dir, 'data/cameras.json')
    output_file = os.path.join(base_dir, 'data/working_cameras.json')
    tested_file = os.path.join(base_dir, 'data/tested_cameras.json')

    # Load cameras and tested cameras
    cameras = load_cameras(json_file)

    # Load tested cameras as a set of JSON strings
    tested_cameras = load_tested_cameras(tested_file)
    tested_keys = {generate_camera_key(c) for c in tested_cameras}

    # Load working cameras if output_file exists
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            working_cameras = json.load(f)
    else:
        working_cameras = []

    # Initialize a queue for cameras to be processed
    cams_queue = deque()

    # Add existing working cameras and their neighbors to the queue
    existing_keys = set()
    for working_cam in working_cameras:
        add_to_queue(working_cam, cams_queue, tested_keys, existing_keys)

        neighbors = get_neighboring_ips(working_cam["ip"])
        for neighbor_ip in neighbors:
            neighbor_cam = {
                "ip": neighbor_ip,
                "port": working_cam["port"],
                "productvendor": working_cam["productvendor"]
            }
            add_to_queue(neighbor_cam, cams_queue, tested_keys, existing_keys)

    # Add all untested cameras to the queue
    for camera in cameras:
        add_to_queue(camera, cams_queue, tested_keys, existing_keys)

    # Process the camera queue
    process_camera_queue(cams_queue, tested_keys, tested_cameras, output_file, tested_file)

    # Generate the map
    generate_map('data/working_cameras.json', 'map/camera_map.html')


if __name__ == '__main__':
    main()
