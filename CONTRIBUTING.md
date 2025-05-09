# Contributing to ObsidianGPT ✨🧠

First off, thank you for considering contributing to ObsidianGPT! We welcome contributions from everyone and appreciate your help in making this project better. Whether it's reporting a bug, proposing a new feature, improving documentation, or writing code, your input is valuable.

Please take a moment to review this document to understand how you can contribute.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Enhancements](#suggesting-enhancements)
  - [Your First Code Contribution](#your-first-code-contribution)
  - [Pull Requests](#pull-requests)
- [Development Setup](#development-setup)
- [Coding Guidelines](#coding-guidelines)
  - [Git Commit Messages](#git-commit-messages)
  - [Python Styleguide](#python-styleguide)
  - [Frontend (Streamlit) Notes](#frontend-streamlit-notes)
- [Testing](#testing)
- [Community & Communication](#community--communication)

## Code of Conduct

This project and everyone participating in it is governed by a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior. *(You'll need to create a CODE_OF_CONDUCT.md file - a common one is the Contributor Covenant: https://www.contributor-covenant.org/)*

## How Can I Contribute?

### Reporting Bugs

If you encounter a bug, please help us by reporting it!

1.  **Check if the bug has already been reported:** Search the [GitHub Issues](https://github.com/your-username/obsidiangpt-project/issues) to see if someone else has already reported the same issue.
2.  **If it's a new bug:** Open a new issue. Be sure to include:
    *   A clear and descriptive title.
    *   A detailed description of the bug, including steps to reproduce it.
    *   What you expected to happen and what actually happened.
    *   Your environment details (e.g., OS, Python version, Streamlit version, FastAPI version, Browser, LM Studio version, LLM model used).
    *   Any relevant error messages or screenshots.

### Suggesting Enhancements

We love to hear your ideas for new features or improvements!

1.  **Check if the enhancement has already been suggested:** Search the [GitHub Issues](https://github.com/your-username/obsidiangpt-project/issues) to see if your idea is already being discussed.
2.  **If it's a new suggestion:** Open a new issue. Provide:
    *   A clear and descriptive title.
    *   A detailed explanation of the proposed enhancement.
    *   Why this enhancement would be useful.
    *   Any potential implementation ideas (optional).

### Your First Code Contribution

Unsure where to begin?
*   Look for issues tagged with `good first issue` or `help wanted`. These are usually good starting points.
*   You can also start by improving documentation, adding tests, or fixing small bugs.
*   Don't hesitate to ask questions on an issue if you need clarification before starting work!

### Pull Requests

We use Pull Requests (PRs) for code contributions.

1.  **Fork the repository** on GitHub.
2.  **Clone your fork locally:** `git clone https://github.com/your-username/obsidiangpt-project.git`
3.  **Create a new branch** for your changes from the `main` branch: `git checkout -b feature/my-awesome-feature` or `fix/bug-description`. Please use a descriptive branch name.
4.  **Make your changes** locally.
5.  **Commit your changes** with clear, descriptive commit messages (see [Git Commit Messages](#git-commit-messages)).
6.  **Push your branch** to your fork: `git push origin feature/my-awesome-feature`.
7.  **Open a Pull Request** from your forked repository's branch to the `main` branch of the original `your-username/obsidiangpt-project` repository.
8.  **In your PR description:**
    *   Clearly describe the changes you've made.
    *   Link to any relevant GitHub issues (e.g., "Closes #123" or "Fixes #456").
    *   Mention any new dependencies or configuration changes.
9.  Your PR will be reviewed. Be prepared to discuss your changes and make adjustments if requested.

## Development Setup

Please refer to the [Getting Started > Installation](#installation) and [Configuration](#configuration) sections in the main `README.md` file for instructions on setting up the development environment.

Ensure you have a working local setup where you can run both the FastAPI backend and the Streamlit frontend.

## Coding Guidelines

### Git Commit Messages

*   Use the present tense ("Add feature" not "Added feature").
*   Use the imperative mood ("Move cursor to..." not "Moves cursor to...").
*   Limit the first line to 72 characters or less.
*   Reference issues and pull requests liberally after the first line.
*   Consider using [Conventional Commits](https://www.conventionalcommits.org/) for more structured messages (e.g., `feat: add dark mode toggle`, `fix: resolve daily note date parsing`).

### Python Styleguide

*   Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code.
*   We recommend using a code formatter like [Black](https://github.com/psf/black) and a linter like [Flake8](https://flake8.pycqa.org/en/latest/).
    ```bash
    pip install black flake8
    black .
    flake8 .
    ```
    Run these before committing your changes.
*   Include type hints where appropriate.
*   Write clear and concise comments where necessary.

### Frontend (Streamlit) Notes

*   Try to keep the UI clean and intuitive.
*   When adding new UI elements or workflows, consider the user experience.
*   If adding significant CSS, discuss whether it should be inline, in the main `<style>` block, or in a separate `assets/style.css` file.

## Testing

*(This section is a placeholder. If you add tests, expand it.)*

Currently, automated testing is minimal. We encourage contributions that add:
*   **Unit tests** for backend logic (e.g., using `pytest`).
*   **Integration tests** for API endpoints.
*   If possible, simple tests for Streamlit app logic (can be challenging).

When submitting a PR with new features or bug fixes, please consider if tests are applicable and try to include them.

## Community & Communication

*   **GitHub Issues:** For bug reports, feature requests, and discussions related to specific tasks.
*   **GitHub Discussions:** (If you enable it on your repository) For broader questions, ideas, and community chat.
*   *(If you create a Discord/Slack/etc., list it here)*

We aim to be responsive and create a welcoming environment for all contributors. Thank you for your interest in improving ObsidianGPT!
