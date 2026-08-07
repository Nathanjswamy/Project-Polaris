import os
import pandas as pd
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

if not APIFY_API_TOKEN:
    print("ERROR: Please set your APIFY_API_TOKEN in the .env file.")
    exit(1)

client = ApifyClient(APIFY_API_TOKEN)

csv_path = "../data/v1_leaders_vs_challengers.csv"
df = pd.read_csv(csv_path)

# Map cafes to their likely Instagram usernames
insta_map = {
    "Cafe Niloufer": "cafeniloufer",
    "Roastery Coffee House": "roasterycoffeehouse",
    "Roast CCX - Coffee & Culinary Xperience": "roast.ccx",
    "Conçu Jubilee Hills": "concu",
    "Habitat Cafe": "habitatcafe.hyd",
    "F3 Café": "f3cafebistro",
    "HC Café (Drive Through Outlet)": "hccaffe",
    "SAGE Farm Cafe": "sagefarmcafe",
    "Lemerian Workin Cafe": "lemerianworkincafe",
    "Thrivesome Cafe Co": "thrivesome",
    "Mikro Neighbourhood Cafe": "mikrostories"
}

usernames = list(insta_map.values())

run_input = {
    "usernames": usernames
}

print(f"Starting Apify Actor (apify/instagram-profile-scraper) for {len(usernames)} profiles...")
run = client.actor("apify/instagram-profile-scraper").call(run_input=run_input)
print(f"Actor run finished. Fetching results...")

results = client.dataset(run.default_dataset_id).iterate_items()

scraped_data = {}
for item in results:
    username = item.get("username", "")
    followers = item.get("followersCount", 0)
    scraped_data[username] = followers

print(f"Successfully extracted data for {len(scraped_data)} profiles.")

for index, row in df.iterrows():
    cafe_name = row['business_name']
    if cafe_name in insta_map:
        username = insta_map[cafe_name]
        if username in scraped_data:
            df.at[index, 'instagram_followers'] = scraped_data[username]

df.to_csv(csv_path, index=False)
print(f"Updated {csv_path} with Instagram followers data.")
