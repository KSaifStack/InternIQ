"""
AI Parser Module — Parses Markdown tables of internships into structured JSON data.
Supports both OpenAI and Google Gemini APIs.
"""
import os
import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# ==============================================================================
# 🔑 API KEY CONFIGURATION
# Set AI_API_KEY and AI_PROVIDER in your .env file (see .env.example).
# Never hardcode secrets here — they will be exposed in version control.
# ==============================================================================
HARDCODED_AI_PROVIDER = os.environ.get("AI_PROVIDER", "gemini")
HARDCODED_API_KEY = os.environ.get("AI_API_KEY", "")

SYSTEM_PROMPT = """
You are an expert data extractor. The user will provide a Markdown document (usually a GitHub README) containing a table of internship listings.
Your task is to extract ALL valid internship job listings and return them as a strict JSON array of objects.

Output FORMAT (strictly JSON array):
[
  {
    "company_name": "Company Name (string)",
    "title": "Job Title (string, e.g., 'Software Engineer Intern')",
    "location": "Location (string, e.g., 'San Francisco, CA' or 'Remote' or 'Multiple')",
    "application_url": "URL (string, MUST start with http/https)"
  }
]

RULES:
1. ONLY extract rows that represent actual jobs.
2. If a company name has a link (e.g. `[Company](url)`), extract just the name.
3. If a row says "↳" for the company, it means it's the SAME company as the previous row.
4. If an "Apply" link is provided, extract the raw URL. If not, omit the job or leave it blank.
5. Return ONLY valid JSON. No markdown backticks, no explanatory text.
6. If the payload is too large, extract at least the first 50 results.
"""

def parse_markdown_with_openai(markdown_text: str, api_key: str) -> List[Dict]:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Parse this markdown table:\n\n{markdown_text[:40000]}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        # Handle cases where the model returns {"jobs": [...] } instead of just an array
        if isinstance(data, dict):
            for val in data.values():
                if isinstance(val, list):
                    return val
            # Try to return the first list inside it
            return []
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        logger.error(f"OpenAI parsing failed: {e}")
        raise ValueError(f"OpenAI API Error: {e}")

def parse_markdown_with_gemini(markdown_text: str, api_key: str) -> List[Dict]:
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        # We use strict JSON schema for Gemini output
        model = genai.GenerativeModel('gemini-1.5-flash',
            generation_config={"response_mime_type": "application/json"})
        
        prompt = f"{SYSTEM_PROMPT}\n\nHere is the markdown to parse:\n\n{markdown_text[:40000]}"
        response = model.generate_content(prompt)
        
        data = json.loads(response.text)
        if isinstance(data, dict):
            for val in data.values():
                if isinstance(val, list):
                    return val
            return []
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        logger.error(f"Gemini parsing failed: {e}")
        raise ValueError(f"Gemini API Error: {e}")

def parse_github_repo_with_ai(markdown_text: str, provider: str, api_key: str) -> List[Dict]:
    """
    Main entrypoint for parsing markdown text with an AI provider.
    """
    if not markdown_text or not markdown_text.strip():
        raise ValueError("No markdown text provided.")
    
    provider_to_use = provider or HARDCODED_AI_PROVIDER
    key_to_use = api_key or HARDCODED_API_KEY

    if not provider_to_use or not key_to_use:
        raise ValueError("AI Provider and API Key must be provided (either via UI or hardcoded in backend/scrapers/ai_parser.py).")

    if provider_to_use.lower() == "openai":
        return parse_markdown_with_openai(markdown_text, key_to_use)
    elif provider_to_use.lower() == "gemini":
        return parse_markdown_with_gemini(markdown_text, key_to_use)
    else:
        raise ValueError(f"Unsupported AI provider: {provider_to_use}")
