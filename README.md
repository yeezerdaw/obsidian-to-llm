# ObsidianGPT ✨🧠

**ObsidianGPT is an AI-powered assistant designed to supercharge your Obsidian vault, providing intelligent analysis, querying, and content generation capabilities directly within a user-friendly web interface.**

This project combines a FastAPI backend for interacting with your local Obsidian notes and an LLM (like one running in LM Studio), with a Streamlit frontend for intuitive user interaction.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
<!-- Optional: Add more badges like build status, stars, forks if you set them up -->

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

*   **🔍 Find Notes:** Quickly search your Obsidian vault for notes by name or keyword.
*   **❓ Query a Note:** Ask specific questions about the content of any note and get AI-generated answers.
*   **⚙️ Process a Note:** Trigger AI analysis (e.g., summarization, key takeaways) for selected notes, with results saved back into your vault.
*   **🔗 Analyze Connections:** Explore conceptual overlaps, contradictions, and synthesis points between two notes.
*   **📅 Daily Note Toolkit:**
    *   Automatically find or create daily notes.
    *   Refresh daily notes with a predefined template.
    *   Generate AI summaries for your daily activities and insights.
    *   Restructure daily note content for better organization.
*   **🤖 LLM Integration:** Leverages local LLMs via LM Studio (or any OpenAI-compatible API endpoint).
*   **🕵️ File Monitoring (Optional):** Automatically process notes upon modification in your Obsidian vault using a watchdog.
*   **🎨 User-Friendly Interface:** Built with Streamlit for easy interaction.

## Demo / Screenshots

*(It's highly recommended to add a GIF or a few screenshots here showing your application in action. This significantly helps potential users and contributors understand the project.)*

**Example:**

A quick look at the ObsidianGPT interface:
![ObsidianGPT Screenshot 1](path/to/your/screenshot1.png)
*(Add more if you have them)*

## Tech Stack

*   **Backend:**
    *   Python
    *   FastAPI (for the core API)
    *   Uvicorn (ASGI server)
    *   Requests (for calling LLM API)
    *   Watchdog (for file system monitoring)
*   **Frontend:**
    *   Streamlit
*   **LLM Interaction:**
    *   Designed for LM Studio (or any OpenAI API compatible endpoint)
*   **Development:**
    *   Git & GitHub

## Project Structure
