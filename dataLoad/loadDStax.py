import os
import asyncio
import logging
import astrapy
from openai import OpenAI
from dotenv import load_dotenv
from google.cloud import bigquery

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(funcName)s]',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Load environment variables
load_dotenv()

# Initialize Datastax client and database
astrapy_client = astrapy.DataAPIClient()
database = astrapy_client.get_database(
    api_endpoint=os.environ["ASTRA_DB_API_ENDPOINT"],
    token=os.environ["ASTRA_DB_APPLICATION_TOKEN"]
)

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# Datastax and BigQuery configuration
COLLECTION_NAME = os.environ['COLLECTION_NAME']
PROJECT_ID = os.environ['PROJECT_ID']
DATASET_ID = os.environ['DATASET_ID']
TABLE_ID = os.environ['TABLE_ID']

async def fetch_bigquery_data():
    """Fetch data from BigQuery."""
    client = bigquery.Client(project=PROJECT_ID)
    query = f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`"
    results = client.query(query)
    rows = [dict(row) for row in results]
    logging.info(f"Fetched {len(rows)} rows from BigQuery.")
    return rows

def preprocess_row(row, fields):
    """Combine multiple fields into a single string for embedding generation with normalization and descriptive context."""
    logging.info("Starting preprocessing of row...")
    
    # Step 1: Normalize Data (convert to lowercase, strip spaces, replace missing values with 'none')
    normalized_row = {}
    for field in fields:
        if field in row:
            value = row[field]
            normalized_row[field] = str(value).strip().lower() if value else "none"
        else:
            normalized_row[field] = "none"  # Explicitly handle missing fields
    
    logging.info(f"Step 1 - Normalized row: {normalized_row}")
    
    # Step 2: Create Descriptive Context for Embedding
    descriptive_context = []
    for field in fields:
        value = normalized_row[field]
        descriptive_context.append(f"{field}: {value}")
    
    descriptive_text = " | ".join(descriptive_context)
    logging.info(f"Step 2 - Descriptive text for embedding: {descriptive_text}")
    
    # Step 3: Verify Output
    if not descriptive_text:
        logging.warning("Preprocessing resulted in an empty descriptive text. Check row data.")
    else:
        logging.info("Preprocessing completed successfully.")
    
    return descriptive_text

def generate_embedding(text):
    """Generate an embedding using OpenAI."""
    logging.info(f"Generating embedding for text: {text[:100]}... (truncated)")  # Shortened log
    try:
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-large"
        )
        embedding = response.data[0].embedding
        logging.info("Embedding generated successfully.")
        return embedding
    except Exception as e:
        logging.error(f"Error generating embedding for text. Error: {e}")
        return None

async def insert_batch_into_datastax(batch):
    """Insert a batch of documents into the Datastax collection."""
    logging.info(f"Inserting a batch of {len(batch)} documents into the Datastax collection.")
    try:
        collection = database.get_collection(name=COLLECTION_NAME)
        result = collection.insert_many(batch, ordered=False, chunk_size=100)
        logging.info(f"Batch inserted successfully.")
        return result
    except Exception as e:
        logging.error(f"Error inserting batch into Datastax. Error: {e}")
        return None

async def main():
    """Main function to orchestrate the data transfer."""
    logging.info("Fetching data from BigQuery...")
    data = await fetch_bigquery_data()
    fields_to_embed = [
        "city", "state", "county", 
        "zipcode", "datePosted", "datesold",
        "hometype", "homestatus", "price", 
        "yearbuilt", "livingarea", "bathrooms", 
        "bedrooms", "pageviewcount", "favoritecount"
    ]

    batch = []
    for i, row in enumerate(data, start=1):
        # Generate embedding for selected fields
        embedding_input = preprocess_row(row, fields_to_embed)
        embedding = generate_embedding(embedding_input)
        if embedding:
            row["$vector"] = embedding
            batch.append(row)
        else:
            logging.warning(f"Skipping row due to embedding error. Row index: {i}")

        # Insert batch when size reaches 100 or it's the last row
        if len(batch) == 100 or i == len(data):
            await insert_batch_into_datastax(batch)
            batch.clear()

        # Log progress
        if i % 200 == 0:
            rows_remaining = len(data) - i
            logging.info(f"Rows processed: {i}, Rows remaining: {rows_remaining}")

    logging.info("Data transfer completed successfully.")

if __name__ == "__main__":
    asyncio.run(main())
