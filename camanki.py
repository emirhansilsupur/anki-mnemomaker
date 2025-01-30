import sys
import os
import time
import random
# Add libs directory to Python path
libs_dir = os.path.join(os.path.dirname(__file__), "libs")
sys.path.insert(0, libs_dir)

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
import requests
from bs4 import BeautifulSoup
from typing import Dict, List

class MnemonicGenerator:
    def __init__(self, provider: str, api_key: str, model: str):
        if provider == "groq":
            self.llm = ChatGroq(temperature=0.7, api_key=api_key, model_name=model)
        elif provider == "openai":
            self.llm = ChatOpenAI(temperature=0.7, api_key=api_key, model=model)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an expert in creating memorable mnemonics and providing vocabulary insights.
                You understand that mnemonics are most effective when provided in the user's native language,
                while synonyms and antonyms should be in the target learning language.""",
                ),
                (
                    "human",
                    """Create a memorable mnemonic for the word '{word}'.
            Definition: {definition}

            Requirements:
            1. Create the mnemonic in {native_language} (user's native language)
            2. Make it easy to remember for {native_language} speakers
            3. Use culturally relevant word associations or stories that make sense to {native_language} speakers
            4. Keep it concise (max 2 sentences)
            5. Use simple language appropriate for a 5-year-old
            6. Connect clearly to the word's meaning
            7. Provide one synonym and one antonym in {target_language}

            Output format:
            - Mnemonic: (in {native_language})
            - Synonym: (in {target_language})
            - Antonym: (in {target_language}""",
                ),
            ]
        )

        self.chain = self.prompt | self.llm


    def create_mnemonic(
        self, 
        word: str, 
        definition: str, 
        native_language: str = "English",
        target_language: str = "English"
    ) -> dict:
        """Generate a mnemonic, synonym, and antonym for the given word"""
        response = self.chain.invoke({
            "word": word,
            "definition": definition,
            "native_language": native_language,
            "target_language": target_language
        })
        return self._parse_response(response.content.strip())