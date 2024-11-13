import os
import json
from collections import deque
import modules.camera_logger as camera_logger
from modules.file_utils import load_cameras, load_tested_cameras
from modules.ip_utils import extract_ip_from_url, get_neighboring_ips
from modules.camera_tester import test_camera_connection
from modules.map import generate_map

def main():
    # Define file paths
    json_file = os.path.join(os.path.dirname(__file__), 'data/cameras.json')
    output_file = os.path.join(os.path.dirname(__file__), 'data/working_cameras.json')
    tested_file = os.path.join(os.path.dirname(__file__), 'data/tested_cameras.json')

    # Load cameras and tested cameras
    cameras = load_cameras(json_file)

    # Load tested cameras as a set of JSON strings
    tested_cameras = set()
    for tested_camera in load_tested_cameras(tested_file):
        tested_cameras.add(json.dumps(tested_camera, sort_keys=True))

    # Load working cameras if output_file exists
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            working_cameras = json.load(f)
    else:
        working_cameras = []

    # Initialize a queue for cameras to be processed
    cams_queue = deque()

    # Add existing working cameras and their neighbors to the queue
    for working_cam in working_cameras:
        cam_key = json.dumps(working_cam, sort_keys=True)
        if cam_key not in tested_cameras:
            cams_queue.append(working_cam)
        neighbors = get_neighboring_ips(working_cam["ip"])
        for neighbor_ip in neighbors:
            neighbor_cam = {
                "ip": neighbor_ip,
                "port": working_cam["port"],
                "productvendor": working_cam["productvendor"]
            }
            neighbor_key = json.dumps(neighbor_cam, sort_keys=True)
            if neighbor_key not in tested_cameras:
                cams_queue.append(neighbor_cam)

    # Add all untested cameras to the queue
    for camera in cameras:
        cam_key = json.dumps(camera, sort_keys=True)
        if cam_key not in tested_cameras:
            cams_queue.append(camera)

    # Process the camera queue
    while cams_queue:
        working_cam = cams_queue.popleft()
        cam_key = json.dumps(working_cam, sort_keys=True)

        # Skip if already tested
        if cam_key in tested_cameras:
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
        tested_cameras.add(cam_key)

        if is_valid:
            # Add neighbors of valid cameras to the queue
            neighbors = get_neighboring_ips(working_cam["ip"])
            for neighbor_ip in neighbors:
                neighbor_cam = {
                    "ip": neighbor_ip,
                    "port": working_cam["port"],
                    "productvendor": working_cam["productvendor"]
                }
                neighbor_key = json.dumps(neighbor_cam, sort_keys=True)
                if neighbor_key not in tested_cameras and neighbor_key not in [json.dumps(cc, sort_keys=True) for cc in cams_queue]:
                    cams_queue.append(neighbor_cam)

    # Generate the map
    generate_map('data/working_cameras.json', 'map/camera_map.html')


if __name__ == '__main__':
    main()
