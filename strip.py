import json
import os

def strip_titles_json_quick():
    """
    Quick version that strips titles.json to titles_stripped.json without prompts
    Only keeps entries that have an iconUrl
    """
    input_file = "titles.json"
    output_file = "titles_stripped.json"
    
    if not os.path.exists(input_file):
        print(f"[ERROR] {input_file} not found!")
        return False
    
    try:
        # Read the original titles.json
        with open(input_file, 'r', encoding='utf-8') as f:
            titles_data = json.load(f)
        
        # Create stripped data with only title ID and iconUrl
        # Only include entries that have an iconUrl
        stripped_data = {}
        
        for title_id, game_data in titles_data.items():
            icon_url = game_data.get("iconUrl")
            # Only add if iconUrl exists and is not None/empty
            if icon_url:
                stripped_data[title_id] = {
                    "iconUrl": icon_url
                }
        
        # Save the stripped data
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(stripped_data, f, indent=2, ensure_ascii=False)
        
        # Print statistics
        original_count = len(titles_data)
        stripped_count = len(stripped_data)
        
        print(f"[SUCCESS] Created {output_file}")
        print(f"Original entries: {original_count}")
        print(f"Entries with iconUrl: {stripped_count}")
        print(f"Entries without iconUrl: {original_count - stripped_count}")
        
        # Show a few samples
        print(f"\nSample entries:")
        sample_count = min(3, stripped_count)  # Don't try to show more than available
        for i, (title_id, data) in enumerate(list(stripped_data.items())[:sample_count]):
            icon_url = data.get('iconUrl', '')
            icon_preview = icon_url[:50] + "..." if len(icon_url) > 50 else icon_url
            print(f"  {title_id}: {icon_preview}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to process {input_file}: {e}")
        import traceback
        print(f"Full error details: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    strip_titles_json_quick()
