# ObsidianGPT ✨🧠

**ObsidianGPT is an AI-powered assistant designed to supercharge your Obsidian vault, providing intelligent analysis, querying, and content generation capabilities directly within a user-friendly web interface.**

This project combines a FastAPI backend for interacting with your local Obsidian notes and an LLM (like one running in LM Studio), with a Streamlit frontend for intuitive user interaction.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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

## Features

- 🔍 **Find Notes** – Search your Obsidian vault by name or keyword.
- ❓ **Query a Note** – Ask questions about note content and get AI-generated answers.
- ⚙️ **Process a Note** – Summarize, extract takeaways, and insert results back into your notes.
- 🔗 **Analyze Connections** – Explore overlaps, contradictions, and synthesis across notes.
- 📅 **Daily Note Toolkit**
  - Automatically locate or generate daily notes.
  - Populate notes using a configurable template.
  - Summarize your day using AI.
  - Organize daily content more effectively.
- 🤖 **LLM Integration** – Compatible with LM Studio and OpenAI-like APIs.
- 🕵️ **Optional File Monitoring** – Auto-process modified notes using Watchdog.
- 🎨 **User-Friendly UI** – Built with Streamlit for simple interaction.

## Demo / Screenshots

*(Add GIFs or images here to showcase features visually)*

**Example:**

![ObsidianGPT Screenshot](path/to/your/screenshot.png)

## Tech Stack

**Backend:**
- Python
- FastAPI
- Uvicorn
- Watchdog
- Requests

**Frontend:**
- Streamlit

**LLM Integration:**
- LM Studio (or OpenAI-compatible endpoints)

## Project Structure

```

obsidiangpt-project/
├── backend/                     # FastAPI application
│   ├── main.py                 # Main FastAPI app logic
│   ├── config.json.template    # Template config for user setup
│   └── ...                     # Additional backend utilities
├── frontend-streamlit/         # Streamlit UI application
│   ├── streamlit\_app.py       # Main Streamlit logic
│   ├── assets/                # Optional: images, logos
│   └── style.css              # Optional: custom styling
├── .streamlit/                 # Streamlit theming config
│   └── config.toml
├── .gitignore
├── LICENSE
├── README.md
└── CONTRIBUTING.md

````

## Getting Started

### Prerequisites

- Python 3.8+
- Git
- LM Studio (or OpenAI API-compatible LLM server)
- An Obsidian vault on your system

### Installation

```bash
git clone https://github.com/your-username/obsidiangpt-project.git
cd obsidiangpt-project

# Set up virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
````

### Configuration

**Backend Setup:**

```bash
cp backend/config.json.template backend/config.json
```

Edit `backend/config.json`:

* `vault_path`: Path to your Obsidian vault
* `llmstudio.api_url`: e.g. `http://localhost:1234/v1/chat/completions`
* `llmstudio.model`: Name/ID of your model
* Adjust other fields as needed

**Streamlit UI Theme (Optional):**

Create `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#00A1E0"
backgroundColor = "#1E1E1E"
secondaryBackgroundColor = "#252526"
textColor = "#E0E0E0"
font = "sans serif"
```

### Running the Application

**Start the backend:**

```bash
cd backend
python main.py
# or
# uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

**Start the frontend:**

```bash
cd frontend-streamlit
streamlit run streamlit_app.py
```

Access the app at: `http://localhost:8501`

## Usage

* Select options in the Streamlit sidebar.
* Use “Find Notes” to locate content.
* Use “Query” to ask questions.
* Use “Process” to extract summaries, key points, etc.

## Contributing

We welcome all contributions! Please check [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.

### Ways to Contribute

* Report bugs or suggest enhancements via GitHub Issues.
* Add new backend or frontend features.
* Improve documentation or write tutorials.
* Optimize code or fix compatibility issues.

### Development Setup for Contributors

```bash
# Fork & clone your fork
git clone https://github.com/your-username/obsidiangpt-project.git

# Create a branch
git checkout -b feature/your-feature-name
```

Push changes and open a Pull Request.

### Pull Request Process

* Keep PRs focused and minimal.
* Describe your changes clearly in the PR.
* Update documentation as needed.
* Follow [SemVer](http://semver.org/) for version bumps.

### Code Style

Follow PEP 8. Use tools like:

```bash
pip install black flake8
black .
flake8 .
```

## Future Scope & Roadmap

* [ ] Full chat history in Streamlit
* [ ] Support for Ollama and Hugging Face local models
* [ ] Visual graphs for note connections
* [ ] Dockerized deployment
* [ ] Entity and topic extraction
* [ ] Smart content generation (e.g., flashcards)

## License

This project is licensed under the [MIT License](LICENSE).

```

