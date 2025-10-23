import json
import os

def get_game_details(game_id):
    details = {}
    
    details['id'] = game_id
    details['name'] = input("Enter the name: ")
    details['releaseDate'] = 1
    details['version'] = 0
    
    return details

def save_game_details(directory, game_details):
    file_path = os.path.join(directory, f"{game_details['id']}.json")
    with open(file_path, 'w') as json_file:
        json.dump(game_details, json_file, indent=4)
    print(f"Details saved to {file_path}")

def update_game_details(file_path):
    with open(file_path, 'r') as json_file:
        game_details = json.load(json_file)

    print(f"Current details: {json.dumps(game_details, indent=4)}")

    new_name = input(f"Enter the name (current: {game_details['name']}): ")
    if new_name:
        game_details['name'] = new_name

    with open(file_path, 'w') as json_file:
        json.dump(game_details, json_file, indent=4)
    print(f"Details updated in {file_path}")

def main():
    directory = 'base'
    os.makedirs(directory, exist_ok=True)

    game_id = input("Enter the ID of the game: ")
    file_path = os.path.join(directory, f"{game_id}.json")

    if os.path.exists(file_path):
        print(f"{file_path} already exists.")
        update_game_details(file_path)
    else:
        print(f"{file_path} does not exist. Creating new file.")
        game_details = get_game_details(game_id)
        save_game_details(directory, game_details)

if __name__ == "__main__":
    main()
