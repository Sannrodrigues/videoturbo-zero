import json, re


def _extract_json(text: str):
    text = text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.I)
    text = re.sub(r'\s*```$', '', text)
    start, end = text.find('{'), text.rfind('}')
    if start >= 0 and end > start:
        text = text[start:end+1]
    return json.loads(text)


def generate_plan(api_key: str, topic: str, language: str, duration_sec: int, style: str):
    from google import genai
    client = genai.Client(api_key=api_key)
    words = max(55, int(duration_sec * 2.2))
    prompt = f'''Create a video plan in {language} about: {topic}
Target duration: {duration_sec} seconds (~{words} spoken words).
Style: {style}.
Return ONLY valid JSON with this exact schema:
{{
  "title":"...",
  "narration":"complete narration text",
  "scenes":[
    {{"text":"short narration portion", "search_query":"English stock-video search phrase"}}
  ]
}}
Rules: 4-10 scenes, factual language, no fabricated statistics, each search_query must be visual and suitable for Pexels stock footage.'''
    # Gemini 2.5 Flash was retired by the API; use the currently suggested Flash model.
    response = client.models.generate_content(model='gemini-3.6-flash', contents=prompt)
    return _extract_json(response.text)
