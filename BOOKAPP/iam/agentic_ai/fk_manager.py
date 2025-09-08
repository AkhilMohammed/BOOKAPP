# from typing import Dict, List, Any
# from django.apps import apps
# from collections import defaultdict, deque
# import logging
# logger = logging.getLogger(__name__)

# def build_fk_pools(schema_meta: Dict[str, Any]) -> Dict[str, List[int]]:
#     """
#     Builds lookup pools for foreign key fields in a Django model schema.

#     --- Purpose ---
#     This function examines the schema metadata of a Django model (from `reflect_schema`)
#     and generates a dictionary containing sample primary key values for each foreign key field.
#     These pools can be used to:
#         - Automatically populate foreign key fields when creating dummy or test data.
#         - Facilitate bulk data generation or seeding while maintaining referential integrity.

#     --- How It Works ---
#     1. Loops through each field in `schema_meta["fields"]`.
#     2. Checks if the field has a `foreign_key`.
#     3. Retrieves the corresponding Django model class using `apps.get_model`.
#     4. Fetches up to 500 primary key values from the foreign model and stores them in the pool.

#     --- Design Pattern ---
#     - Reflection / Introspection: Dynamically discovers the target model of each foreign key.
#     - Factory-style behavior: Generates a ready-to-use pool of values for dependent fields.

#     --- SOLID Principles ---
#     1. Single Responsibility Principle (SRP): Only responsible for building FK pools.
#     2. Open/Closed Principle (OCP): Can extend to fetch additional fields from the FK model without modifying core logic.
#     3. Liskov Substitution Principle (LSP): Works for any model schema from any Django model subclass.

#     --- Example Use Case ---
#         schema_meta = reflect_schema(Book)
#         fk_pools = build_fk_pools(schema_meta)
#         # Output might be:
#         # {"author": [1, 2, 3, 4, 5], "publisher": [10, 11, 12]}

#     --- Benefits ---
#     - Automates foreign key population.
#     - Maintains referential integrity when generating synthetic data.
#     - Scalable to multiple models and foreign key fields.
#     """
#     pools = {}
#     for f in schema_meta["fields"]:
#         if f.get("foreign_key"):
#             app_label, model_name = f["foreign_key"].split(".")
#             FKModel = apps.get_model(app_label, model_name)
#             pools[f["name"]] = list(FKModel.objects.values_list("pk", flat=True)[:500])
#     return pools

# def build_fk_dependency_graph(models: List) -> List:
#     """
#     Builds a dependency graph of Django models based on their foreign key relationships
#     and returns an order for creating or processing models without violating FK constraints.

#     --- Purpose ---
#     This function analyzes a list of Django models and computes an order in which
#     models should be created or processed, respecting foreign key dependencies.
#     Useful for:
#         - Bulk data insertion while avoiding integrity errors.
#         - Generating synthetic data in the correct dependency order.
#         - Migrating or seeding data across multiple related models.

#     --- How It Works ---
#     1. Initializes a directed graph where nodes are model names and edges represent foreign key dependencies.
#     2. Calculates in-degree for each node (number of dependencies).
#     3. Performs a topological sort using a queue (Kahn’s algorithm):
#         - Start with models that have no dependencies.
#         - Iteratively remove them from the graph, updating in-degree counts.
#     4. Returns a list of Django model classes in an order that satisfies FK constraints.

#     --- Design Pattern ---
#     - Graph / Dependency Analysis: Uses a **directed graph** to represent FK relationships.
#     - Topological Sorting Algorithm (Kahn's Algorithm) as a design for **dependency resolution**.
#     - Factory / Utility pattern: Provides a reusable ordered list of models for bulk operations.

#     --- SOLID Principles ---
#     1. Single Responsibility Principle (SRP): Only responsible for computing FK order.
#     2. Open/Closed Principle (OCP): Can extend to handle more complex dependencies or additional metadata.
#     3. Liskov Substitution Principle (LSP): Works for any list of Django model subclasses.

#     --- Example Use Case ---
#         models = [Author, Publisher, Book]
#         ordered_models = build_fk_dependency_graph(models)
#         # Output: [Author, Publisher, Book]
#         # Ensures Author and Publisher are created before Book (which has FK to them).

#     --- Benefits ---
#     - Prevents foreign key constraint violations during bulk operations.
#     - Supports complex dependency chains.
#     - Can be integrated with synthetic data generators or migration scripts.
#     """
#     graph = defaultdict(list)
#     indegree = defaultdict(int)
#     model_map = {f"{m._meta.app_label}.{m.__name__}": m for m in models}
#     logger.info(f"model map:{model_map.keys()}")
#     logger.info(f"building model map :{model_map}")

#     # Build the graph
#     for m in models:
#         logger.info(f"building model map inside for loop  :{m}")
#         key = f"{m._meta.app_label}.{m.__name__}"
#         logger.info(f"building model map key :{key}")
#         for f in m._meta.get_fields():
#             logger.info(f"building model map f :{f}")
#             if getattr(f, "remote_field", None) and getattr(f.remote_field, "model", None):
#                 logger.info(f"building model map inside if 108")
#                 fk_model = f.remote_field.model
#                 fk_key = f"{fk_model._meta.app_label}.{fk_model.__name__}"
#                 if fk_key in model_map: 
#                     logger.info(f"building model map fk key present:{model_map}") # only include internal models
#                     graph[fk_key].append(key)
#                     indegree[key] += 1
#                     indegree[fk_key] = indegree.get(fk_key, 0)
#                     logger.info(f"graph and indegreeupdated : {graph} {indegree}")
#                 else:
#                     logger.info(f"Skipping external FK dependency: {fk_key}")

#     # Initialize queue with zero indegree nodes
#     queue = deque([k for k in indegree if indegree[k] == 0])
#     ordered = []

#     while queue:
#         node = queue.popleft()
#         if node in model_map:
#             ordered.append(model_map[node])
#         for neighbor in graph.get(node, []):
#             indegree[neighbor] -= 1
#             if indegree[neighbor] == 0:
#                 queue.append(neighbor)

#     return ordered

from typing import Dict, List, Any
from django.apps import apps
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)

def build_fk_pools(schema_meta: Dict[str, Any]) -> Dict[str, List[int]]:
    """
    Build lookup pools for foreign key fields in a Django model schema.
    """
    pools = {}
    for f in schema_meta["fields"]:
        if f.get("foreign_key"):
            app_label, model_name = f["foreign_key"].split(".")
            FKModel = apps.get_model(app_label, model_name)
            pools[f["name"]] = list(FKModel.objects.values_list("pk", flat=True)[:500])
    return pools


def build_fk_dependency_graph(models: List) -> List:
    """
    Build a dependency graph of Django models based on foreign keys
    and return a topologically sorted order.
    """
    graph = defaultdict(list)
    indegree = defaultdict(int)
    model_map = {f"{m._meta.app_label}.{m.__name__}": m for m in models}

    for m in models:
        key = f"{m._meta.app_label}.{m.__name__}"
        for f in m._meta.get_fields():
            if getattr(f, "remote_field", None) and getattr(f.remote_field, "model", None):
                fk_model = f.remote_field.model
                fk_key = f"{fk_model._meta.app_label}.{fk_model.__name__}"
                if fk_key in model_map:
                    graph[fk_key].append(key)
                    indegree[key] += 1
                    indegree[fk_key] = indegree.get(fk_key, 0)
    
    # Topological sort using Kahn's algorithm
    queue = deque([k for k in indegree if indegree[k] == 0])
    ordered = []

    while queue:
        node = queue.popleft()
        if node in model_map:
            ordered.append(model_map[node])
        for neighbor in graph.get(node, []):
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)

    # If cyclic dependencies remain, add them in any order (cycle-safe)
    remaining = [model_map[k] for k in model_map if k not in [m._meta.label for m in ordered]]
    ordered.extend(remaining)
    return ordered
