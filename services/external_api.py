import requests

class ExternalAPIService:
    @staticmethod
    def fetch_by_barcode(barcode: str):
        """
        Fetches product information from OpenFoodFacts by barcode.
        Useful for when OCR yields a barcode or as an alternative scan method.
        """
        if not barcode:
            return None
            
        url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
        try:
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            data = res.json()
            if data.get("status") == 1:
                return data.get("product")
        except Exception as e:
            print(f"External API Error: {str(e)}")
            
        return None
