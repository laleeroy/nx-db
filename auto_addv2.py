import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv

# --- LOAD .env ---
load_dotenv()
RAWG_API_KEY = os.getenv("RAWG_API_KEY")

# --- CONFIG ---
TITLES_DIR = "titles_db"  # folder where all your titles*.json are stored


# === TITLE LOOKUP ACROSS MULTIPLE FILES ===
def get_game_info_from_titles_db(title_id, titles_dir=TITLES_DIR):
    if not os.path.isdir(titles_dir):
        print(f"[WARN] Titles directory '{titles_dir}' not found.")
        return None

    title_id_upper = title_id.upper()

    for file_name in os.listdir(titles_dir):
        if not file_name.endswith(".json"):
            continue
        file_path = os.path.join(titles_dir, file_name)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                titles_db = json.load(f)
                if title_id_upper in titles_db:
                    game_data = titles_db[title_id_upper]
                    print(f"[OK] Found {title_id_upper} in {file_name}")
                    return {
                        "id": title_id_upper,
                        "name": game_data.get("name"),
                        "publisher": game_data.get("publisher"),
                        "releaseDate": game_data.get("releaseDate"),
                        "version": game_data.get("version", 0),
                        "region": game_data.get("region", None),
                        "size": game_data.get("size"),
                        "description": game_data.get("description", "")
                    }
        except Exception as e:
            print(f"[ERROR] Failed reading {file_path}: {e}")

    print(f"[INFO] {title_id_upper} not found in any titles.json inside '{titles_dir}'.")
    return None


# === DATA CHECK ===
def is_data_complete(game_data):
    return bool(
        game_data
        and game_data.get("name")
        and game_data.get("size")
    )


# === UTILS ===
def reformat_date(date_str):
    try:
        return int(datetime.strptime(date_str, '%m-%d-%Y').strftime('%Y%m%d'))
    except Exception:
        return None


def size_to_bytes(size_str):
    if not size_str:
        return None
    try:
        num, unit = size_str.split()
        num = float(num)
        unit = unit.upper()
        if "KB" in unit:
            return int(num * 1024)
        elif "MB" in unit:
            return int(num * 1024**2)
        elif "GB" in unit:
            return int(num * 1024**3)
        elif "TB" in unit:
            return int(num * 1024**4)
    except Exception:
        return None
    return None


# === FETCH FROM TINFOIL.MEDIA ===
def fetch_tinfoil_info(title_id):
    url = f"https://tinfoil.media/Title/{title_id}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Could not fetch {title_id}: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    title_tag = soup.find("meta", {"property": "og:title"})
    name = title_tag["content"] if title_tag and title_tag.has_attr("content") else None

    desc_tag = soup.find("meta", {"property": "og:description"})
    description = desc_tag["content"] if desc_tag and desc_tag.has_attr("content") else None

    release_date = None
    size = None
    version = 0
    publisher = None
    region = None

    for li in soup.select("ul.fields li"):
        h4 = li.find("h4")
        div = li.find("div")
        if not h4 or not div:
            continue
        key = h4.get_text(strip=True)
        val = div.get_text(strip=True)
        if key == "Release Date":
            release_date = reformat_date(val)
        elif key == "Size":
            size = size_to_bytes(val)
        elif key == "Version":
            try:
                version = int(val) if val else 1
            except:
                version = 1
        elif key == "Publisher":
            publisher = val if val and val != "N/A" else None
        elif key == "Region":
            region = val if val else None

    return {
        "id": title_id,
        "name": name,
        "publisher": publisher,
        "releaseDate": release_date,
        "version": version,
        "region": region,
        "size": size,
        "description": description
    }


# === FETCH DESCRIPTION FROM RAWG ===
def fetch_description_from_rawg(title):
    if not RAWG_API_KEY:
        print("[WARN] RAWG API key not set. Skipping RAWG description lookup.")
        return None

    try:
        print(f"[INFO] Searching RAWG for '{title}'...")
        url = f"https://api.rawg.io/api/games?search={title}&key={RAWG_API_KEY}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        if not results:
            print("[WARN] No matching game found on RAWG.")
            return None
        game_id = results[0]["id"]
        details_url = f"https://api.rawg.io/api/games/{game_id}?key={RAWG_API_KEY}"
        details = requests.get(details_url, timeout=10).json()
        description = details.get("description_raw")
        if description:
            print("[OK] English description found on RAWG.")
            return description.strip()
        else:
            print("[WARN] No description found on RAWG for this game.")
    except Exception as e:
        print(f"[ERROR] RAWG lookup failed: {e}")
    return None


# === FETCH AND SAVE ===
def fetch_game_info(title_id):
    print(f"Looking up {title_id}...")
    game_data = get_game_info_from_titles_db(title_id)
    if game_data and is_data_complete(game_data):
        print(f"[OK] Found complete data in {TITLES_DIR}")
        return game_data
    else:
        print(f"[INFO] Data incomplete or not found in {TITLES_DIR}, checking tinfoil.media...")
        game_data = fetch_tinfoil_info(title_id)
        if game_data:
            print(f"[OK] Found on tinfoil.media")
            return game_data
    return None


def save_game_data(title_id):
    data = fetch_game_info(title_id)
    if not data:
        print("[ERROR] Failed to fetch data from both sources.")
        return

    print(f"[NOTICE] Found title: {data['name']}")
    choice = input("Do you want to change it? (Y/n): ").strip().lower()
    description_changed = False

    if choice in ["", "y", "yes"]:
        new_name = input("Enter the correct English title: ").strip()
        if new_name:
            print(f"[INFO] Title changed to '{new_name}'")
            data["name"] = new_name
            rawg_desc = fetch_description_from_rawg(new_name)
            if rawg_desc:
                data["description"] = rawg_desc
                description_changed = True
            else:
                print("[INFO] Using existing description from JSON/Tinfoil.")
        else:
            print("[INFO] No new title entered, keeping original.")
    else:
        print(f"[INFO] Keeping original title and description.")

    os.makedirs("base", exist_ok=True)
    file_path = os.path.join("base", f"{title_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    size_display = "Unknown"
    if data.get("size"):
        if data["size"] >= 1024**3:
            size_display = f"{data['size']/1024**3:.1f}G"
        elif data["size"] >= 1024**2:
            size_display = f"{data['size']/1024**2:.1f}M"
        elif data["size"] >= 1024:
            size_display = f"{data['size']/1024:.1f}K"
        else:
            size_display = f"{data['size']}B"

    print(f"[OK] Saved metadata to {file_path}")
    print(f"     Name: {data['name']}")
    print(f"     Size: {size_display}")
    print(f"     Publisher: {data.get('publisher')}")
    print(f"     Region: {data.get('region')}")
    print(f"     Description updated from RAWG: {'Yes' if description_changed else 'No'}")


def main():
    title_id = input("Enter Title ID: ").strip()
    if title_id:
        save_game_data(title_id)
    else:
        print("[ERROR] No Title ID entered.")


if __name__ == "__main__":
    main()
