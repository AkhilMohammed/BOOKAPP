import os
import json
import random
import pandas as pd
from typing import Optional, Dict, List, Any
from django.db import transaction
from django.apps import apps
from django.conf import settings
from .schema_reflector import reflect_schema
from .pydantic_builder import build_pydantic_model
from .fk_manager import build_fk_pools, build_fk_dependency_graph
from langchain_groq import ChatGroq
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from langsmith import traceable
from pydantic import BaseModel, Field
import logging
from .prompts import SYSTEM_PROMPT, USER_PROMPT
from django.db import models, transaction
from django.apps import apps
import csv


logger = logging.getLogger(__name__)

# Default max batch size for synthetic generation
DEFAULT_BATCH_SIZE = int(os.getenv("SYNTH_MAX_BATCH", 500))


class SynthGenerator:
    def __init__(self, Model, api_key: Optional[str] = None, max_batch: Optional[int] = None):
        self.Model = Model
        self.schema_meta = reflect_schema(Model)
        self.RowModel = build_pydantic_model(self.schema_meta)
        self.max_batch = max_batch or DEFAULT_BATCH_SIZE  # FIX: ensure max_batch is never None

        logger.info(f"Initialized SynthGenerator for {Model._meta.label} with batch={self.max_batch}")
        logger.debug(f"Schema metadata: {self.schema_meta}")

        groq_key = api_key or os.getenv("GROQ_API_KEY", "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")
        if not groq_key:
            raise ValueError("Groq API key must be provided via argument or environment variable")

        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.8,
            max_tokens=4096,
            api_key=groq_key
        )
        self.parser = PydanticOutputParser(pydantic_object=self.RowModel)

    @traceable
    def _generate_batch(self, count: int, strategy: str, fk_pools: Dict[str, List[int]], sample_df: Optional[pd.DataFrame] = None):
        logger.info(f"Generating batch isisisiis: count={count}, strategy={strategy}")
        logger.info(f"************************************")
        logger.info(f"FK pools: {fk_pools}")

        constraints = self.schema_meta | {"fk_pools": fk_pools}
        system_prompt  = SYSTEM_PROMPT
        user_prompt = USER_PROMPT.format(
            model_label=self.Model._meta.label,
            constraints_json=json.dumps(constraints).replace("{", "{{").replace("}", "}}"),
            strategy=strategy,
            count=count,
            sample_profile=json.dumps(sample_df.head(5).to_dict(orient="records")).replace("{", "{{").replace("}", "}}") if sample_df is not None else "None"
        )
        logger.info(f"System prompt :{system_prompt}")
        logger.info(f"User prompt :{user_prompt}")

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", user_prompt)
        ])

        logger.info("Sending prompt to LLM...")
        chain = prompt | self.llm
        msg = chain.invoke({})
        text = msg.content.strip()
        logger.info(f"LLM raw response: {text[:500]}")

        try:
            payload = json.loads(text)
            logger.info(f"payload {payload}")
            if isinstance(payload, dict):
                payload = [payload]
        except Exception as e:
            logger.warning(f"JSON parse failed, trying line-by-line parsing. Error={e}")
            payload = [json.loads(line) for line in text.splitlines() if line.strip().startswith("{")]

        rows = []
        logger.info(f"payload {payload}")
        for obj in payload:
            try:
                if "id" in obj:
                    obj["id"] = str(obj["id"])
                parsed = self.RowModel.model_validate(obj).model_dump(exclude={"model"})
                for f in self.schema_meta["fields"]:
                    name = f["name"]
                    if f.get("foreign_key"):
                        pool = fk_pools.get(name, [])
                        if pool and (parsed.get(name) is None or parsed.get(name) not in pool):
                            parsed[name] = random.choice(pool)
                rows.append(parsed)
            except Exception as e:
                logger.error(f"Row parse error: {e}, object={obj}")

        logger.info(f"Generated {len(rows)} rows for {self.Model._meta.label}")
        logger.info(f"Generated rows sample: {rows[:3]}")

        return rows

    def generate_csv(self, total_count: int, output_file: Optional[str] = None, fk_pools: Optional[Dict[str, List[int]]] = None):
        fk_pools = fk_pools or build_fk_pools(self.schema_meta)
        logger.info(f"Generating {total_count} rows to CSV for {self.Model._meta.label}")
        all_rows = []

        for start in range(0, total_count, self.max_batch):
            batch_count = min(self.max_batch, total_count - start)
            logger.debug(f"Batch from {start} size={batch_count}")
            rows = self._generate_batch(batch_count, "balanced", fk_pools)
            all_rows.extend(rows)

        if not output_file:
            output_file = f"{self.Model._meta.model_name}_dummy.csv"

        if all_rows:
            pd.DataFrame(all_rows).to_csv(output_file, index=False)
            logger.info(f"Saved {len(all_rows)} rows to {output_file}")
        else:
            logger.warning("No rows generated, CSV not written")

        return output_file

    def generate_and_insert(self, total_count: int):
        fk_pools = build_fk_pools(self.schema_meta)
        inserted_count = 0

        logger.info(f"Inserting {total_count} rows into {self.Model._meta.label}")

        for start in range(0, total_count, self.max_batch):
            batch_count = min(self.max_batch, total_count - start)
            rows = self._generate_batch(batch_count, "balanced", fk_pools)

            objs = [self.Model(**r) for r in rows]
            logger.debug(f"Prepared {len(objs)} objects for insertion")

            with transaction.atomic():
                self.Model.objects.bulk_create(objs, ignore_conflicts=True)
                inserted_count += len(objs)

        logger.info(f"Inserted {inserted_count} rows into {self.Model._meta.label}")
        return inserted_count


class NestedSynthGenerator:
    def __init__(self, ModelList: List, api_key: str = None, max_batch: Optional[int] = None):
        logger.info(f"Initializing Nested generator with models: {[m._meta.label for m in ModelList]}")
        self.models = build_fk_dependency_graph(ModelList)
        logger.info(f"Dependency order: {[m._meta.label for m in self.models]}")
        self.generators = {
            m: SynthGenerator(m, api_key=api_key, max_batch=max_batch or DEFAULT_BATCH_SIZE)
            for m in self.models
        }

    @traceable
    def generate_nested_csv(self, counts: Dict[str, int]):
        fk_data_store = {}
        csv_paths = {}

        for m in self.models:
            model_label = f"{m._meta.app_label}.{m.__name__}"
            row_count = counts.get(model_label, 10)
            generator = self.generators[m]
            logger.info(f"Generating CSV for {model_label} with {row_count} rows")

            fk_pools = {
                f.name: fk_data_store.get(f.remote_field.model._meta.label, [])
                for f in m._meta.get_fields()
                if getattr(f, "remote_field", None) and getattr(f.remote_field, "model", None)
            }
            logger.debug(f"FK pools for {model_label}: {fk_pools}")

            csv_file = generator.generate_csv(row_count, fk_pools=fk_pools)
            df = pd.read_csv(csv_file)
            pk_name = m._meta.pk.attname
            fk_data_store[model_label] = df[pk_name].tolist() if pk_name in df.columns else []
            csv_paths[model_label] = csv_file
            logger.info(f"Generated CSV {csv_file} with {len(df)} rows for {model_label}")

        return csv_paths
    @traceable
    def insert_nested_from_csv(self, csv_paths: Dict[str, str]):
        inserted_count = {}

        for model_label, csv_file in csv_paths.items():
            logger.info(f"Inserting rows for {model_label} from {csv_file}")
            app_label, model_name = model_label.split(".")
            Model = apps.get_model(app_label, model_name)

            # Detect all FK fields dynamically
            fk_fields = {
                field.name: field.name + "_id"
                for field in Model._meta.fields
                if isinstance(field, models.ForeignKey)
            }

            objs = []
            with open(csv_file, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row in reader:
                    # Convert FK fields from "field" -> "field_id"
                    for fk_name, fk_id_name in fk_fields.items():
                        if fk_name in row:
                            row[fk_id_name] = row.pop(fk_name)

                    objs.append(Model(**row))

            with transaction.atomic():
                Model.objects.bulk_create(objs, ignore_conflicts=True)
                inserted_count[model_label] = len(objs)
                logger.info(f"Inserted {len(objs)} rows into {model_label}")

        return inserted_count