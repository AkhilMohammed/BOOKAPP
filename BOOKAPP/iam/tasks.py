

# from celery import shared_task
# from iam.agentic_ai.generator import NestedSynthGenerator
# from django.apps import apps

# @shared_task
# def generate_and_insert_nested(models:list, counts:dict):
#     model_objs = [apps.get_model(*m.split(".")) for m in models]
#     generator = NestedSynthGenerator(model_objs)
#     csv_paths = generator.generate_nested(counts)
#     inserted = generator.insert_nested(csv_paths)
#     return inserted

from django.apps import apps
from .agentic_ai.generator import NestedSynthGenerator
from bookonlinesales.celery import app
import logging

logger = logging.getLogger(__name__)
from django.apps import apps
from .agentic_ai.generator import NestedSynthGenerator
from bookonlinesales.celery import app
import logging

logger = logging.getLogger(__name__)

@app.task
def generate_and_insert_nested(app_labels, counts: dict):
    if isinstance(app_labels, str):
        app_labels = [app_labels]  # normalize to list

    all_inserted = {}

    logger.info(f"App labels received: {app_labels}")

    # Build list of model classes to generate
    model_classes = []
    for label in app_labels:
        app_name, model_name = label.split(".")
        model_class = apps.get_model(app_name, model_name)
        model_classes.append(model_class)
        logger.info(f"Adding model for generation: {model_class}")

    # Create generator for these models
    generatorobj = NestedSynthGenerator(model_classes)

    logger.info(f"NestedSynthGenerator object created: {generatorobj}")

    csv_paths = generatorobj.generate_nested_csv(counts)
    inserted = generatorobj.insert_nested_from_csv(csv_paths)

    for cls in model_classes:
        label = f"{cls._meta.app_label}.{cls.__name__}"
        all_inserted[label] = inserted.get(label, {})

    return all_inserted
