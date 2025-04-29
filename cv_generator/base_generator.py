from openai import OpenAI
import os
from dotenv import load_dotenv

class BaseGenerator:
    def __init__(self, api_key=None):
        """Initialize the base generator with OpenAI client."""
        if api_key is None:
            load_dotenv()
            api_key = os.environ.get("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("OpenAI API key is required. Set it in environment variables or pass it directly.")
            
        self.client = OpenAI(api_key=api_key)
        self.context = {}

    def _clean_text(self, text):
        """Clean text by removing unwanted characters and formatting."""
        if not text:
            return ""
            
        # Remove leading dashes/bullets
        if text.startswith('-'):
            text = text[1:].strip()
        if text.startswith('•'):
            text = text[1:].strip()
            
        # Remove trailing period
        if text.endswith('.'):
            text = text[:-1]
            
        return text.strip()

    def _process_response(self, response):
        """Process OpenAI response and return cleaned lines."""
        if not response or not response.choices:
            return []
            
        content = response.choices[0].message.content
        lines = [self._clean_text(line) for line in content.splitlines()]
        return [line for line in lines if line] 