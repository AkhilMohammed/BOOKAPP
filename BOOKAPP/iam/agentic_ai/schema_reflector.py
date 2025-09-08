from typing import Dict, Any, List
from django.apps import apps

def reflect_schema(Model) -> Dict[str, Any]:
    """
    Generates a dictionary representation of a Django model's schema by introspecting its fields.

    --- Purpose ---
    This function examines the given Django Model class dynamically at runtime
    and extracts information about its fields, including name, type, constraints,
    choices, and foreign key relationships. It returns a structured dictionary
    representing the model schema.

    --- Design Pattern ---
    Reflection / Introspection Pattern:
    - Reflection allows the function to "look at" the model and its fields at runtime
      without knowing them beforehand.
    - Analogy: Like opening a box without a manual and listing all items inside.
    - Benefit: Works for any Django model dynamically, making the code reusable
      across the project.
    - Alternate approaches:
        1. Hardcoding fields: manually specifying all model fields (not scalable).
        2. Using serializers: depends on external classes and requires updates.
        3. Database introspection: may miss model-specific Python logic like 'choices'.

    --- SOLID Principles Used ---
    1. Single Responsibility Principle (SRP):
       - This function has one responsibility: reflect the schema of a model.
       - It does not handle serialization, validation, or database operations.
    2. Open/Closed Principle (OCP):
       - The function can be extended to include more metadata (e.g., custom field attributes)
         without changing the existing code structure.
    3. Liskov Substitution Principle (LSP):
       - Accepts any Django model subclass, ensuring substitutability.
    4. Interface Segregation Principle (ISP) and Dependency Inversion Principle (DIP) are not directly applicable here.

    --- Example Usage ---
    Suppose you have a Django model:

        class Book(models.Model):
            title = models.CharField(max_length=100)
            author = models.ForeignKey('Author', on_delete=models.CASCADE)
            price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
            genre = models.CharField(max_length=20, choices=[('F', 'Fiction'), ('NF', 'Non-Fiction')])

    Calling `reflect_schema(Book)` will return:

        {
            "model": "myapp.Book",
            "fields": [
                {"name": "id", "type": "AutoField", "null": False, "blank": False, "unique": True},
                {"name": "title", "type": "CharField", "null": False, "blank": False, "max_length": 100},
                {"name": "author", "type": "ForeignKey", "foreign_key": "myapp.Author"},
                {"name": "price", "type": "DecimalField", "null": True, "blank": True, "max_digits": 6, "decimal_places": 2},
                {"name": "genre", "type": "CharField", "null": False, "blank": False, "max_length": 20, "choices": ["F", "NF"]}
            ]
        }

    This demonstrates how reflection/introspection allows dynamic discovery of model structure
    and ensures maintainable, reusable code.
    """
    meta = {"model": f"{Model._meta.app_label}.{Model.__name__}", "fields": []}
    for f in Model._meta.get_fields():
        if not hasattr(f, "attname") or f.many_to_many or f.one_to_many:
            continue
        field = {
            "name": f.name,
            "type": f.get_internal_type(),
            "null": getattr(f, "null", False),
            "blank": getattr(f, "blank", False),
            "unique": getattr(f, "unique", False),
            "choices": [c[0] for c in getattr(f, "choices", [])] if getattr(f, "choices", None) else None
        }
        # Range hints
        if hasattr(f, "max_length"): field["max_length"] = f.max_length
        if hasattr(f, "decimal_places"): field["decimal_places"] = f.decimal_places
        if hasattr(f, "max_digits"): field["max_digits"] = f.max_digits
        # FK
        if getattr(f, "remote_field", None) and getattr(f.remote_field, "model", None):
            field["foreign_key"] = f.remote_field.model._meta.label
        meta["fields"].append(field)
    return meta
