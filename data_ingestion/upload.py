import os
from dotenv import load_dotenv
from algoliasearch.search_client import SearchClient
import json

# Load environment variables from .env file
load_dotenv()

# Get Algolia credentials from environment variables
ALGOLIA_APP_ID = os.getenv('ALGOLIA_APP_ID')
ALGOLIA_API_KEY = os.getenv('ALGOLIA_API_KEY')

# Initialize Algolia client
client = SearchClient.create(ALGOLIA_APP_ID, ALGOLIA_API_KEY)
index = client.init_index('products')

# Load data from a local JSON file or any other source
with open('/content/sample_data/data/expected_algolia_payload.json', 'r') as file:
    data = json.load(file)

# Upload data to Algolia
index.save_objects(data, {'autoGenerateObjectIDIfNotExist': True})

print("Data uploaded successfully to Algolia")

