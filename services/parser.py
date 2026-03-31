import re

class IngredientParser:
    @staticmethod
    def parse(text: str) -> list:
        """
        Cleans and splits raw OCR text into individual ingredient items.
        Handles common separators like commas, semicolons, and newlines.
        """
        if not text:
            return []
            
        # Convert to lowercase for uniformity
        text = text.lower()
        
        # Remove common "Ingredients:" header if present
        text = re.sub(r'^.*?ingredients:?\s*', '', text, flags=re.IGNORECASE)
        
        # Split by typical separators
        # Regex: comma, semicolon, bullet points or newlines
        parts = re.split(r'[,;•\n\r]', text)
        
        cleaned_ingredients = []
        for p in parts:
            # Remove parentheses content (e.g. "Wheat Flour (from grain)") -> "Wheat Flour"
            p = re.sub(r'\(.*?\)', '', p).strip()
            # Remove percentages (e.g. "Salt 2%") -> "Salt"
            p = re.sub(r'\d+%', '', p).strip()
            # Remove non-alphanumeric at start/end but keep spaces
            p = p.strip(' .:-*')
            
            if len(p) > 1:
                cleaned_ingredients.append(p)
                
        return cleaned_ingredients
