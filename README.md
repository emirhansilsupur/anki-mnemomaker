# MnemoMaker - AI-Powered Flashcard Creator

## Description
MnemoMaker is an advanced Anki add-on that transforms vocabulary learning by automatically creating comprehensive flashcards. It integrates with Cambridge Dictionary and AI services to generate beautifully formatted cards featuring definitions, examples, translations, and AI-powered mnemonics.

## What are Mnemonics?
A mnemonic device is a learning technique that aids information retention by creating meaningful associations. These memory devices help connect new information with existing knowledge in your long-term memory, making learning more efficient and memorable.


<img src="https://raw.githubusercontent.com/emirhansilsupur/anki-mnemomaker/main/assets/mnemonic_ui.PNG" alt="mm" style="width: 50%; margin-right: 10px;">
<div style="display: flex;">
  <img src="https://raw.githubusercontent.com/emirhansilsupur/anki-mnemomaker/main/assets/mnemonic_pr.PNG" alt="mm2" style="width: 50%;">
</div>

## Features

### Multi-Language Support
Supports multiple language pairs including: 
-	English → French, Spanish, German, Italian, Portuguese
-	Turkish, French, Spanish, German, Italian, Portuguese → English

### AI-Powered Mnemonics
- Generate culturally-relevant memory hooks in your native language
- Smart word associations based on your cultural context
- Automatic synonym and antonym suggestions
- Multiple AI provider support (Groq and OpenAI)

### Rich Content Integration
- Comprehensive definitions from Cambridge Dictionary
- Native language translations
- Contextual usage examples
- IPA pronunciation guides
- Detailed word structure and grammar information

## Prerequisites
**Important**: Valid API credentials are required for mnemonic generation. You'll need an API key from either:
- Groq: Get your free [API key](https://console.groq.com/keys)
- OpenAI: Get your [API key](https://platform.openai.com/api-keys) (paid)

## Installation Guide

1. **Add-on Installation**
   1. In Anki, go to Tools → Add-ons → Get Add-ons and enter the installation code [from here.](https://ankiweb.net/shared/info/756388520?cb=1738266247932).
   2. Restart Anki.


2. **AI Service Configuration**
   - Go to Tools → MnemoMaker → Config
   - Enter your chosen API credentials

## How to Use

1. Open MnemoMaker from Tools → MnemoMaker - AI-Powered Flashcard Creator
2. Configure your settings:
   - Choose AI service and model
   - Select native and target languages
   - Pick destination deck
3. Enter the word you want to learn
4. Click "Create Card"
