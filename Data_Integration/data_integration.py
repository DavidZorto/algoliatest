import requests
import xml.etree.ElementTree as ET
import json
from kafka import KafkaConsumer
from time import sleep
from datetime import datetime
from typing import List, Dict
import logging
from algoliasearch.search_client import SearchClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
API_URL = "http://internal-api.example.com/products"
XML_CATALOG_URL = "https://secure-url.example.com/catalog.xml"
KAFKA_BOOTSTRAP_SERVERS = ['localhost:9092']  # Replace with actual Kafka server addresses
KAFKA_TOPIC = 'product_updates'
ALGOLIA_APP_ID = 'your_algolia_app_id'
ALGOLIA_API_KEY = 'your_algolia_api_key'
ALGOLIA_INDEX_NAME = 'your_product_index'

def fetch_api_data(max_items: int, request_limit: int) -> List[Dict]:

    """Fetch product IDs from the internal API within request limits."""

    products = []
    offset = 0
    requests_made = 0

    while requests_made < request_limit:
        try:
            response = requests.get(f"{API_URL}?limit=1000&offset={offset}")
            response.raise_for_status()
            batch = response.json()
            products.extend(batch)
            offset += len(batch)
            requests_made += 1

            if len(batch) < 1000 or len(products) >= max_items:
                break

            sleep(0.1)  # Respect the rate limit of 10 req/s
        except requests.RequestException as e:
            logger.error(f"Error fetching data from API: {e}")
            break

    return products[:max_items]

def fetch_xml_catalog() -> Dict[str, Dict]:
    """ Fetch and parse XML product catalog. """
    try:
        response = requests.get(XML_CATALOG_URL)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        
        catalog = {}
        for product in root.findall('.//product'):
            product_id = product.find('id').text
            catalog[product_id] = {child.tag: child.text for child in product}
        
        return catalog
    except (requests.RequestException, ET.ParseError) as e:
        logger.error(f"Error fetching or parsing XML catalog: {e}")
        return {}

def process_kafka_updates(catalog: Dict[str, Dict]) -> None:

    """ Process Kafka updates and apply them to the catalog. """

    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )

    for message in consumer:
        update = message.value
        product_id = update.get('id')
        if product_id in catalog:
            # Apply only the fields that are present in both the update and the catalog
            for key, value in update.items():
                if key in catalog[product_id]:
                    catalog[product_id][key] = value
        else:
            logger.warning(f"Received update for unknown product ID: {product_id}")

def enrich_product_data(product_ids: List[Dict], catalog: Dict[str, Dict]) -> List[Dict]:
    
    """ Enrich product data with information from the XML catalog. """
    
    enriched_products = []
    for product in product_ids:
        product_id = product['id']
        if product_id in catalog:
            enriched_product = catalog[product_id]
            enriched_product['id'] = product_id
            enriched_products.append(enriched_product)
        else:
            logger.warning(f"Product ID {product_id} not found in catalog")
    
    return enriched_products

def upload_to_algolia(products: List[Dict]) -> None:
    
    """ Upload the enriched product data to Algolia. """
    
    client = SearchClient.create(ALGOLIA_APP_ID, ALGOLIA_API_KEY)
    index = client.init_index(ALGOLIA_INDEX_NAME)

    try:
        result = index.save_objects(products)
        logger.info(f"Uploaded {len(products)} products to Algolia. Task ID: {result['taskID']}")
    except Exception as e:
        logger.error(f"Error uploading to Algolia: {e}")

def main():
    try:
        # Step 1: Fetch product IDs from the internal API
        logger.info("Fetching product IDs from internal API...")
        product_ids = fetch_api_data(max_items=100000, request_limit=100)  # Adjust as needed

        # Step 2: Fetch and parse the XML catalog
        logger.info("Fetching and parsing XML catalog...")
        catalog = fetch_xml_catalog()

        # Step 3: Process Kafka updates
        logger.info("Processing Kafka updates...")
        process_kafka_updates(catalog)

        # Step 4: Enrich product data
        logger.info("Enriching product data...")
        enriched_products = enrich_product_data(product_ids, catalog)

        # Step 5: Upload to Algolia
        logger.info("Uploading enriched product data to Algolia...")
        upload_to_algolia(enriched_products)

        logger.info("Data integration process completed successfully.")

    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()

