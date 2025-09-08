from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

def build_pydantic_model(schema_meta: Dict[str, Any]):
    """
    Dynamically builds a Pydantic model class based on the schema metadata of a Django model.

    --- Purpose ---
    This function converts a Django model schema (produced by `reflect_schema`) into a
    Pydantic model class. The Pydantic model can be used for:
        - Data validation
        - Serialization
        - API request/response handling
    dynamically at runtime, without hardcoding fields for each Django model.

    --- How It Works ---
    1. Iterates through each field in `schema_meta["fields"]`.
    2. Maps Django field types (e.g., CharField, IntegerField, DecimalField) to Python/Pydantic types.
       Handles nullable fields with `Optional`.
    3. Constructs a dictionary of field annotations (`__annotations__`) dynamically.
    4. Uses Python's `type()` to create a new Pydantic model class at runtime with the field annotations.
    5. Returns the dynamically created Pydantic model class.

    --- Design Patterns ---
    1. Reflection / Introspection:
       - The function examines the schema metadata at runtime to discover field types and attributes.
       - Analogy: Like opening a box without a manual and seeing what’s inside.
       - Benefit: Works for any Django model automatically.
       - Alternate approaches:
           - Hardcoding fields (not scalable)
           - Using serializers (requires extra maintenance)
           - Database introspection (may miss model-specific Python logic)
    
    2. Factory Pattern:
       - Dynamically creates and returns a new Pydantic model class based on input metadata.
       - Allows creation of many different models using the same logic without manually defining them.

    --- SOLID Principles ---
    1. Single Responsibility Principle (SRP):
       - Function only builds a Pydantic model dynamically.
    2. Open/Closed Principle (OCP):
       - Can be extended to handle additional field metadata (like `verbose_name`, `help_text`) without modifying the core logic.
    3. Liskov Substitution Principle (LSP):
       - Works for any schema from any Django model subclass.
    4. Interface Segregation Principle (ISP) and Dependency Inversion Principle (DIP) are not directly applicable.

    --- Example Use Case ---
    Suppose you have a Django model:
    
        class Book(models.Model):
            title = models.CharField(max_length=100)
            author = models.ForeignKey('Author', on_delete=models.CASCADE)
            price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
            genre = models.CharField(max_length=20, choices=[('F', 'Fiction'), ('NF', 'Non-Fiction')])

    Step 1: Reflect schema
        schema_meta = reflect_schema(Book)

    Step 2: Build Pydantic model
        BookModel = build_pydantic_model(schema_meta)

    Step 3: Create instance and validate
        book_instance = BookModel(title="AI Book", price=299.99)
        print(book_instance.dict())
    
    Output:
        {
            "title": "AI Book",
            "author": None,
            "price": 299.99,
            "genre": None,
            "model": {}
        }

    --- Benefits ---
    - Dynamic: Works for any Django model without rewriting code.
    - Reusable: One function can generate many Pydantic models.
    - Extensible: Easily add support for extra field metadata without modifying existing code.
    - Safe: Leverages Pydantic validation to ensure correct data types.

    --- Example Extension (OCP in Action) ---
    To include extra metadata such as `verbose_name`:
    
        def build_pydantic_model_extended(schema_meta: Dict[str, Any]):
            RowModel = build_pydantic_model(schema_meta)
            for idx, f in enumerate(schema_meta["fields"]):
                RowModel.__annotations__[f["name"]] = (RowModel.__annotations__[f["name"]][0],
                                                       Field(None, description=f.get("verbose_name")))
            return RowModel

    """
    annotations = {}
    field_defaults = {}

    for f in schema_meta["fields"]:
        t = f["type"]
        nullable = f.get("null", True)

        # Map Django field types to Python types
        if t in ["CharField", "TextField", "EmailField", "SlugField", "URLField"]:
            py_type = Optional[str] if nullable else str
        elif t in ["IntegerField", "AutoField", "BigIntegerField", "SmallIntegerField", "PositiveIntegerField"]:
            py_type = Optional[int] if nullable else int
        elif t in ["FloatField", "DecimalField"]:
            py_type = Optional[float] if nullable else float
        elif t in ["BooleanField", "NullBooleanField"]:
            py_type = Optional[bool] if nullable else bool
        elif t in ["DateField", "DateTimeField"]:
            py_type = Optional[str] if nullable else str
        elif t in ["UUIDField"]:
            py_type = Optional[str] if nullable else str
        elif t in ["ForeignKey"]:
            py_type = Optional[int] if nullable else int
        else:
            py_type = Optional[str] if nullable else str

        annotations[f["name"]] = py_type
        field_defaults[f["name"]] = Field(default=None)

    # Base model for extra fields
    class RowModel(BaseModel):
        model: Dict[str, Any] = Field(default_factory=dict)

        class Config:
            extra = "ignore"
            arbitrary_types_allowed = True  # ✅ fix for PydanticSchemaGenerationError

    # Dynamically create new model with annotations
    RowModel = type("RowModel", (RowModel,), {"__annotations__": annotations, **field_defaults})
    return RowModel