import requests
import json
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

# 1. API Keys Configuration
SERPER_API_KEY = "4dc18602c17b81736f1218effc7e86c8b4a74129"
GEMINI_API_KEY = "AIzaSyC1xS7zAhlZSJ2PGRjO42nRS-ZCnLRx5g" 

# Gemini Configuration
genai.configure(api_key=GEMINI_API_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

app = FastAPI()

# Standard Global Headers configuration for Vercel
HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS, PUT, PATCH, DELETE",
    "Access-Control-Allow-Headers": "X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version",
    "Access-Control-Allow-Credentials": "true"
}

@app.options("/{rest_of_path:path}")
def preflight_handler():
    """Handles browser preflight OPTIONS requests gracefully"""
    return JSONResponse(content={"status": "ok"}, headers=HEADERS)

@app.get("/")
def read_root():
    return JSONResponse(content={"status": "success", "message": "Local SEO API Server is operational"}, headers=HEADERS)

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
            return JSONResponse(status_code=404, content={"success": False, "detail": "Business not found on Google Maps"}, headers=HEADERS)
            
        business = maps_data["maps"][0]  # Selection logic array index wrap up
        
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
        
        return JSONResponse(content={
            "success": True,
            "name": business.get('title'),
            "rating": business.get('rating', 'N/A'),
            "total_reviews": business.get('ratingCount', 0),
            "address": business.get('address', 'N/A'),
            "ai_report": ai_response.text
        }, headers=HEADERS)
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "detail": str(e)}, headers=HEADERS)
