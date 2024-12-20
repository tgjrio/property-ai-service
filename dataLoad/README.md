# BigQuery to Datastax Pipeline

This README describes the functionality and workflow of a data pipeline designed to transfer data from Google BigQuery to Datastax. The pipeline preprocesses rows, generates vector embeddings using OpenAI, and stores the enriched data in a Datastax collection.

## Overview

This pipeline automates the following tasks:
1. Fetches data from **Google BigQuery**.
2. Preprocesses rows to normalize and create descriptive text for embedding.
3. Generates embeddings using **OpenAI's embedding model**.
4. Inserts the enriched data, including embeddings, into a **Datastax collection** in batches.

## Components

### 1. **BigQuery Data Fetching**

The script connects to BigQuery and retrieves rows from a specified table:
```python
async def fetch_bigquery_data():
    """Fetch data from BigQuery."""
    client = bigquery.Client(project=PROJECT_ID)
    query = f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`"
    results = client.query(query)
    rows = [dict(row) for row in results]
    logging.info(f"Fetched {len(rows)} rows from BigQuery.")
    return rows
```

### 2. **Preprocessing Rows**

Prepares each row by normalizing data and creating a descriptive text format for embedding:
```python
def preprocess_row(row, fields):
    """Combine multiple fields into a single string for embedding generation."""
    normalized_row = {field: str(row.get(field, 'none')).strip().lower() for field in fields}
    descriptive_context = [f"{field}: {value}" for field, value in normalized_row.items()]
    return " | ".join(descriptive_context)
```

### 3. **Embedding Generation**

Generates vector embeddings for the descriptive text using OpenAI:
```python
def generate_embedding(text):
    """Generate an embedding using OpenAI."""
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-large"
    )
    return response.data[0].embedding
```

### 4. **Datastax Batch Insertion**

Inserts processed rows, including embeddings, into the Datastax collection:
```python
async def insert_batch_into_datastax(batch):
    """Insert a batch of documents into the Datastax collection."""
    collection = database.get_collection(name=COLLECTION_NAME)
    result = collection.insert_many(batch, ordered=False, chunk_size=100)
    return result
```

---

## Workflow

1. **Fetch Data**:
   - Retrieve rows from BigQuery using the `fetch_bigquery_data` function.

2. **Preprocess Rows**:
   - Normalize and create descriptive text for embedding using `preprocess_row`.

3. **Generate Embeddings**:
   - Generate vector embeddings for each row using OpenAI's `generate_embedding`.

4. **Insert Data into Datastax**:
   - Insert rows, including embeddings, into Datastax in batches of 100.

5. **Log Progress**:
   - Monitor progress with logging for every 200 rows processed.

## Configuration

Environment variables are used to configure the pipeline:
- **`ASTRA_DB_API_ENDPOINT`**: API endpoint for Datastax.
- **`ASTRA_DB_APPLICATION_TOKEN`**: Authentication token for Datastax.
- **`OPENAI_API_KEY`**: API key for OpenAI.
- **`PROJECT_ID`**: Google Cloud project ID.
- **`DATASET_ID`**: BigQuery dataset ID.
- **`TABLE_ID`**: BigQuery table ID.
- **`COLLECTION_NAME`**: Datastax collection name.

## Error Handling

- **Embedding Generation**:
   - Logs errors and skips rows if embedding generation fails.

- **Batch Insertion**:
   - Logs errors during Datastax insertion but continues with the next batch.


## Future Enhancements

1. **Retry Mechanism**:
   - Implement retries for failed embedding generation or batch insertions.

2. **Parallel Processing**:
   - Use asynchronous tasks to handle multiple batches concurrently.

3. **Data Validation**:
   - Add validation to ensure data consistency before insertion.

4. **Performance Optimization**:
   - Optimize preprocessing and embedding generation for large datasets.


## Troubleshooting

- **BigQuery Fetch Issues**:
   - Ensure the `PROJECT_ID`, `DATASET_ID`, and `TABLE_ID` are correctly configured.

- **Embedding Errors**:
   - Verify the `OPENAI_API_KEY` and check OpenAI API rate limits.

- **Datastax Insertion Errors**:
   - Check the `ASTRA_DB_API_ENDPOINT` and `ASTRA_DB_APPLICATION_TOKEN` for accuracy.
