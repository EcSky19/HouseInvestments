from dotenv import load_dotenv
import os
import httpx

load_dotenv()

api_key = os.getenv("API_KEY")
zip_code = "10001"  # Example zip code
response = httpx.get(f'https://api.rentcast.io/v1/properties?zipCode={zip_code}&limit=20', headers={'X-Api-Key': api_key, 'Accept': 'application/json'})
print(response.json())

def fetch_properties(zip_code: str, limit: int = 20, bedrooms: int = None, bathrooms: int = None, squareFootage: int = None, price: int = None):
    params = {
        'zipCode': zip_code,
        'limit': limit,
        'bedrooms': bedrooms,
        'bathrooms': bathrooms,
        'squareFootage': squareFootage,
        'price': price
    }
    response = httpx.get(
        'https://api.rentcast.io/v1/properties',
        headers={'X-Api-Key': api_key, 'Accept': 'application/json'},
        params={k: v for k, v in params.items() if v is not None}
    )
    return response.json()