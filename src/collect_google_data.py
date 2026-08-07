import os
import pandas as pd
from apify_client import ApifyClient
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

if not APIFY_API_TOKEN or APIFY_API_TOKEN == "your_token_here":
    print("ERROR: Please set your APIFY_API_TOKEN in the .env file.")
    exit(1)

# Initialize the ApifyClient with your API token
client = ApifyClient(APIFY_API_TOKEN)

# Load the dataset to get the list of cafes
csv_path = "../data/v1_leaders_vs_challengers.csv"
df = pd.read_csv(csv_path)
cafes = df['business_name'].tolist()

print(f"Loaded {len(cafes)} cafes from CSV. Preparing to scrape...")

# Prepare the Actor input
# Using the standard Google Maps Scraper actor on Apify (compass/crawler-google-places)
# We append 'Hyderabad' to ensure we get the right location
search_queries = [f"{cafe} Hyderabad" for cafe in cafes]

run_input = {
    "searchStringsArray": search_queries,
    "maxCrawledPlacesPerSearch": 1,
    "language": "en",
    "allPlacesNoSearchAction": ""
}

print("Starting Apify Actor (compass/crawler-google-places)...")
# Run the Actor and wait for it to finish
run = client.actor("compass/crawler-google-places").call(run_input=run_input)

print(f"Actor run finished. Fetching results...")

# Fetch and process Actor results from the run's dataset
results = client.dataset(run.default_dataset_id).iterate_items()

scraped_data = {}
for item in results:
    # Match the result to the original search term
    # This requires some fuzzy matching or just relying on the order/title
    title = item.get('title', '')
    total_reviews = item.get('reviewsCount', 0)
    rating = item.get('totalScore', 0)
    website = item.get('website', '')
    has_website = 1 if website else 0
    
    # Store by title (this might need fuzzy matching in reality, but we assume exact for V1)
    # To be safe, we iterate through our list and check if it's a substring
    matched_cafe = None
    for cafe in cafes:
        if cafe.lower() in title.lower() or title.lower() in cafe.lower():
            matched_cafe = cafe
            break
            
    if matched_cafe:
        scraped_data[matched_cafe] = {
            'total_reviews': total_reviews,
            'average_rating': rating,
            'has_website': has_website
        }

print(f"Successfully extracted data for {len(scraped_data)} cafes.")

# Update the DataFrame
for index, row in df.iterrows():
    cafe_name = row['business_name']
    if cafe_name in scraped_data:
        df.at[index, 'total_reviews'] = scraped_data[cafe_name]['total_reviews']
        df.at[index, 'average_rating'] = scraped_data[cafe_name]['average_rating']
        df.at[index, 'has_website'] = scraped_data[cafe_name]['has_website']
        # Note: years_in_business cannot be perfectly scraped from the top-level place object usually, 
        # it requires digging into the first review date. 
        # For this script, we will prompt the user to manually estimate it if 0.

# Save back to CSV
df.to_csv(csv_path, index=False)
print(f"Updated {csv_path} with scraped data.")
print("Note: 'years_in_business' requires deep review history analysis. Please manually estimate this column for now to calculate review_velocity.")
