import json
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def remove_duplicates_from_json(file_path):
    try:
        # Read the JSON file
        with open(file_path, 'r') as file:
            data = json.load(file)

        # Ensure the file contains a list
        if not isinstance(data, list):
            logging.error("The JSON file does not contain a list.")
            return

        # Remove duplicates while preserving order
        seen = set()
        unique_list = []
        duplicates_count = 0

        for item in data:
            # Convert item to a tuple if it's a dictionary for hashing
            # Otherwise, use the item directly
            item_key = tuple(item.items()) if isinstance(item, dict) else item
            if item_key not in seen:
                unique_list.append(item)
                seen.add(item_key)
            else:
                duplicates_count += 1

        # Write the cleaned list back to the file
        with open(file_path, 'w') as file:
            json.dump(unique_list, file, indent=4)

        logging.info("Duplicates removed successfully.")
        logging.info(f"Total duplicates removed: {duplicates_count}")
        logging.info(f"Remaining unique entries: {len(unique_list)}")
    except FileNotFoundError:
        logging.error(f"File '{file_path}' not found.")
    except json.JSONDecodeError:
        logging.error("Failed to decode JSON. Ensure the file contains valid JSON.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Ensure a file path is provided as a command-line argument
    if len(sys.argv) != 2:
        logging.error("Usage: python remove_duplicates_from_json.py <file_path>")
    else:
        file_path = sys.argv[1]
        remove_duplicates_from_json(file_path)
