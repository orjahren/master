import os


from google import genai


def get_api_key() -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY environment variable not set.")
    return api_key


client = genai.Client(api_key=get_api_key())


def api_is_up():
    return True  # Assume Google never dies...


# TODO: Use decorator for asserting API liveness? Or standard assertion??
def execute_gemini_model(model_name: str, prompt: str) -> str:

    response = client.models.generate_content(
        model=model_name or "gemini-2.5-flash",
        contents=prompt
    )

    return response.text
