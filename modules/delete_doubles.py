import json
import sys

def remove_duplicates_from_json(file_path):
    try:
        # Read the JSON file
        with open(file_path, 'r') as file:
            data = json.load(file)

        # Ensure the file contains a list
        if not isinstance(data, list):
            print("Error: The JSON file does not contain a list.")
            return

        # Remove duplicates while preserving order
        seen = set()
        unique_list = []
        for item in data:
            # Convert item to a tuple if it's a dictionary for hashing
            # Otherwise, use the item directly
            item_key = tuple(item.items()) if isinstance(item, dict) else item
            if item_key not in seen:
                unique_list.append(item)
                seen.add(item_key)

        # Write the cleaned list back to the file
        with open(file_path, 'w') as file:
            json.dump(unique_list, file, indent=4)

        print("Duplicates removed successfully.")
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON. Ensure the file contains valid JSON.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Ensure a file path is provided as a command-line argument
    if len(sys.argv) != 2:
        print("Usage: python remove_duplicates_from_json.py <file_path>")
    else:
        file_path = sys.argv[1]
        remove_duplicates_from_json(file_path)
