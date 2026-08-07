import pandas as pd

csv_path = "c:/Users/natha/Desktop/Project Polaris/data/v1_leaders_vs_challengers.csv"
df = pd.read_csv(csv_path)

years_map = {
    "Cafe Niloufer": 48,
    "Roastery Coffee House": 9,
    "Roast CCX - Coffee & Culinary Xperience": 2,
    "Conçu Jubilee Hills": 14,
    "Habitat Cafe": 2,
    "F3 Café": 7,
    "HC Café (Drive Through Outlet)": 5,
    "SAGE Farm Cafe": 9,
    "Lemerian Workin Cafe": 3,
    "Thrivesome Cafe Co": 2,
    "Mikro Neighbourhood Cafe": 3
}

missing_data = {
    "F3 Café": {"total_reviews": 1500, "average_rating": 4.4, "has_website": 0},
    "HC Café (Drive Through Outlet)": {"total_reviews": 140, "average_rating": 4.9, "has_website": 0}
}

for index, row in df.iterrows():
    name = row['business_name']
    
    # Fill missing Apify data
    if name in missing_data:
        df.at[index, 'total_reviews'] = missing_data[name]['total_reviews']
        df.at[index, 'average_rating'] = missing_data[name]['average_rating']
        df.at[index, 'has_website'] = missing_data[name]['has_website']
        
    # Set years in business
    if name in years_map:
        df.at[index, 'years_in_business'] = years_map[name]

# Calculate review_velocity
df['review_velocity'] = (df['total_reviews'] / df['years_in_business']).round(2)

df.to_csv(csv_path, index=False)
print("CSV Updated Successfully!")
