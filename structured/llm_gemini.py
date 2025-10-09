# === llm_gemini.py ===
from google import genai
from google.genai import types
from config import API_KEY_GEMINI, SYSTEM_PROMPT

genai_client = genai.Client(vertexai=True, api_key=API_KEY_GEMINI)

def ask_gemini(history, visualizer):
    tools = [types.Tool(google_search=types.GoogleSearch())]
    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        top_p=0.95,
        max_output_tokens=2048,
        safety_settings=[
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF")
        ],
        tools=tools,
        system_instruction=[types.Part.from_text(text=SYSTEM_PROMPT)]
    )

    response_chunks = genai_client.models.generate_content_stream(
        model="gemini-2.5-flash-lite",
        contents=history,
        config=generate_content_config,
    )

    full_response = ""
    for chunk in response_chunks:
        if chunk.text:
            full_response += chunk.text

    return full_response.strip()
