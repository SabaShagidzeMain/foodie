import os
import django
from decouple import config
import requests
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foodie.settings')
django.setup()

def debug_raw():
    """Debug the raw API response"""
    
    app_id = config('EDAMAM_APP_ID', default='')
    app_key = config('EDAMAM_APP_KEY', default='')
    
    print("🔍 Debugging Raw API Response...")
    print("-" * 50)
    
    ingredient = "1 apple"
    url = "https://api.edamam.com/api/nutrition-data"
    params = {
        'app_id': app_id,
        'app_key': app_key,
        'ingr': ingredient
    }
    
    print(f"Testing: '{ingredient}'")
    print()
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        print()
        
        data = response.json()
        
        # Print the full response structure
        print("Full Response:")
        print(json.dumps(data, indent=2)[:2000])  # First 2000 chars
        
        print("\n" + "=" * 50)
        print("Looking for nutrition data...")
        
        # Check all possible locations
        print(f"\n1. 'calories' field: {data.get('calories', 'NOT FOUND')}")
        
        if 'totalNutrients' in data:
            print("\n2. 'totalNutrients' found:")
            for key in ['ENERC_KCAL', 'PROCNT', 'FAT', 'CHOCDF']:
                if key in data['totalNutrients']:
                    print(f"   {key}: {data['totalNutrients'][key]}")
                else:
                    print(f"   {key}: NOT FOUND")
        
        if 'ingredients' in data and len(data['ingredients']) > 0:
            print("\n3. 'ingredients[0].nutrients' found:")
            if 'nutrients' in data['ingredients'][0]:
                nutrients = data['ingredients'][0]['nutrients']
                for key in ['ENERC_KCAL', 'PROCNT', 'FAT', 'CHOCDF']:
                    if key in nutrients:
                        print(f"   {key}: {nutrients[key]}")
                    else:
                        print(f"   {key}: NOT FOUND")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_raw()