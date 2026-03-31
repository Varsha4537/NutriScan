from models.ingredient import Ingredient
from models.database import db
import re

class FoodKnowledgeService:
    @staticmethod
    def get_ingredient_info(name: str):
        """
        Looks up an ingredient in the database by name or INS code.
        """
        # 1. Direct name match
        ing = Ingredient.query.filter(Ingredient.name.ilike(name)).first()
        if ing:
            return ing
            
        # 2. INS Code match (if the name looks like an INS code, e.g. "INS 123" or "123")
        ins_match = re.search(r'(?:ins\s*)?(\d+)', name, re.IGNORECASE)
        if ins_match:
            ins_code = f"INS {ins_match.group(1)}"
            ing = Ingredient.query.filter_by(ins_code=ins_code).first()
            if ing:
                return ing
                
        # 3. Check aliases
        # This is a bit more complex for a simple query, but for now we'll skip 
        # or use a simplified fuzzy match if needed.
        
        return None

    @staticmethod
    def enrich_ingredients(ingredient_names: list) -> list:
        """
        Takes a list of raw ingredient names and returns a list of enriched ingredient data.
        """
        enriched_results = []
        for name in ingredient_names:
            info = FoodKnowledgeService.get_ingredient_info(name)
            if info:
                enriched_results.append({
                    "raw_name": name,
                    "db_info": info.to_dict(),
                    "matched": True
                })
            else:
                enriched_results.append({
                    "raw_name": name,
                    "db_info": None,
                    "matched": False
                })
        return enriched_results
