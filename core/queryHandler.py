import logging
from fastapi import HTTPException
from pydantic import BaseModel
import re
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

# Define the schema for the structured output
class ValidationResponse(BaseModel):
    ambiguous: bool
    real_estate_related: bool
    unsupported_complexity: bool


# Ensures consistent detection results
DetectorFactory.seed = 0

def validate_language(user_input: str) -> bool:
    """
    Validates if the input query is in English.

    Args:
        user_input (str): The user's input query.

    Returns:
        bool: True if the language is English, False otherwise.
    """
    try:
        # Detect the language of the input
        language = detect(user_input)
        return language == 'en'
    except LangDetectException:
        # Handle cases where language detection fails
        return False

async def validate_input_format_ai(user_input: str, client) -> bool:
    """
    Validates the user input dynamically using AI to ensure it is a natural-language query.

    Args:
        user_input (str): The user's input query.
        client: OpenAI client for making API calls.

    Returns:
        bool: True if the input is valid, False otherwise.
    """
    logging.info("Validating user input format with AI...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": (
                    "Evaluate the following query and determine if it is a valid natural-language question "
                    "about real estate or property listings. Respond with 'true' if it is valid, or 'false' if it is invalid."
                )},
                {"role": "user", "content": user_input}
            ]
        )
        is_valid = response.choices[0].message.content.strip().lower() == "true"
        return is_valid
    except Exception as e:
        logging.error(f"Error during input format validation: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while validating the input format.")


async def validate_query(user_input: str, client) -> dict:
    """
    Validate the user query for ambiguity, real estate relevance, and complexity.

    Args:
        user_input (str): The user's input query.
        client: OpenAI client for making API calls.

    Returns:
        dict: A dictionary with keys 'ambiguous', 'real_estate_related', and 'unsupported_complexity'.
    """
    logging.info("Validating user input for ambiguity, real estate relevance, and complexity...")
    try:
        response = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": (
                    "Evaluate the following query for three things: "
                    "1. Is it ambiguous or unclear? "
                    "2. Is it related to real estate? "
                    "3. Does it ask for investor-specific insights, property comparisons, or involve unsupported complexity? "
                    "Respond strictly with a valid JSON object that adheres to the schema."
                )},
                {"role": "user", "content": user_input}
            ],
            response_format=ValidationResponse  # Ensure schema adherence
        )
        validation = response.choices[0].message.parsed
        return {
            "ambiguous": validation.ambiguous,
            "real_estate_related": validation.real_estate_related,
            "unsupported_complexity": validation.unsupported_complexity,
        }
    except Exception as e:
        logging.error(f"Error during validation: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while validating your query.")


async def generate_refinement_message(user_input: str, client) -> str:
    """
    Generate a dynamic refinement message for ambiguous queries.
    
    Args:
        user_input (str): The user's input query.
        client: OpenAI client for making API calls.

    Returns:
        str: A refinement message suggesting improvements to the user's query.
    """
    logging.info("Generating dynamic refinement message...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": (
                    "The user's query is ambiguous or too broad. "
                    "Generate a helpful response explaining why their query needs refinement and provide an example of a more specific query based on their input. "
                    "This is a simple POC app so the suggestions should be like: "
                    "'Can you give me properties in x location with x bedrooms and x bathrooms?'"
                )},
                {"role": "user", "content": user_input}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error generating refinement suggestion: {e}")
        return (
            "Your query is too broad or ambiguous. Please specify additional details, "
            "such as location, price range, or property type, and try again."
        )
    
async def generate_non_real_estate_message(user_input: str, client) -> str:
    """
    Generate a dynamic error message for non-real-estate-related queries.

    Args:
        user_input (str): The user's input query.
        client: OpenAI client for making API calls.

    Returns:
        str: A user-friendly error message with examples of valid, real-estate-related queries.
    """
    logging.info("Generating dynamic response for non-real-estate-related query...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": (
                    "The user's query is not related to real estate. "
                    "Generate a helpful response explaining why their query cannot be processed. "
                    "Provide an example of valid real-estate-related queries, such as listing properties by location, "
                    "price range, or property type."
                )},
                {"role": "user", "content": user_input}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error generating non-real-estate message: {e}")
        return (
            "Your query does not appear to be related to real estate. "
            "Please ask a question about properties, such as listing properties by location, price range, or property type."
        )

async def generate_unsupported_complexity_message(user_input: str, client) -> str:
    """
    Generate a dynamic error message for unsupported or overly complex queries.

    Args:
        user_input (str): The user's input query.
        client: OpenAI client for making API calls.

    Returns:
        str: A user-friendly error message with examples of simpler queries.
    """
    logging.info("Generating dynamic response for unsupported complexity...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": (
                    "The user's query is unsupported or too complex for this system to handle. "
                    "Generate a helpful response explaining why their query cannot be processed and provide an example "
                    "of a simpler query that this system can handle, such as listing properties by location or price range."
                )},
                {"role": "user", "content": user_input}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error generating complexity message: {e}")
        return (
            "Your query is too complex or unsupported by this system. Please simplify your query. "
            "For example, you can ask for a list of properties by location or price range."
        )


async def generate_invalid_input_message(user_input: str, client) -> str:
    """
    Generate a dynamic error message for invalid input formats.

    Args:
        user_input (str): The user's input query.
        client: OpenAI client for making API calls.

    Returns:
        str: A user-friendly error message with examples of valid input formats.
    """
    logging.info("Generating dynamic response for invalid input format...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": (
                    "The user query provided is not in a valid format. "
                    "Analyze the input and generate a helpful response explaining why the format is invalid. "
                    "Provide specific feedback on how to correct the query and examples of valid queries such as: "
                    "'Show me properties listed in San Francisco under $700,000.' or 'Find 3-bedroom homes in Austin.'"
                )},
                {"role": "user", "content": user_input}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error generating invalid input message: {e}")
        return (
            "Your query is not in a valid format. Please ensure your question is written in natural language, such as: "
            "'Show me properties listed in San Francisco under $700,000.' or 'Find 3-bedroom homes in Austin.'"
        )
