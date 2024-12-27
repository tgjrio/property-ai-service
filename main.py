from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from typing import List

import core.responseHelpers as hp
import core.responseFormat as rf
import core.queryHandler as qh

import logging
import json
import os

app = FastAPI()
 
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(funcName)s]',
    datefmt='%Y-%m-%d %H:%M:%S'
)

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

class UserRequest(BaseModel):
    user_input: str

@app.post("/process_request/")
async def process_request(user_request: UserRequest):
    user_input = user_request.user_input

    # Step 1: Validate input format
    if not await qh.validate_input_format_ai(user_input, client):
        invalid_input_message = await qh.generate_invalid_input_message(user_input, client)
        return {
            "status": "error",
            "message": invalid_input_message
        }

    # Step 3: Validate the query for ambiguity and relevance
    validation = await qh.validate_query(user_input, client)

    # Handle ambiguous queries
    if validation["ambiguous"]:
        refinement_message = await qh.generate_unsupported_complexity_message(user_input, client)
        return {"status": "error", "message": refinement_message}

    # Handle non-real-estate queries
    if not validation["real_estate_related"]:
        non_real_estate_message = await qh.generate_non_real_estate_message(user_input, client)
        return {"status": "error", "message": non_real_estate_message}

    # Handle unsupported or overly complex queries
    if validation["unsupported_complexity"]:
        complexity_message = await qh.generate_unsupported_complexity_message(user_input, client)
        return {"status": "error", "message": complexity_message}

    # Proceed with further processing
    parsed_fields = hp.parse_with_gpt_json(user_input, rf.response_format_main)
    parsed_fields = json.loads(parsed_fields)
    fields_to_embed = [
        "city", "state", "county",
        "zipcode", "datePosted", "datesold", 
        "hometype", "homestatus", "price", 
        "yearbuilt", "livingarea", "bathrooms", 
        "bedrooms", "pageviewcount", "favoritecount"
    ]
    return await fetch_data(parsed_fields, fields_to_embed, user_input)

async def fetch_data(parsed_fields, fields_to_embed: List[str], user_input: str):
    logging.info("Processing non-aggregate embed request...")
    try:
        # Step 1: Generate embedding for user input
        embedding_input = hp.preprocess_row(parsed_fields, fields_to_embed)
        embedding = hp.generate_embedding(embedding_input)
        if not embedding:
            raise HTTPException(status_code=500, detail="Failed to parse user input.")

        # Step 3: Query main dataset with filters and embedding
        results = hp.query_datastax_with_embedding(embedding, parsed_fields)
        if not results:
            logging.info("No properties found matching the given filters.")
            return {
                    "properties": [],
                    "summary": 
                        """
                            ### No Properties Found

                            Your query did not match any properties in our database. Try refining your search with:
                            - A different city or location.
                            - Adjusting the price range.
                            - Specifying the number of bedrooms or bathrooms.

                            **Example queries:**
                            - "Show me properties listed in San Francisco under $700,000."
                            - "Find homes with 3 bedrooms in Austin."
                        """
                }

        # Step 4: Summarize results
        summary = hp.generate_summary(results, user_input)

        finalResults = {
            "properties": results,
            "summary": summary
        }

        return finalResults

    except Exception as e:
        logging.error(f"Error in non-aggregate embedding workflow: {e}")
        raise HTTPException(status_code=500, detail="Error in non-aggregate embedding workflow.")
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)