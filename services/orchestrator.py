from services.ocr_service import OCRService
from services.parser import IngredientParser
from services.llm_service import LLMService
from services.food_knowledge import FoodKnowledgeService
from services.rules import RulesEngine
from services.scoring import ScoringService
from services.external_api import ExternalAPIService

class OrchestratorService:
    @staticmethod
    def scan_food_image(file, user_profile: list) -> dict:
        """
        The central entry point for image-based food analysis.
        Orchestrates: OCR -> Parsing -> Knowledge (RAG) -> Rules -> Scoring -> LLM Reasoning.
        """
        # 1. OCR Extraction
        raw_text = OCRService.extract_text(file)
        if not raw_text:
            return {"error": "OCR failed to extract any text from the image.", "partial": True}

        return OrchestratorService._orchestrate_analysis(raw_text, user_profile)

    @staticmethod
    def scan_food_text(text: str, user_profile: list) -> dict:
        """
        Entry point for manual text-based food analysis.
        """
        if not text:
            return {"error": "No text provided.", "partial": True}
            
        return OrchestratorService._orchestrate_analysis(text, user_profile)

    @staticmethod
    def _orchestrate_analysis(text: str, user_profile: list) -> dict:
        """
        Internal shared logic for Parsing -> Knowledge -> Rules -> Scoring -> LLM.
        """
        # 2-5: Deterministic Pipeline (Wrapped for Robustness)
        try:
            # 2. Ingredient Parsing
            ingredients_list = IngredientParser.parse(text)
            
            # 3. Knowledge Enrichment (RAG)
            enriched = FoodKnowledgeService.enrich_ingredients(ingredients_list)
            
            # 4. Apply Deterministic Rules
            flagged = RulesEngine.apply_rules(enriched)
            
            # 5. Deterministic Scoring
            score = ScoringService.compute_score(flagged)
            
            # Collect warnings
            warnings = [f"{item['raw_name']}: {item['warning']}" for item in flagged if item['warning']]
            
            deterministic_context = {
                "score": score,
                "warnings": warnings,
                "ingredients": ingredients_list
            }
        except Exception as e:
            print(f"ERROR: Deterministic Pipeline Failed: {str(e)}")
            score = 5 # default
            warnings = []
            ingredients_list = []
            deterministic_context = None

        # 6. AI-Driven Reasoning & Explanation (Grounded in deterministic data)
        analysis_result = LLMService.generate_explanation(
            text, 
            user_profile, 
            deterministic_data=deterministic_context
        )
        
        # 7. Post-Process Alternatives (Convert example links to real Amazon search links)
        if analysis_result and "alternatives" in analysis_result:
            for alt in analysis_result["alternatives"]:
                if "name" in alt:
                    query = alt["name"].replace(" ", "+")
                    alt["link"] = f"https://www.amazon.in/s?k={query}"

        if not analysis_result:
            # Fallback to partial result if LLM fails
            return {
                "name": "Scan Result (Text Only)",
                "summary": "AI analysis timed out, but we applied local rules.",
                "health_score": score,
                "raw_text": text,
                "warnings": warnings,
                "partial": True
            }

        return analysis_result
