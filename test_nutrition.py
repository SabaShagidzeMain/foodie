import os
import django
from decouple import config
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foodie.settings')
django.setup()

from apps.recipes.services import NutritionService

def test_nutrition_api():
    """Test the Edamam API integration"""
    
    print("🔍 Testing Edamam Nutrition API (FIXED)...")
    print("-" * 50)
    
    # Check if credentials are set
    app_id = config('EDAMAM_APP_ID', default='')
    app_key = config('EDAMAM_APP_KEY', default='')
    
    if not app_id or not app_key:
        print("❌ ERROR: EDAMAM_APP_ID or EDAMAM_APP_KEY not found in .env file!")
        return
    
    print(f"✅ App ID found: {app_id[:5]}...")
    print(f"✅ App Key found: {app_key[:5]}...")
    print()
    
    # Initialize service
    nutrition_service = NutritionService()
    
    # Test ingredients
    test_ingredients = [
        "1 apple",
        "100g chicken breast",
        "2 eggs",
        "1 cup rice",
        "100g pasta"
    ]
    
    print("🧪 Testing with sample ingredients:")
    print("-" * 50)
    
    for ingredient in test_ingredients:
        print(f"\n📊 Testing: '{ingredient}'")
        
        # Use the service method (which now has the correct parsing)
        result = nutrition_service.get_ingredient_nutrition(ingredient)
        
        if result:
            print(f"   ✅ Success!")
            print(f"   Calories: {result.get('calories', 0):.1f} kcal")
            print(f"   Protein: {result.get('protein', 0):.1f}g")
            print(f"   Fat: {result.get('fat', 0):.1f}g")
            print(f"   Carbs: {result.get('carbs', 0):.1f}g")
            print(f"   Fiber: {result.get('fiber', 0):.1f}g")
        else:
            print(f"   ❌ Failed to get nutrition data")
    
    print("\n" + "=" * 50)
    print("🏁 Test complete!")

if __name__ == "__main__":
    test_nutrition_api()