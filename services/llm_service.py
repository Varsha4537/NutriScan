import os
import json
import time
from openai import OpenAI

class LLMService:
    @staticmethod
    def generate_explanation(text_val: str, profile: list, deterministic_data: dict = None) -> dict:
        """
        Sends extracted text and deterministic analysis to Groq for final reasoning.
        """
        try:
            client = OpenAI(
                api_key=os.environ.get("XAI_API_KEY"),
                base_url="https://api.groq.com/openai/v1"
            )
            
            # Build deterministic context for the LLM
            det_context = ""
            if deterministic_data:
                det_context = f"\nDeterministic Analysis Results:\n- Health Score: {deterministic_data.get('score')}/10\n- Flagged Additives: {json.dumps(deterministic_data.get('warnings'), indent=2)}"

            # Using a raw string for the prompt to avoid f-string escaping issues
            # We use {{ }} to escape literal braces for the .format() call
            PROMPT_TEMPLATE = """You are a professional food safety auditor and nutritionist.
CRITICAL: Use the "Deterministic Analysis Results" below to identify known chemical/regulatory risks. 
If the safety score is low (e.g. < 7), your final `health_score` MUST NOT exceed it significantly.
However, you MUST ALSO evaluate the nutritional quality (sugar, fat, processing) and deduct score accordingly for junk food. 
A product like Oreo should be around 3-4/10 due to high sugar/fat, even if it has no "banned" ingredients.

Product/Ingredients text: {text_val}
User Dietary Preferences: {profile}
{det_context}

Provide a detailed analysis in JSON format:
{{
  "name": "Product Name",
  "subtitle": "Brief description",
  "health_score": 1-10,
  "nutrition_breakdown": [{{ "name": "Fat", "level": "High/Low", "percentage": 85, "tip": "..." }}],
  "regulatory_warnings": [{{ "chemical": "...", "standard": "FDA/ISI/EFSA", "warning": "..." }}],
  "red_flags": ["Ingredient X", "Reason Y"],
  "consumption_advice": "Recommendation",
  "alternatives": [{{ "name": "X", "emoji": "...", "subtitle": "...", "link": "..." }}],
  "summary": "Detailed overall analysis. Mention if its vegan/gluten-free based on profile."
}}
Return ONLY the JSON object. No markdown, no pre-amble."""

            prompt_filled = PROMPT_TEMPLATE.format(
                text_val=text_val, 
                profile=profile, 
                det_context=det_context
            )

            for attempt in range(2):
                try:
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": "You are a professional nutrition and food safety auditor."},
                            {"role": "user", "content": prompt_filled}
                        ],
                        response_format={"type": "json_object"},
                        timeout=25
                    )
                    
                    content = response.choices[0].message.content
                    
                    # Strip markdown code blocks if present
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0].strip()
                    elif "```" in content:
                        content = content.split("```")[1].strip()
                        
                    data = json.loads(content)
                    return data
                except Exception as e:
                    print(f"LLM Attempt {attempt+1} Error: {str(e)}")
                    if attempt < 1: time.sleep(1)
            
            return None
        except Exception as global_e:
            print(f"CRITICAL LLM SERVICE ERROR: {str(global_e)}")
            return None
