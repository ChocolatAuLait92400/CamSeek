import os
import modules.camera_logger as camera_logger
from collections import deque
from modules.file_utils import load_cameras, load_tested_cameras
from modules.ip_utils import extract_ip_from_url, get_neighboring_ips
from modules.camera_tester import test_camera_connection
import json
from modules.map import generate_map

def main():
    json_file = os.path.join(os.path.dirname(__file__), 'data/cameras.json')
    output_file = os.path.join(os.path.dirname(__file__), 'data/working_cameras.json')
    tested_file = os.path.join(os.path.dirname(__file__), 'data/tested_cameras.json')

    cameras = load_cameras(json_file)
    tested_cameras = set(tuple(camera.items()) for camera in load_tested_cameras(tested_file))

    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            working_cameras = json.load(f)
    else:
        working_cameras = []

    cams_queue = deque()

    for working_cam in working_cameras:
        if tuple(working_cam.items()) not in tested_cameras:
            cams_queue.append(working_cam)
        neighbors = get_neighboring_ips(working_cam["ip"])
        for neighbor_ip in neighbors:
            neighbor_tuple = tuple({"ip": neighbor_ip, "port": working_cam["port"], "productvendor": working_cam["productvendor"]}.items())
            if neighbor_tuple not in tested_cameras:
                cams_queue.append({"ip": neighbor_ip, "port": working_cam["port"], "productvendor": working_cam["productvendor"]})

    for camera in cameras:
        if tuple(camera.items()) not in tested_cameras:
            cams_queue.append(camera)

    while cams_queue:
        working_cam = cams_queue.popleft()
        if tuple(working_cam.items()) in tested_cameras:
            continue
        is_valid = test_camera_connection(working_cam["productvendor"], working_cam["ip"], working_cam["port"], output_file, tested_file)[0]
        tested_cameras.add(tuple(working_cam.items()))

        if is_valid:
            neighbors = get_neighboring_ips(working_cam["ip"])
            for neighbor_ip in neighbors:
                neighbor_tuple = tuple({"ip": neighbor_ip, "port": working_cam["port"], "productvendor": working_cam["productvendor"]}.items())
                if neighbor_tuple not in tested_cameras and neighbor_tuple not in [tuple(cc.items()) for cc in cams_queue]:
                    cams_queue.append({"ip": neighbor_ip, "port": working_cam["port"], "productvendor": working_cam["productvendor"]})

    generate_map('data/working_cameras.json', 'map/camera_map.html')


if __name__ == '__main__':
    main()
