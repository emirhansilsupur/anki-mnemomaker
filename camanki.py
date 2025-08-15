import sys
import os
import time
import random
# Add OS-aware libs directory to Python path
# Prefer vendor/libs/<os>/, fallback to vendor/libs/
base_dir = os.path.dirname(__file__)
libs_base = os.path.join(base_dir, "libs")

plat = sys.platform
if plat.startswith("win"):
    sub = "windows"
elif plat == "darwin":
    sub = "darwin"
else:
    # linux and others
    sub = "linux"

candidate_paths = [
    os.path.join(libs_base, sub),
    libs_base,
]
for p in candidate_paths:
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)

# Modern platform-aware pydantic loading with graceful fallbacks
def _setup_pydantic_environment():
    """Setup pydantic with multiple fallback strategies for cross-platform compatibility"""
    import importlib
    import warnings
    
    # Strategy 1: Try bundled platform-specific version first
    pydantic_available = False
    error_details = []
    
    try:
        import pydantic_core
        import pydantic
        pydantic_available = True
        return True
    except Exception as e:
        error_details.append(f"Bundled pydantic failed: {e}")
    
    # Strategy 2: Try system pydantic (Anki might have it)
    try:
        # Temporarily remove our libs from path to try system version
        original_paths = sys.path.copy()
        for p in candidate_paths:
            if p in sys.path:
                sys.path.remove(p)
        
        import pydantic_core
        import pydantic
        
        # If successful, add our libs back but prioritize system pydantic
        for p in reversed(candidate_paths):
            if os.path.isdir(p) and p not in sys.path:
                sys.path.append(p)  # append instead of insert
        
        pydantic_available = True
        return True
        
    except Exception as e:
        error_details.append(f"System pydantic failed: {e}")
        # Restore original path
        sys.path = original_paths
    
    # Strategy 3: Try lightweight installation for current Python version
    target_dir = candidate_paths[0] if os.path.isdir(candidate_paths[0]) else candidate_paths[1]
    try:
        _install_compatible_pydantic(target_dir)
        importlib.invalidate_caches()
        import pydantic_core
        import pydantic
        pydantic_available = True
        return True
    except Exception as e:
        error_details.append(f"Auto-install failed: {e}")
    
    # If all strategies fail, provide detailed error guidance
    python_info = f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    platform_info = f"Platform: {sys.platform}"
    
    error_msg = f"""
MnemoMaker Compatibility Issue:

The addon requires 'pydantic' but couldn't load it on your system.
System Info: {python_info}, {platform_info}

Troubleshooting options:
1. Install pydantic manually in Anki's Python environment:
   {sys.executable} -m pip install --upgrade pydantic

2. If using Anki from package managers (Snap, Flatpak), permissions may be restricted.
   Try installing Anki directly from https://apps.ankiweb.net/

Failed attempts:
""" + "\n".join(f"- {detail}" for detail in error_details)
    
    raise RuntimeError(error_msg)

def _install_compatible_pydantic(target_dir: str):
    """Lightweight pydantic installation compatible with current Python version"""
    import subprocess
    import platform
    
    os.makedirs(target_dir, exist_ok=True)
    
    # Determine the right pydantic-core version for current Python
    py_version = f"cp{sys.version_info.major}{sys.version_info.minor}"
    
    # Platform-specific wheel tags
    if sys.platform.startswith("win"):
        if platform.machine().lower() in ["amd64", "x86_64"]:
            platform_tag = "win_amd64"
        else:
            platform_tag = "win32"
    elif sys.platform == "darwin":
        if platform.machine() == "arm64":
            platform_tag = "macosx_11_0_arm64"
        else:
            platform_tag = "macosx_10_9_x86_64"
    else:  # linux and others
        if platform.machine() in ["x86_64", "amd64"]:
            platform_tag = "linux_x86_64"
        elif platform.machine() in ["aarch64", "arm64"]:
            platform_tag = "linux_aarch64"
        else:
            platform_tag = "linux_x86_64"  # fallback
    
    # Use latest compatible versions
    pydantic_version = "2.10.6"  # pure Python, universal
    pydantic_core_version = "2.27.2"  # may need platform-specific wheel
    
    exe = sys.executable
    if exe.lower().endswith("pythonw.exe"):
        candidate = os.path.join(os.path.dirname(exe), "python.exe")
        if os.path.isfile(candidate):
            exe = candidate
    
    # First try to install pydantic-core with specific platform tag
    cmd = [
        exe, "-m", "pip", "install", 
        "--no-deps", "--only-binary", ":all:", "--disable-pip-version-check",
        "--no-input", "--no-color", "--target", target_dir,
        f"pydantic-core=={pydantic_core_version}",
        f"pydantic=={pydantic_version}",
        "typing-extensions>=4.6.0",
    ]
    
    env = os.environ.copy()
    env.update({
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        "PYTHONUTF8": "1",
        "PIP_NO_WARN_SCRIPT_LOCATION": "1"
    })
    
    subprocess.check_call(cmd, env=env, timeout=120)

# Initialize pydantic with fallback strategies and determine available features
PYDANTIC_AVAILABLE = False
LANGCHAIN_AVAILABLE = False

# Diagnostic information
def _log_platform_info():
    """Log platform and environment information for debugging"""
    import platform
    info = [
        f"Python: {sys.version}",
        f"Platform: {sys.platform}",
        f"Architecture: {platform.machine()}",
        f"Libs directory: {libs_base}",
        f"Candidate paths: {candidate_paths}"
    ]
    print("MnemoMaker Platform Info:")
    for line in info:
        print(f"  {line}")

try:
    _log_platform_info()  # Always log platform info
    _setup_pydantic_environment()
    PYDANTIC_AVAILABLE = True
    print("  Pydantic: ✓ Available")
    
    # Try importing LangChain components
    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_groq import ChatGroq
        from langchain_openai import ChatOpenAI
        LANGCHAIN_AVAILABLE = True
        print("  LangChain: ✓ Available (using enhanced mode)")
    except ImportError as e:
        # LangChain requires pydantic but may still fail to import
        print(f"  LangChain: ✗ Not available: {e}")
        print("  Using HTTP API fallback mode")
        LANGCHAIN_AVAILABLE = False
        
except Exception as e:
    print(f"  Pydantic: ✗ Not available: {e}")
    print("  LangChain: ✗ Not available")
    print("  Using simplified HTTP-only mode")
    PYDANTIC_AVAILABLE = False
    LANGCHAIN_AVAILABLE = False

import requests
from bs4 import BeautifulSoup
from typing import Dict, List
import json


class MnemonicGenerator:
    def __init__(self, provider: str, api_key: str, model: str):
        self.provider = provider
        self.api_key = api_key
        self.model = model
        
        if LANGCHAIN_AVAILABLE:
            # Use LangChain if available (preferred method)
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
            self.use_langchain = True
        else:
            # Fallback to direct HTTP API calls
            self.use_langchain = False
            if provider not in ["groq", "openai"]:
                raise ValueError(f"Unsupported provider: {provider}")
            
        self.system_prompt = """You are an expert in creating memorable mnemonics and providing vocabulary insights.
You understand that mnemonics are most effective when provided in the user's native language,
while synonyms and antonyms should be in the target learning language."""

    def create_mnemonic(
        self, 
        word: str, 
        definition: str, 
        native_language: str = "English",
        target_language: str = "English"
    ) -> dict:
        """Generate a mnemonic, synonym, and antonym for the given word"""
        
        if self.use_langchain:
            # Use LangChain implementation
            response = self.chain.invoke({
                "word": word,
                "definition": definition,
                "native_language": native_language,
                "target_language": target_language
            })
            return self._parse_response(response.content.strip())
        else:
            # Use direct HTTP API calls
            user_prompt = f"""Create a memorable mnemonic for the word '{word}'.
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
- Antonym: (in {target_language}"""

            if self.provider == "groq":
                response_text = self._call_groq_api(user_prompt)
            elif self.provider == "openai":
                response_text = self._call_openai_api(user_prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
            return self._parse_response(response_text)
    
    def _call_groq_api(self, user_prompt: str) -> str:
        """Direct API call to Groq"""
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def _call_openai_api(self, user_prompt: str) -> str:
        """Direct API call to OpenAI"""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"]

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
        time.sleep(random.uniform(3, 5))
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
