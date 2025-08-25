# charcreator/rules/sr3_priority.py
from typing import Dict, List

class PriorityResolver:
    """
    Compute outcomes for Race/Magic/Attributes/Skills/Resources
    based on an A–E assignment. All data comes from your unified
    sr3 namespace (already loaded via your JSON loader).
    """

    def __init__(self, namespaces: Dict):
        self.ns = namespaces
        # Expect a table under something like "sr3.priorities"
        self.table = self._load_priority_table()

    def _load_priority_table(self) -> Dict:
        # Adapt this to your actual path / shape.
        # Example shape expected:
        # {
        #   "matrix": {
        #      "A": {"Attributes": 30, "Skills": 50, "Resources": 1000000, "Magic": "Full", "Race": "Any"},
        #      "B": {...}, ... "E": {...}
        #   }
        # }
        return self.ns["sr3.priorities"]

    def compute(self, order: List[str]) -> Dict:
        """
        order: list of categories in A..E order, e.g.
            ["Race", "Magic", "Attributes", "Skills", "Resources"]
        returns a dict with derived values for each category.
        """
        rows = ["A", "B", "C", "D", "E"]
        matrix = self.table["matrix"]
        outcome: Dict[str, object] = {}

        for idx, category in enumerate(order):
            row = rows[idx]
            row_vals = matrix[row]

            if category == "Race":
                # Could be "Any", "Human", "Human/Meta", etc.
                # If namespace provides richer race lists, map here.
                outcome["Race"] = row_vals["Race"]

            elif category == "Magic":
                # Could be "Full", "Aspected", "Adept", "None"
                outcome["Magic"] = row_vals["Magic"]

            elif category == "Attributes":
                outcome["Attributes"] = row_vals["Attributes"]

            elif category == "Skills":
                outcome["Skills"] = row_vals["Skills"]

            elif category == "Resources":
                outcome["Resources"] = row_vals["Resources"]

        # Optional: expand “Race”/“Magic” into option lists if present in your ns
        # For v1, just return the raw values from the matrix.
        return outcome
