import os


from google import genai

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"


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
        model=model_name or DEFAULT_GEMINI_MODEL,
        contents=prompt
    )

    return response.text


def print_model_info(model_id: str):
    try:
        model_info = client.models.get(model=model_id)

        print(f"Information for model: {model_id}")
        print(model_info)

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":

    print_model_info(DEFAULT_GEMINI_MODEL)
