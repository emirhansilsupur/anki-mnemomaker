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

    def setup_ui(self):
        self.setWindowTitle("MnemoMaker - AI-Powered Flashcard Creator")
        self.setMinimumWidth(500)
        self.apply_theme_styles()

        layout = QVBoxLayout()

        # LLM Selection
        llm_layout = QHBoxLayout()
        provider_layout = QVBoxLayout()
        provider_layout.addWidget(QLabel("AI Service:"))
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(self.llm_providers)
        provider_layout.addWidget(self.provider_combo)

        model_layout = QVBoxLayout()
        model_layout.addWidget(QLabel("AI Model:"))
        self.model_combo = QComboBox()
        model_layout.addWidget(self.model_combo)

        llm_layout.addLayout(provider_layout)
        llm_layout.addLayout(model_layout)
        layout.addLayout(llm_layout)

        
        # Language Selection
        lang_layout = QHBoxLayout()
        source_layout = QVBoxLayout()
        source_layout.addWidget(QLabel("Native Language:"))
        self.source_combo = QComboBox()
        self.source_combo.addItems(
            [self.language_names[lang] for lang in self.language_config]
        )
        source_layout.addWidget(self.source_combo)

        target_layout = QVBoxLayout()
        target_layout.addWidget(QLabel("Target Language:"))
        self.target_combo = QComboBox()
        target_layout.addWidget(self.target_combo)

        lang_layout.addLayout(source_layout)
        lang_layout.addLayout(target_layout)
        layout.addLayout(lang_layout)

        # Word Input
        word_layout = QHBoxLayout()
        self.word_label = QLabel("Word in English:")
        self.word_input = QLineEdit()
        self.word_input.setPlaceholderText("Enter word")
        word_layout.addWidget(self.word_label)
        word_layout.addWidget(self.word_input)
        layout.addLayout(word_layout)

        # Deck Selection
        deck_layout = QHBoxLayout()
        self.deck_combo = QComboBox()
        self.update_deck_list()
        deck_layout.addWidget(QLabel("Deck:"))
        deck_layout.addWidget(self.deck_combo)
        layout.addLayout(deck_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Create Card")
        self.cancel_btn = QPushButton("Close")
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        # Connections
        qconnect(self.source_combo.currentIndexChanged, self.update_target_languages)
        qconnect(self.target_combo.currentTextChanged, self.update_word_label)
        qconnect(self.provider_combo.currentTextChanged, self.update_models)
        qconnect(self.add_btn.clicked, self.create_card)
        qconnect(self.cancel_btn.clicked, self.reject)

        self.update_target_languages()
        self.update_models()