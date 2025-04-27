# Second Brain

Second Brain is a personal knowledge management system that integrates with your Obsidian vault and uses a language model to analyze, query, and process your notes. It acts as a personal assistant, helping you extract insights, analyze connections, and perform daily reviews.

## Features

- **Automatic Note Processing**: Automatically processes and analyzes notes in your Obsidian vault.
- **Query Notes**: Ask questions about specific notes and get detailed answers.
- **Analyze Connections**: Compare two notes to find overlaps, contradictions, and synthesis points.
- **Daily Reviews**: Automatically generate daily reviews for your notes.
- **Customizable**: Configure excluded folders, daily note templates, and language model parameters.

## Requirements

- Python 3.10 or higher
- Dependencies listed in `requirements.txt`

## Installation

1. Clone the repository:
   ```bash
   git clone [https://github.com/yeezerdaw/second-brain.git](https://github.com/yeezerdaw/second-brain.git)
   cd second-brain
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure the application:
   Edit the `config.json` file to match your setup (e.g., `vault_path`, `llmstudio` API settings).

## Usage

### Start the Second Brain

Run the main script to start the Second Brain:

```bash
python second_brain.py
```

### Interactive Query Mode

To interactively query your notes:

```bash
python second_brain.py --query
```

**Example query:**

```
What is the main idea of the note on "AI in Healthcare"?
```

### Daily Review

To process a daily review for today:

```bash
python second_brain.py --daily
```

To process a daily review for a specific date:

```bash
python second_brain.py --daily YYYY-MM-DD
```

**Example Daily Review Output**

A daily note might look like this:

```markdown
# Daily Note - Monday 2025-04-28

## Highlights

- Key concept 1
- Key concept 2

## Tasks
- [ ] Review AI research notes
- [ ] Follow up on project status
```

## Configuration

The application is configured via the `config.json` file. Key settings include:

```json
{
  "vault_path": "/path/to/your/vault",
  "llmstudio": {
    "api_url": "http://localhost:1234/v1/chat/completions",
    "model": "llama-3.2-1b-instruct",
    "context_window": 8000,
    "temperature": 0.3,
    "max_tokens": 500
  },
  "response_folder": "🤖 SecondBrain",
  "daily_notes": {
    "enabled": true,
    "folder": "Journal/Daily logs",
    "file_formats": ["{full_date}.md"],
    "date_formats": {
      "day": "%d",
      "full_date": "%Y-%m-%d"
    },
    "default_template": "# Daily Note - {weekday} {full_date}\n\n## Highlights\n\n## Tasks\n- [ ] "
  },
  "system_prompt": "You are an AI second brain...",
  "excluded_folders": [".obsidian", "Templates", "🤖 SecondBrain", "node_modules"],
  "watchdog": {
    "debounce_seconds": 2
  }
}
```

Key settings explained:

- `vault_path`: Path to your Obsidian vault.
- `llmstudio`: Configuration for the language model API.
- `response_folder`: Folder where processed outputs are saved.
- `daily_notes`: Settings for daily note processing.
- `excluded_folders`: Folders to exclude from processing.

## Logs

Logs are saved in the `logs/processing.log` file. You can monitor this file for detailed information about the application's operations.

## Web Service (Work in Progress)

We are currently working on a web-based interface for Second Brain. This will allow users to interact with their notes and the language model through a browser-based chat interface. Stay tuned for updates!

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.
