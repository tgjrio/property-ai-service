response_format_main={
    "type": "json_schema",
    "json_schema": {
        "name": "property_schema",
        "schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City of the property. Put 'none' if the value isn't picked up from the user's request."
                },
                "state": {
                    "type": "string",
                    "description": "State of the property (abbreviated). Put 'none' if the value isn't picked up from the user's request."
                },
                "county": {
                    "type": "string",
                    "description": "County of the property. Put 'none' if the value isn't picked up from the user's request."
                },
                "zipcode": {
                    "type": "string",
                    "description": "Zip code of the property. Put 'none' if the value isn't picked up from the user's request."
                },
                "datePosted": {
                    "type": "object",
                    "properties": {
                        "value": {
                            "type": "string",
                            "format": "date",
                            "description": "Date of when the property was listed for sale in YYYY-MM-DD format. Put 'none' if the value isn't picked up from the user's request."
                        },
                        "operator": {
                            "type": "string",
                            "enum": ["gte", "lte", "eq"],
                            "description": "Comparison operator. Put 'none' if the value isn't picked up from the user's request."
                        }
                    },
                    "required": ["value"]
                },
                "datesold": {
                    "type": "object",
                    "properties": {
                        "value": {
                            "type": "string",
                            "format": "date",
                            "description": "Date of when the property was sold in YYYY-MM-DD format. Put 'none' if the value isn't picked up from the user's request."
                        },
                        "operator": {
                            "type": "string",
                            "enum": ["gte", "lte", "eq"],
                            "description": "Comparison operator. Put 'none' if the value isn't picked up from the user's request."
                        }
                    },
                    "required": ["value"]
                },
                "hometype": {
                    "type": "string",
                    "description": "Type of the home (e.g., Single Family, Lot). Put 'none' if the value isn't picked up from the user's request."
                },
                "homestatus": {
                    "type": "string",
                    "description": "Status of the home (Values Available: For Sale,, Recently Sold, Pending, For Rent, Pre Forclosure, Foreclosed, Other). Put 'none' if the value isn't picked up from the user's request."
                },
                "price": {
                    "type": "object",
                    "properties": {
                        "value": {
                            "type": "number",
                            "description": "Price value. Put 'none' if the value isn't picked up from the user's request. If user is asking for an average, do no put anything here."
                        },
                        "operator": {
                            "type": "string",
                            "enum": ["gte", "lte", "eq"],
                            "description": "Comparison operator. Put 'none' if the value isn't picked up from the user's request."
                        }
                    },
                    "required": ["value"]
                },
                "yearbuilt": {
                    "type": "object",
                    "properties": {
                        "value": {
                            "type": "number",
                            "description": "Year built value. Put 'none' if the value isn't picked up from the user's request."
                        },
                        "operator": {
                            "type": "string",
                            "enum": ["gte", "lte", "eq"],
                            "description": "Comparison operator. Put 'none' if the value isn't picked up from the user's request."
                        }
                    },
                    "required": ["value"]
                },
                "livingarea": {
                    "type": "object",
                    "properties": {
                        "value": {
                            "type": "number",
                            "description": "Living area in sqft. Put 'none' if the value isn't picked up from the user's request."
                        },
                        "operator": {
                            "type": "string",
                            "enum": ["gte", "lte", "eq"],
                            "description": "Comparison operator. Put 'none' if the value isn't picked up from the user's request."
                        }
                    },
                    "required": ["value"]
                },
                "bathrooms": {
                    "type": "object",
                    "properties": {
                        "value": {
                            "type": "number",
                            "description": "Number of bathrooms. Put 'none' if the value isn't picked up from the user's request."
                        },
                        "operator": {
                            "type": "string",
                            "enum": ["gte", "lte", "eq"],
                            "description": "Comparison operator. Put 'none' if the value isn't picked up from the user's request."
                        }
                    },
                    "required": ["value"]
                },
                "bedrooms": {
                    "type": "object",
                    "properties": {
                        "value": {
                            "type": "number",
                            "description": "Number of bedrooms. Put 'none' if the value isn't picked up from the user's request."
                        },
                        "operator": {
                            "type": "string",
                            "enum": ["gte", "lte", "eq"],
                            "description": "Comparison operator. Put 'none' if the value isn't picked up from the user's request."
                        }
                    },
                    "required": ["value"]
                },
                "pageviewcount": {
                    "type": "object",
                    "properties": {
                        "value": {
                            "type": "number",
                            "description": "Page view count. Put 'none' if the value isn't picked up from the user's request."
                        },
                        "operator": {
                            "type": "string",
                            "enum": ["gte", "lte", "eq"],
                            "description": "Comparison operator. Put 'none' if the value isn't picked up from the user's request."
                        }
                    },
                    "required": ["value"]
                },
                "favoritecount": {
                    "type": "object",
                    "properties": {
                        "value": {
                            "type": "number",
                            "description": "Favorite count. Put 'none' if the value isn't picked up from the user's request."
                        },
                        "operator": {
                            "type": "string",
                            "enum": ["gte", "lte", "eq"],
                            "description": "Comparison operator. Put 'none' if the value isn't picked up from the user's request."
                        }
                    },
                    "required": ["value"]
                }
            },
            "additionalProperties": False,
            "required": ["city", "state", "homeType", "homeStatus"]
        }
    }
}
