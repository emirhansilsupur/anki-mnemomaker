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
    
    def _parse_response(self, response: str) -> dict:
        result = {"mnemonic": "", "synonym": "", "antonym": ""}
        for line in response.split("\n"):
            line = line.strip()
            if line.startswith("- Mnemonic:"):
                result["mnemonic"] = line.split(":", 1)[1].strip()
            elif line.startswith("- Synonym:"):
                result["synonym"] = line.split(":", 1)[1].strip()
            elif line.startswith("- Antonym:"):
                result["antonym"] = line.split(":", 1)[1].strip()
        return result
    
    def get_word_data(word: str, dict_url: str) -> Dict:
        """Get word data from Cambridge Dictionary"""
        try:
            url = f"https://dictionary.cambridge.org/dictionary/{dict_url}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Referer": "https://dictionary.cambridge.org/",
                "Accept-Language": "en-US,en;q=0.9",
            }
            time.sleep(random.uniform(2, 5))
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # New existence check
            entry_body = soup.find(class_="entry-body")
            dictionary_entry = soup.find(class_="dictionary-entry")
            
            # If neither main content structure exists, return None
            if not entry_body and not dictionary_entry:
                return None
            
            result = {"word": word, "structure": [], "entries": [], "pronunciation": None}

            structures = soup.find(class_="dpos")
            if structures:
                result["structure"].append(structures.text.strip())

            ipa_pronunciation = soup.find(class_="ipa dipa")
            if ipa_pronunciation:
                result["pronunciation"] = ipa_pronunciation.text.strip()

            for def_block in soup.find_all(class_="def-block"):
                entry = {"definition": None, "translation": None, "examples": []}

                definition = def_block.find(class_="def")
                translation = def_block.find(class_="trans")
                examples = def_block.find_all(class_="eg")

                if definition:
                    entry["definition"] = definition.text.strip()
                if translation:
                    entry["translation"] = translation.text.strip()
            
                if examples:
                    entry["examples"].extend([ex.text.strip() for ex in examples])

                if entry["definition"] or entry["translation"]:  # Only add if there's content
                    result["entries"].append(entry)    

                

            other_examples = []
            if soup.find_all(class_="degs"):
                for examp in soup.find_all(class_="degs"):
                    deg_examples = examp.find_all(class_="deg")
                    if deg_examples:
                        other_examples.extend([ex.text.strip() for ex in deg_examples])
            

            if other_examples:
                result["other_examples"] = other_examples[:1]
            
            return result if result["entries"] else None
        except requests.RequestException as e:
            raise Exception(f"Cannot access Cambridge Dictionary: {str(e)}")
