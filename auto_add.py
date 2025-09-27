import asyncio
import json
import os
from datetime import datetime, date
import rawg

# RAWG API configuration
api_key = ''

async def fetch_game_info(game_id):
    """Fetch detailed game information from RAWG by game ID."""
    async with rawg.ApiClient(rawg.Configuration(api_key={'key': api_key})) as api_client:
        api = rawg.GamesApi(api_client)
        try:
            return await api.games_read(id=game_id)
        except Exception as e:
            print(f"Exception when calling GamesApi->games_read: {e}")
            return None

async def fetch_game_info_by_name(name):
    """Fetch game information from RAWG by game name."""
    async with rawg.ApiClient(rawg.Configuration(api_key={'key': api_key})) as api_client:
        api = rawg.GamesApi(api_client)
        try:
            response = await api.games_list(search=name, search_precise=True)
            if response.results:
                return response.results[0]
            else:
                print(f"[INFO] No results found for '{name}'")
                return None
        except Exception as e:
            print(f"Exception when calling GamesApi->games_list: {e}")
            return None

def reformat_date(date_str):
    """Convert YYYY-MM-DD to YYYYMMDD (int)."""
    if isinstance(date_str, str):
        try:
            return int(datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y%m%d'))
        except ValueError:
            return None
    return None

async def process_games(directory):
    """Process JSON files in the directory and cache metadata."""
    for file_name in os.listdir(directory):
        if not file_name.endswith('.json'):
            continue

        file_path = os.path.join(directory, file_name)
        with open(file_path, 'r') as json_file:
            game_details = json.load(json_file)
            print(f"Processing file: {file_name}")

        # Skip if cached
        if "releaseDate" in game_details and "description" in game_details:
            print(f"[CACHE] Skipping {file_name}, already has metadata.\n")
            continue

        name = game_details.get('name')
        if not name:
            print(f"No name found in {file_name}")
            continue

        base_name = name.split('[')[0].strip()
        search_result = await fetch_game_info_by_name(base_name)

        if not search_result:
            print(f"No search results for '{base_name}'")
            continue

        game_info = await fetch_game_info(search_result.id)
        if not game_info:
            print(f"No details for game ID '{search_result.id}'")
            continue

        # Process release date
        release_date = game_info.released
        if isinstance(release_date, date):
            release_date = release_date.strftime('%Y-%m-%d')
        formatted_date = reformat_date(release_date)
        if formatted_date is not None:
            game_details['releaseDate'] = formatted_date

        # Process description
        description = getattr(game_info, 'description', 'No description available')
        game_details['description'] = description

        # Debug / logging
        print('——————————————————————————————————————————————')
        print(f"        Name | {game_info.name}")
        print(f"    Released | {game_info.released or 'Not available'}")
        print(f"      Rating | {game_info.rating or 'Not available'}")
        print(f"    Website | {getattr(game_info, 'website', 'Not available') or 'Not available'}")
        print(f"  Metacritic | {getattr(game_info, 'metacritic', 'Not available') or 'Not available'}")
        print(f"Description | {game_details['description']}")
        print(f"Formatted Date | {game_details.get('releaseDate', 'Not available')}")
        print('——————————————————————————————————————————————\n')

        # Save updated JSON
        with open(file_path, 'w') as json_file:
            json.dump(game_details, json_file, indent=4, separators=(',', ': '))

async def main():
    directory = "base"  # only use the "base" folder
    if not os.path.exists(directory):
        print(f"The directory {directory} does not exist. Exiting.")
        return

    print(f"Processing games in directory: {directory}")
    await process_games(directory)

if __name__ == "__main__":
    asyncio.run(main())
