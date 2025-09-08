import os
from .generator import SynthGenerator
from .csv_manager import save_rows_to_csv
from django.apps import apps

class SyntheticDataService:
    """
    High-level service to generate synthetic data and manage CSV storage.
    """

    def __init__(self, model_label: str):
        self.model_label = model_label
        self.Model = apps.get_model("your_app", model_label)
        self.generator = SynthGenerator(self.Model)

    def generate_csv(self, record_count: int, output_file: str = None):
        """
        Generate synthetic rows and save them as a CSV file.
        """
        if output_file is None:
            output_file = f"/tmp/{self.model_label}_synthetic.csv"

        # Generate synthetic rows
        rows = self.generator.generate_and_return_rows(record_count)

        # Save to CSV
        save_rows_to_csv(rows, output_file)
        return output_file

    def generate_and_insert(self, record_count: int):
        """
        Generate synthetic rows and directly insert into DB (optional bulk insert logic).
        """
        rows = self.generator.generate_and_return_rows(record_count)
        objects = [self.Model(**r) for r in rows]

        # Bulk insert using Django
        from django.db import transaction
        with transaction.atomic():
            self.Model.objects.bulk_create(objects, ignore_conflicts=True)

        return len(objects)