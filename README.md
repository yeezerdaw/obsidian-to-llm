# ObsidianGPT 🧠

**ObsidianGPT is an AI-powered assistant designed to supercharge your Obsidian vault, providing intelligent analysis, querying, and content generation capabilities directly within a user-friendly web interface.**

This project combines a FastAPI backend for interacting with your local Obsidian notes and an LLM (like one running in LM Studio), with a Streamlit frontend for intuitive user interaction.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Table of Contents

- [Features](#features)
- [Demo / Screenshots](#demo--screenshots)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Running the Application](#running-the-application)
- [Usage](#usage)
- [Contributing](#contributing)
  - [Ways to Contribute](#ways-to-contribute)
  - [Development Setup for Contributors](#development-setup-for-contributors)
  - [Pull Request Process](#pull-request-process)
  - [Code Style](#code-style)
- [Future Scope & Roadmap](#future-scope--roadmap)
- [License](#license)
- [Acknowledgements](#acknowledgements)

---

## Features

- **🔍 Find Notes:** Quickly search your Obsidian vault for notes by name or keyword.
- **❓ Query a Note:** Ask specific questions about the content of any note and get AI-generated answers.
- **⚙️ Process a Note:** Trigger AI analysis (e.g., summarization, key takeaways) for selected notes, with results saved back into your vault.
- **🔗 Analyze Connections:** Explore conceptual overlaps, contradictions, and synthesis points between two notes.
- **📅 Daily Note Toolkit:**
  - Automatically find or create daily notes.
  - Refresh daily notes with a predefined template.
  - Generate AI summaries for your daily activities and insights.
  - Restructure daily note content for better organization.
- **🤖 LLM Integration:** Leverages local LLMs via LM Studio (or any OpenAI-compatible API endpoint).
- **🕵️ File Monitoring (Optional):** Automatically process notes upon modification in your Obsidian vault using a watchdog.
- **🎨 User-Friendly Interface:** Built with Streamlit for easy interaction.

---

## Demo / Screenshots

<p align="center">
  <img src="https://github.com/yeezerdaw/obsidian-to-llm/raw/main/docs/ezgif.com-animated-gif-maker.gif" alt="ObsidianGPT Demo 1" width="700">
</p>

<p align="center">
  <img src="https://github.com/yeezerdaw/obsidian-to-llm/raw/main/docs/2.gif" alt="ObsidianGPT Demo 2" width="700">
</p>

---

## Tech Stack

- **Backend:**
  - Python
  - FastAPI (for the core API)
  - Uvicorn (ASGI server)
  - Requests (for calling LLM API)
  - Watchdog (for file system monitoring)
- **Frontend:**
  - Streamlit
- **LLM Interaction:**
  - Designed for LM Studio (or any OpenAI API compatible endpoint)
- **Development:**
  - Git & GitHub

---

## Project Structure

```

obsidiangpt-project/
├── backend/                  # FastAPI backend
│   ├── main.py              # FastAPI application logic
│   ├── config.json.template# Configuration template
│   └── ...                  # Additional backend modules
├── frontend-streamlit/      # Streamlit frontend
│   ├── streamlit\_app.py    # Streamlit UI
│   └── assets/             # Assets like images or CSS
│       └── style.css
├── .streamlit/              # Optional Streamlit config
│   └── config.toml
├── .gitignore
├── LICENSE
├── README.md
└── CONTRIBUTING.md

````

---

## Getting Started

Follow these instructions to get ObsidianGPT up and running on your local machine.

### Prerequisites

- Python 3.8 or higher
- Git
- LM Studio (or any OpenAI-compatible LLM server)
- An existing Obsidian vault

---

### Installation

```bash
git clone https://github.com/your-username/obsidiangpt-project.git
cd obsidiangpt-project

python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

pip install -r requirements.txt
````

---

### Configuration

1. Copy the template config and edit:

   ```bash
   cp backend/config.json.template backend/config.json
   ```

2. Edit `backend/config.json`:

   * Set `vault_path`, `llmstudio.api_url`, `llmstudio.model`
   * Configure `response_folder`, `excluded_folders`, `daily_notes`, etc.

3. (Optional) Customize Streamlit theme:

   ```toml
   # .streamlit/config.toml
   [theme]
   primaryColor="#00A1E0"
   backgroundColor="#1E1E1E"
   secondaryBackgroundColor="#252526"
   textColor="#E0E0E0"
   font="sans serif"
   ```

---

### Running the Application

1. **Start Backend:**

```bash
cd backend
python main.py
# Or:
# uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

2. **Start Frontend:**

```bash
cd frontend-streamlit
streamlit run streamlit_app.py
```

Access Streamlit at: [http://localhost:8501](http://localhost:8501)

---

## Usage

Use the Streamlit sidebar to:

* Browse or search notes
* Ask questions about a note
* Summarize or restructure notes
* Analyze relationships between notes
* Work with your daily notes

---

## Contributing

All contributions are welcome! See [`CONTRIBUTING.md`](CONTRIBUTING.md).

### Ways to Contribute

* Report bugs or request features via GitHub Issues
* Improve frontend UI/UX
* Add backend features (note parsing, NLP)
* Write documentation and guides
* Add or improve test coverage

### Code Style

* Follow [PEP 8](https://peps.python.org/pep-0008/)
* Use tools like Black and Flake8:

  ```bash
  black .
  flake8 .
  ```

---

## Future Scope & Roadmap

* [ ] Better chat interface (history, streaming)
* [ ] Ollama / Hugging Face LLM support
* [ ] Visual note graph in Streamlit
* [ ] Note tagging-based workflows
* [ ] Local semantic search
* [ ] Docker-based deployment
* [ ] Unit/integration testing

---

## License

Licensed under the [MIT License](LICENSE).

---

## Acknowledgements

* Inspired by the power of Obsidian and open-source LLMs
* Built with ❤️ using FastAPI and Streamlit

```

---

Let me know if you'd like this saved as a file or want help deploying this to your GitHub repo.
```
