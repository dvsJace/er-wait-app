from langchain_google_genai import ChatGoogleGenerativeAI

def get_llm(temperature: float = 0.0, model: str = "gemini-2.5-flash"):
    """
    Returns a fresh instance of the LLM. 
    It automatically finds GOOGLE_API_KEY in the environment.
    """
    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature
    )