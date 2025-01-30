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

    def create_anki_note(
        word_data: Dict,
        deck_name: str,
        mnemonic: str,
        synonym: str,
        antonym: str,
        night_mode: bool,
    ) -> Dict:
        """Creates a theme-aware Anki note with dynamic styling"""

        # Theme configuration
        if night_mode:
            card_bg = "#2c2c2c"
            heading_color = "#D8DEE9"
            idx_color = "#8F9CB5"
            pronunciation_color = "#808080"
            structure_color = "#81A1C1"
            mnemonic_bg = "#363636"
            mnemonic_border = "#81A1C1"
            definition_bg = "#3B4252"
            definition_border = "#8F9CB5"
            text_primary = "#D8DEE9"
            text_secondary = "#808080"
            example_border = "#4C566A"
            translation_color = "#2d82c6"
            box_border = "#363636"
            synonym_bg = "#363636"
            synonym_border = "#81A1C1"
            antonym_bg = "#363636"
            antonym_border = "#BF616A"
        else:
            card_bg = "#FFFFFF"
            heading_color = "#2C3E50"
            idx_color = "#2C3E50"
            pronunciation_color = "#7F8C8D"
            structure_color = "#95A5A6"
            mnemonic_bg = "#F0F9FF"
            mnemonic_border = "#3498DB"
            definition_bg = "#F8F9FA"
            definition_border = "#E5E7EB"
            text_primary = "#2C3E50"
            text_secondary = "#7F8C8D"
            example_border = "#E5E7EB"
            translation_color = "#3498DB"
            box_border = "#E5E7EB"
            synonym_bg = "#E6F4EA"
            synonym_border = "#4CAF50"
            antonym_bg = "#FFEBEE"
            antonym_border = "#BF616A"

        front = f"""<div style="text-align: center; padding: 20px; background-color: {card_bg};">
            <h1 style="font-size: 2.5em; color: {heading_color}; margin-bottom: 10px;">{word_data['word']}</h1>
            <div style="color: {pronunciation_color}; font-family: monospace; margin-bottom: 10px;">/{word_data.get('pronunciation', '')}/</div>
            <div style="color: {structure_color}; font-style: italic;">{', '.join(word_data.get('structure', []))}</div>
        </div>"""

        back = f"""<div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: {card_bg};">
            <!-- Mnemonic Section -->
            <div style="background-color: {mnemonic_bg}; border-left: 4px solid {mnemonic_border}; padding: 15px; margin-bottom: 20px; border-radius: 4px;">
                <div style="color: {mnemonic_border}; font-weight: bold; margin-bottom: 5px;">💡 Memory Hook</div>
                <div style="font-style: italic; color: {text_primary};">{mnemonic}</div>
            </div>

            <!-- Synonym & Antonym Section -->
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;">
                <div style="background-color: {synonym_bg}; border: 1px solid {synonym_border}; padding: 10px; border-radius: 4px;">
                    <div style="display: flex; flex-direction: column; justify-content: center; height: 100%;">
                        <div style="color: {synonym_border}; font-weight: bold; margin-bottom: 5px;">🔗 Synonym</div>
                        <div style="color: {text_primary};">{synonym}</div>
                    </div>
                </div>
                <div style="background-color: {antonym_bg}; border: 1px solid {antonym_border}; padding: 10px; border-radius: 4px;">
                    <div style="display: flex; flex-direction: column; justify-content: center; height: 100%;">
                        <div style="color: {antonym_border}; font-weight: bold; margin-bottom: 5px;">🧭 Antonym</div>
                        <div style="color: {text_primary};">{antonym}</div>
                    </div>
                </div>
            </div>
            <!-- Definitions Section -->
            <div style="display: grid; gap: 20px;">"""

        for idx, entry in enumerate(word_data.get("entries", []), 1):
            back += f"""
                <div style="border: 1px solid {box_border}; padding: 15px; border-radius: 8px;">
                    <div style="display: flex; gap: 10px; align-items: baseline; margin-bottom: 10px;">
                        <span style="background-color: {idx_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8em;">#{idx}</span>
                        <div style="font-weight: 500; color: {heading_color};">{entry['definition']}</div>
                    </div>
                    
                    <div style="color: {translation_color}; margin-bottom: 10px; padding-left: 25px;">
                        {entry['translation']}
                    </div>"""

            if entry.get("examples"):
                back += (
                    """<div style="margin-top: 10px; padding-left: 25px;">
                    <div style="color: %s; font-size: 0.9em; margin-bottom: 5px;">Examples:</div>
                    <ul style="list-style-type: none; padding: 0; margin: 0;">"""
                    % text_secondary
                )
                for example in entry["examples"]:
                    back += f"""<li style="margin-bottom: 5px; color: {text_primary}; padding-left: 15px; border-left: 2px solid {example_border};">
                        {example}
                    </li>"""
                back += "</ul></div>"

            back += "</div>"

        back += """</div></div>"""

        return {
            "deckName": deck_name,
            "modelName": "Basic",
            "fields": {"Front": front, "Back": back},
            "options": {"allowDuplicate": True},
            "tags": ["cambridge_dictionary"],
        }