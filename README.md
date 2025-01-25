# Property Ai Service

This README outlines the design and functionality of a chatbot service that allows end users to interact with Zillow data using natural language queries. The system retrieves property data based on user inputs, leveraging OpenAI for query validation and embedding generation, and Datastax for data retrieval.


## Overview

The service enables users to query a bot for property data using questions like:

> "Get me properties for sale in Atlanta, GA that cost less than $800k."

The service validates the input, processes the query, retrieves relevant property data, and provides a summary and list of matching properties.


## Components

### 1. **Input Validation**

#### Language Validation
Ensures that the query is in English using the `validate_language` function:
```python
def validate_language(user_input: str) -> bool:
    """
    Validates if the input query is in English.
    """
    try:
        language = detect(user_input)
        return language == 'en'
    except LangDetectException:
        return False
```

#### Input Format Validation
Validates the input format using OpenAI's GPT model to ensure the query is a valid natural-language question about real estate:
```python
async def validate_input_format_ai(user_input: str, client) -> bool:
    """
    Validates the user input dynamically using AI.
    """
    response = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": "..."},
            {"role": "user", "content": user_input}
        ]
    )
    return response.choices[0].message.content.strip().lower() == "true"
```
---
### 2. **Embedding Generation**
**Normalizes row before embedding:**

```python
def preprocess_row(row, fields):
    """Combine multiple fields into a single string for embedding generation with 
    normalization and descriptive context."""
    
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

```

**EXAMPLE RESPONSE FOR NORMALIZING ROWS:**

```txt
{
	'city': 'atlanta', 
	'state': 'ga', 
	'county': 'none', 
	'zipcode': 'none', 
	'datePosted': "{'value': 'none', 'operator': 'none'}", 
	'datesold': "{'value': 'none', 'operator': 'none'}", 
	'hometype': 'single family', 
	'homestatus': 'for sale', 
	'price': "{'value': 800000, 'operator': 'lte'}", 
	'yearbuilt': "{'value': none, 'operator': 'none'}", 
	'livingarea': "{'value': none, 'operator': 'none'}", 
	'bathrooms': "{'value': none, 'operator': 'none'}", 
	'bedrooms': "{'value': none, 'operator': 'none'}", 
	'pageviewcount': "{'value': none, 'operator': 'none'}", 
	'favoritecount': "{'value': none, 'operator': 'none'}"
}
```
-

**EXAMPLE RESPONSE FOR DESCRIPTIVE TEXT:**

``` text
city: atlanta | state: ga | county: none | zipcode: none | datePosted: {'value': 'none', 'operator': 'none'} | datesold: {'value': 'none', 'operator': 'none'} | hometype: single family | homestatus: for sale | 
'price: {'value': 800000, 'operator': 'lte'} | yearbuilt: {'value': none, 'operator': 'none'} | 
livingarea: {'value': none, 'operator': 'none'} | bathrooms: {'value': none, 'operator': 'none'} | 
bedrooms: {'value': none, 'operator': 'none'} | 
pageviewcount: {'value': none, 'operator': 'none'} | favoritecount: {'value': none, 'operator': 'none'}
```
-

**Generates vector embeddings for user inputs using OpenAI's embedding model:**
```python
def generate_embedding(input_data: str):
    """
    Generate a vector embedding for a query using OpenAI.
    """
    response = client.embeddings.create(
        input=input_data,
        model="text-embedding-3-large",
    )
    return response.data[0].embedding
```
**EXAMPLE EMBEDDING:**
``` text
[-0.019218720495700836,0.025079138576984406,-0.00576705252751708,0.037690527737140656,0.01233129482716322,...]
```
-

---

### 3. **Querying Datastax**
Queries the Datastax collection using embeddings and dynamic filters:
```python
def query_datastax_with_embedding(embedding, parsed_fields):
    """
    Query the Datastax collection using embeddings and filters.
    """
    filters = []
    for field in ["city", "state", "hometype", "homestatus"]:
        if field in parsed_fields and parsed_fields[field] != "none":
            value = parsed_fields[field].title() if isinstance(parsed_fields[field], str) else parsed_fields[field]
            filters.append({field: value})
    for field in ["price", "bedrooms"]:
        if field in parsed_fields and parsed_fields[field] != "none":
            field_data = parsed_fields[field]
            if "value" in field_data and "operator" in field_data:
                filters.append({field: {f"${field_data['operator']}": field_data["value"]}})
    combined_filter = {"$and": filters} if filters else {}
    collection = database.get_collection(name=COLLECTION_NAME)
    cursor = collection.find(
        filter=combined_filter,
        sort={"$vector": embedding},
        limit=21,
        include_similarity=True
    )
    return [{"document": result, "similarity": result.get("$similarity", None)} for result in list(cursor)]
```
**EXAMPLE DYNAMIC FILTERING**
``` text
{
    '$and': [
        {'city': 'Atlanta'}, 
        {'state': 'GA'}, 
        {'hometype': 'Single Family'}, 
        {'homestatus': 'For Sale'}, 
        {'price': {'$lte': 800000}} -- lte = Less than or equal to
    ]
} 
```
-

---

### 4. **Summary Generation**
Generates a summary of the property data using GPT:
```python
def generate_summary(property_data, user_input):
    """
    Generate a summary using GPT for the given property data.
    """
    response = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": "..."},
            {"role": "user", "content": user_input},
            {"role": "user", "content": json.dumps(property_data)}
        ]
    )
    return response.choices[0].message.content
```
---

## Workflow

1. **Input Validation**:
   - Validate query language and format.
   - Check for ambiguous or irrelevant queries.

2. **Embedding Generation**:
   - Generate a vector embedding for the query using OpenAI.

3. **Data Query**:
   - Use the embedding and parsed fields to query the Datastax collection.
   - Apply dynamic filters based on query parameters (e.g., price, location).

4. **Summary and Response**:
   - Generate a summary of the matching properties.
   - Return the summary and property list to the user.

---

## API Endpoints

### `POST /process_request/`
Handles user queries by validating input, querying Datastax, and generating a response.

#### Request Body
```json
{
  "user_input": "Get me properties for sale in Atlanta, GA that cost less than $800k."
}
```

#### Response Body
```json
{
  "properties": [
    {
      "address": "123 Main St",
      "price": 750000,
      "bedrooms": 3,
      "bathrooms": 2
    }
  ],
  "summary": "Found 1 property matching your criteria in Atlanta, GA."
}
```


## Troubleshooting
- **Invalid Input**: Ensure queries are in English and formatted as natural-language questions.
- **No Results Found**: Refine search parameters (e.g., price range, location).
- **Service Errors**: Check logs for embedding or Datastax query failures.

---

