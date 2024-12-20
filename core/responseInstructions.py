instructions = """
PLEASE PROVIDE A HIGH-LEVEL SUMMARY OF THE FOLLOWING REAL ESTATE PROPERTY DATA.
ALSO PLEASE BE SURE TO ANSWER THE USERS QUESTION IN THE SUMMARY.

PAY ATTENTION TO THE DATA AND CONFIRM THE VALUE OF homestatus AND THEN PROCEED WITH THE FOLLOWING STEPS:

FORMAT THE SUMMARY AS FOLLOWS:
1. START WITH AN OVERVIEW:
   - Describe the real estate market, including the total number of properties and location. Mention if there is a variety of property types and any notable price ranges.

2. ORGANIZE BY PROPERTY TYPE (e.g., 'Single-Family Homes', 'Condos', 'Lots for Sale'):
   - For each property type, summarize:
     - The price range of properties within that type.
     - Any notable properties (e.g., the most expensive, highest engagement).
     - Key features (e.g., number of bedrooms, age of construction).
     - Include trends such as average view count or favorites if applicable.

3. SAMPLE SUMMARY:
The real estate market in [City, State] currently features a variety of properties available for sale across different types and price ranges, all located in [County]. Here are some highlights:

- **Single-Family Homes**:
  - Prices range from \$[lowest_price] to \$[highest_price].
  - Notable properties include [description of notable properties, e.g., the most expensive home, the most viewed property].
  - Homes typically have [number] bedrooms and [number] bathrooms, with most being [newly constructed or built in specific years].

- **Lots for Sale**:
  - Prices range from \$[lowest_price] to \$[highest_price].
  - Notable lots include [address or unique identifiers], priced at $[price], with [view count and/or favorites count].

4. PROVIDE AN ENDING INSIGHT:
   - Comment on the overall interest level, indicated by metrics like page views and favorites.
   - Mention the typical property tax rate if available.

MAKE SURE TO:
- Keep the language concise and easy to understand.
- Use bold text for headings like property types and notable details.
- Avoid listing out every property individually unless they are significant.
- Maintain readability with short, informative sentences.

IMPORTANT: 
- When summarizing the price ranges make sure you use \\$ to ensure it's rendered properly on UI.
- Avoid placing numbers directly next to each other without spacing or punctuation.
- Use Markdown format properly, ensuring no words or numbers get concatenated together.
- When talking about price, please uses \\$ to ensure it's rendered properly on the UI.
- Format the summary in a way that ensures readability in a Markdown context, specifically when it will be rendered in a Streamlit UI.
- Ensure that each property detail is clearly separated, and bullet points do not merge text.
"""