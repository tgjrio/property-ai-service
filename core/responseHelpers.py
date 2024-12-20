from core.responseInstructions import instructions
from dotenv import load_dotenv
from openai import OpenAI

import logging
import astrapy
import json
import os


# Initialize Datastax client and database
astrapy_client = astrapy.DataAPIClient()
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(funcName)s]',
    datefmt='%Y-%m-%d %H:%M:%S'
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

COLLECTION_NAME=os.getenv("ASTRA_COLLECTION_NAME")

database = astrapy_client.get_database(
    api_endpoint=os.getenv("ASTRA_DB_API_ENDPOINT"),
    token=os.getenv("ASTRA_DB_APPLICATION_TOKEN")
)

# Helper Functions
def generate_embedding(input_data: str):
    """
    Generate a vector embedding for a query using OpenAI.
    """
    try:
        response = client.embeddings.create(
            input=input_data,
            model="text-embedding-3-large",
        )
        return response.data[0].embedding
    except Exception as e:
        logging.error(f"Error generating embedding: {e}")
        return None

def parse_with_gpt_json(user_input: str, response_format):
    """
    Use GPT to parse the sentence into structured JSON fields.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {
                    "role": "system",
                    "content": "Extract property details into JSON data with operators (e.g., 'at least' -> gte, 'up to' -> lte)."
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ],
            response_format=response_format
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error parsing with GPT JSON: {e}")
        return None
    
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

def generate_summary(property_data, user_input):
    """
    Generate a summary using GPT for the given property data.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": f"{instructions}"},
                {"role": "user", "content": user_input},
                {"role": "user", "content": json.dumps(property_data)}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error generating summary: {e}")
        return ""

def query_datastax_with_embedding(embedding, parsed_fields):
    """
    Query the Datastax collection using the generated embedding and dynamic filters with operators.
    """
    try:
        # Base filter list for combining conditions
        filters = []

        # Add filters for string fields
        for field in ["city", "state", "hometype", "homestatus"]:
            if field in parsed_fields and parsed_fields[field] != "none":
                # Ensure proper formatting
                value = (
                    parsed_fields[field].upper() if field == "state" else parsed_fields[field].title() if isinstance(parsed_fields[field], str) else parsed_fields[field]
                )
                filters.append({field: value})

        # Add filters for numeric fields with dynamic operators
        for field in ["datePosted", "datesold", "price", "yearbuilt", "livingarea", "bathrooms", "bedrooms", "pageviewCount", "favoritecount"]:
            if field in parsed_fields and parsed_fields[field] != "none":
                field_data = parsed_fields[field]  # Expecting a dict with "value" and "operator"
                if isinstance(field_data, dict) and "value" in field_data and "operator" in field_data:
                    value = field_data["value"]
                    operator = field_data["operator"]
                    if operator in ["gte", "lte", "eq"]:  # Validate operator
                        filters.append({field: {f"${operator}": value}})

        # Combine filters using $and
        combined_filter = {"$and": filters} if filters else {}

        # Log the constructed filters for debugging
        logging.info(f"Constructed filters: {combined_filter}")

        # Query Datastax collection
        collection = database.get_collection(name=COLLECTION_NAME)
        cursor = collection.find(
            filter=combined_filter,
            sort={"$vector": embedding},
            limit=21,
            include_similarity=True
        )

        # Fetch results
        results = list(cursor)
        return [
            {
                "document": result,
                "similarity": result.get("$similarity", None),
            }
            for result in results
        ]
    except Exception as e:
        logging.error(f"Error querying Datastax: {e}")
        return []