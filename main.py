from aqt import mw
from aqt.qt import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QComboBox,
    QPushButton,
    QLabel,
    QAction,
    QMessageBox,
    QTextEdit,
)
from aqt.utils import showInfo, qconnect
from .camanki import MnemonicGenerator, get_word_data, create_anki_note


# Load config using Anki's addon manager
config = mw.addonManager.getConfig(__name__)


class CambridgeDictionaryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Define language configurations
        self.language_config = {
            "turkish": {
                "can_speak": ["turkish"],
                "can_learn": ["english"],
                "dict_format": "english-turkish" 
                }, # semi-bilingual, fixed format
            "english": {
                "can_speak": ["english"],
                "can_learn": ["french", "spanish", "german", "italian", "portuguese"],
                "dict_format": "{target}-english",  
            },
           
            "french": {
                "can_speak": ["french"],
                "can_learn": ["english"],
                "dict_format": "{target}-french", 
            },
            "spanish": {
                "can_speak": ["spanish"],
                "can_learn": ["english"],
                "dict_format": "{target}-spanish",  
            },
            "german": {
                "can_speak": ["german"],
                "can_learn": ["english"],
                "dict_format": "{target}-german",
            },
            "italian": {
                "can_speak": ["italian"],
                "can_learn": ["english"],
                "dict_format": "{target}-italian",
            },
            "portuguese": {
                "can_speak": ["portuguese"],
                "can_learn": ["english"],
                "dict_format":  "{target}-portuguese",
            },
        }

        # Display names for languages
        self.language_names = {
            "turkish": "Turkish",
            "english": "English",
            "french": "French",
            "spanish": "Spanish",
            "german": "German",
            "italian": "Italian",
            "portuguese": "Portuguese",
        }

        # Define llm parameters
        self.llm_providers = ["Groq", "OpenAI"]
        self.llm_models = {
            "Groq": ["llama-3.3-70b-versatile", "deepseek-r1-distill-llama-70b"],
            "OpenAI": ["o1-mini", "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
        }

        self.setup_ui()
        self.mnemonic_generator = None
        self.initialize_llm()