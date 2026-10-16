import requests
import json
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# 1. API Keys Configuration
SERPER_API_KEY = "4dc18602c17b81736f1218effc7e86c8b4a74129"
GEMINI_API_KEY = "AIzaSyC1xS7zAhlZSJ2PGRjO42nRS-ZCnLRx5g" 

# Gemini Configuration
genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

app = FastAPI()

# Live hosting aur WordPress connection ke liye CORS bypass setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Vercel Root Handler: Yeh check karne ke liye ke server live hai ya nahi
@app.get("/")
def read_root():
    return {"status": "success", "message": "Local SEO API Server is operational"}

@app.get("/api/v1/audit")
def audit_local_business(business_name: str, city: str):
    url = "https://serper.dev"
    payload = json.dumps({"q": f"{business_name} in {city}"})
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, headers=headers, data=payload)
        maps_data = response.json()
        
        if "maps" not in maps_data or len(maps_data["maps"]) == 0:
            raise HTTPException(status_code=404, detail="Business not found on Google Maps")
            
        business = maps_data["maps"][0]  # Array index selection standard
        
        prompt = f"""
        You are an expert Local SEO Consultant. Analyze the following Google Maps business profile and provide a professional audit report in simple English.
        
        Business Name: {business.get('title')}
        Rating: {business.get('rating', 'N/A')}
        Total Reviews: {business.get('ratingCount', 0)}
        Category: {business.get('category', 'Not Specified')}
        Address: {business.get('address', 'N/A')}
        
        Format the response in clean HTML tags (like <h3>, <p>, <ul>, <li>) without markdown code blocks.
        Include:
        1. An assessment of their current rating and local presence.
        2. A perfectly optimized 750-character GMB Business Description including local keywords based on their category.
        3. Two template review replies (one for 5-star, one for a negative review) that use keywords for SEO.
        """
        
        ai_response = ai_model.generate_content(prompt)
        
        return {
            "success": True,
            "name": business.get('title'),
            "rating": business.get('rating', 'N/A'),
            "total_reviews": business.get('ratingCount', 0),
            "address": business.get('address', 'N/A'),
            "ai_report": ai_response.text
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
