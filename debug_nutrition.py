import os
import django
from decouple import config
import requests
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foodie.settings')
django.setup()

def debug_api():
    """Debug the Edamam API response"""
    
    app_id = config('EDAMAM_APP_ID', default='')
    app_key = config('EDAMAM_APP_KEY', default='')
    
    print("🔍 Debugging Edamam API Response...")
    print("-" * 50)
    
    # Test with a simple ingredient
    ingredient = "1 apple"
    url = "https://api.edamam.com/api/nutrition-data"
    params = {
        'app_id': app_id,
        'app_key': app_key,
        'ingr': ingredient
    }
    
    print(f"📊 Testing: '{ingredient}'")
    print(f"URL: {url}")
    print(f"Params: {params}")
    print()
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print()
        
        data = response.json()
        print("Full Response:")
        print(json.dumps(data, indent=2))
        
        # Check different possible structures
        print("\n" + "=" * 50)
        print("🔍 Checking for nutrition data in different locations:")
        
        # Check totalNutrients
        if 'totalNutrients' in data:
            print("✅ Found 'totalNutrients'")
            nutrients = data['totalNutrients']
            for key, value in nutrients.items():
                print(f"   {key}: {value.get('label', '')} - {value.get('quantity', 0)} {value.get('unit', '')}")
        
        # Check nutrients
        if 'nutrients' in data:
            print("✅ Found 'nutrients'")
            print(data['nutrients'])
        
        # Check calories
        if 'calories' in data:
            print(f"✅ Calories: {data['calories']}")
        
        # Check totalWeight
        if 'totalWeight' in data:
            print(f"✅ Total Weight: {data['totalWeight']}g")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_api()