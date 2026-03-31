class RulesEngine:
    # FSSAI Banned Additives (Example)
    BANNED_ADDITIVES = {
        "INS 123": "Amaranth (Banned in India due to health risks)",
        "INS 924": "Potassium Bromate (Banned in food in India)",
        "INS 104": "Quinoline Yellow (Banned in many countries)",
        "INS 127": "Erythrosine (Regulated, potentially harmful if exceeded)"
    }

    @staticmethod
    def apply_rules(enriched_ingredients: list) -> list:
        """
        Applies deterministic safety rules to enriched ingredient data.
        """
        flagged_results = []
        for item in enriched_ingredients:
            # Check for banned additives by name or INS code
            name = item['raw_name'].upper()
            flagged_item = item.copy()
            flagged_item["warning"] = None
            flagged_item["is_banned"] = False

            # Check direct match with internal list
            for code, reason in RulesEngine.BANNED_ADDITIVES.items():
                if code in name:
                    flagged_item["warning"] = reason
                    flagged_item["is_banned"] = True
                    break
            
            # Use database-provided risk level if available and not yet flagged
            if not flagged_item["is_banned"] and item["db_info"]:
                if item["db_info"]["risk_level"] == "Banned":
                    flagged_item["warning"] = item["db_info"]["fssai_status"]
                    flagged_item["is_banned"] = True
                elif item["db_info"]["risk_level"] == "High":
                    flagged_item["warning"] = "⚠️ High Risk Ingredient"

            flagged_results.append(flagged_item)
        return flagged_results
