SYSTEM_PROMPT = """You are a data generation agent that creates VALID synthetic rows for a given Django model.
Follow constraints: required fields, nullability, max_length, choices, uniqueness hints, realistic ranges, and ISO date formats.
Avoid PII; invent fake but plausible values. Keep foreign keys limited to provided ID pools.
Output MUST strictly match provided JSON schema."""

USER_PROMPT = """Return EXACTLY {count} JSON objects matching the schema below. 
            Do NOT include any extra text, explanation, or comments. 
            Output MUST be valid JSON parsable by `json.loads()`.

            Model: {model_label}
            Constraints JSON: {constraints_json}
            Strategy: {strategy}
            Count in this batch: {count}
            Sample rows summary (optional): {sample_profile}
            ⚠️ Important rules:
            - All IDs foriegn keys ids (`id`, `user`, etc.) must be strings, not integers.
            Example: "user": "6" (❌ not 6).
            - All date or datetime fields must be valid ISO8601 format (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS).
            - Never leave them blank. If no value, use a realistic default date.
            - uniqueness constraints must be respected. and they should be very unique that they wont clash with existing records.even primary keys
            """

