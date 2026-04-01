from langchain_google_genai import ChatGoogleGenerativeAI
from enum import Enum

class AvailableModels(str, Enum):
    GEMINI_3_1_FLASH_LITE = "gemini-3.1-flash-lite-preview"
    GEMINI_3_1_FLASH = "gemini-3.1-flash-preview"
    GEMINI_3_1 = "gemini-3.1-preview"
    GEMINI_2 = "gemini-2.0-flash-preview"

def get_llm(temperature: float = 0.0, model: AvailableModels = AvailableModels.GEMINI_3_1_FLASH_LITE):
    """
    Returns a fresh instance of the LLM. 
    It automatically finds GOOGLE_API_KEY in the environment.
    """
    return ChatGoogleGenerativeAI(
        model=model.value,
        temperature=temperature
    )