class ScoringService:
    @staticmethod
    def compute_score(flagged_ingredients: list) -> int:
        """
        Calculates a deterministic health score from 1 to 10.
        """
        score = 10
        for item in flagged_ingredients:
            risk = item.get("risk_level", "Low")
            if risk == "Banned":
                score -= 4
            elif risk == "High":
                score -= 3
            elif risk == "Moderate":
                score -= 2
            elif risk == "Low" and item.get("warning"):
                score -= 1
        
        return max(1, min(10, score))
