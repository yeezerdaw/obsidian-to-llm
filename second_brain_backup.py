import os
import sys
import time
import json
import logging
import threading
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime

class SecondBrain:
    def __init__(self, config):
        self.config = config
        self.setup_logging()
        self.setup_folders()
        logging.info(f"Loaded model: {self.config['llmstudio']['model']}")

    def setup_logging(self):
        os.makedirs('logs', exist_ok=True)
        logging.basicConfig(
            filename='logs/processing.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def setup_folders(self):
        self.response_folder = os.path.join(
            self.config['vault_path'],
            self.config['response_folder']
        )
        os.makedirs(self.response_folder, exist_ok=True)

    def should_process(self, note_path):
        rel_path = os.path.relpath(note_path, self.config['vault_path'])
        return not any(
            f in rel_path.split(os.sep) 
            for f in self.config.get('excluded_folders', [])
        )

    def process_note(self, note_path):
        if not self.should_process(note_path):
            return

        try:
            with open(note_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if len(content) < 25:
                return

            logging.info(f"Processing: {os.path.basename(note_path)}")
            analysis = self.query_llmstudio(content)
            self.save_output(note_path, analysis)

        except Exception as e:
            logging.error(f"Error processing {note_path}: {str(e)}")

    def query_llmstudio(self, content):
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": self.config['llmstudio']['model'],
            "messages": [
                {
                    "role": "system",
                    "content": self.config['system_prompt']
                },
                {
                    "role": "user",
                    "content": content[:self.config['llmstudio']['context_window']]
                }
            ],
            "temperature": self.config['llmstudio']['temperature'],
            "max_tokens": self.config['llmstudio']['max_tokens'],
            "stream": False
        }

        try:
            response = requests.post(
                self.config['llmstudio']['api_url'],
                headers=headers,
                json=payload,
                timeout=90
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            logging.error(f"API Error: {str(e)}")
            return f"⚠️ Analysis failed: {str(e)}"

    def save_output(self, note_path, analysis):
        note_name = os.path.basename(note_path).replace('.md', '')
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        rel_path = os.path.relpath(note_path, self.config['vault_path'])
        
        response_content = f'''# Second Brain Analysis
**Original Note:** [[{rel_path.replace('.md', '')}]]

## 🔍 Key Analysis
{analysis}

_Processed at {timestamp}_'''


        output_file = f"SB_{note_name}_{timestamp}.md"
        output_path = os.path.join(self.response_folder, output_file)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(response_content)
        
        logging.info(f"Created analysis: {output_file}")

    # ===== QUERY METHODS =====
    def query_about_note(self, note_name, question):
        note_path = self.find_note(note_name)
        if not note_path:
            return f"Note '{note_name}' not found"
        
        try:
            with open(note_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Safely get context window with fallback
            context_window = self.config['llmstudio'].get('context_window', 4000)
            
            prompt = f"""Analyze this note and answer the question:
            
            Note: {os.path.basename(note_path)}
            Question: {question}
            
            Content:
            {content[:context_window]}
            """
            
            return self.query_llmstudio(prompt)
        
        except Exception as e:
            return f"Error: {str(e)}"

    def analyze_connections(self, note1, note2):
        """Compare two notes and find connections"""
        note1_path = os.path.join(self.config['vault_path'], f"{note1}.md")
        note2_path = os.path.join(self.config['vault_path'], f"{note2}.md")
        
        try:
            with open(note1_path, 'r', encoding='utf-8') as f1, \
                 open(note2_path, 'r', encoding='utf-8') as f2:
                content = f"Note 1 ({note1}):\n{f1.read()}\n\nNote 2 ({note2}):\n{f2.read()}"
            
            prompt = f"""Analyze connections between these notes:
            
            {content[:self.config['llmstudio']['context_window']]}
            
            1. List conceptual overlaps
            2. Identify contradictions
            3. Suggest synthesis points
            """
            
            return self.query_llmstudio(prompt)
        except FileNotFoundError as e:
            return f"Note not found: {str(e)}"

    def daily_review(self):
        """Ultra-reliable daily note processor with complete error handling"""
        try:
            # 1. Load configuration with multiple fallback layers
            dn_config = self.config.get('daily_notes', {})
            if not dn_config.get('enabled', True):
                return "Daily notes are disabled in config"
                
            # 2. Prepare all date formats
            today = datetime.now()
            date_vars = {
                'day': today.strftime(dn_config.get('date_formats', {}).get('day', '%d')),
                'full_date': today.strftime(dn_config.get('date_formats', {}).get('full_date', '%Y-%m-%d')),
                'weekday': today.strftime('%A'),
                'month': today.strftime('%B'),
                'year': today.strftime('%Y')
            }
            
            logging.debug(f"Date variables: {date_vars}")
            
            # 3. Build all possible file paths
            daily_folder = os.path.join(self.config['vault_path'], 
                                      dn_config.get('folder', 'Daily Notes'))
            possible_files = []
            
            for fmt in dn_config.get('file_formats', ["{full_date}.md"]):
                try:
                    possible_files.append(fmt.format(**date_vars))
                except KeyError:
                    continue  # Skip invalid formats
                    
            # 4. Find existing note (check all possibilities)
            note_path = None
            for filename in possible_files:
                test_path = os.path.join(daily_folder, filename)
                if os.path.exists(test_path):
                    note_path = test_path
                    break
                    
            # 5. Create note if needed (with multiple safeguards)
            if not note_path:
                os.makedirs(daily_folder, exist_ok=True)
                default_filename = f"DAY-{date_vars['day']}.md"
                note_path = os.path.join(daily_folder, default_filename)
                
                template = dn_config.get('default_template', 
                                       "# Daily Note\n\n## Highlights\n\n## Tasks\n- [ ] ")
                
                logging.debug(f"Default template: {template}")
                
                with open(note_path, 'w', encoding='utf-8') as f:
                    f.write(template.format(**date_vars))
                logging.info(f"Created new daily note: {default_filename}")
            
                # 6. Process the note (with content validation)
            with open(note_path, 'r+', encoding='utf-8') as f:
                content = f.read()
                
                if not content.strip():
                    content = "# Empty note\n" + content
                    f.seek(0)
                    f.write(content)
                    f.truncate()
                
                prompt = f"""Analyze today's daily note:
                
                {content[:8000]}
                
                Provide:
                1. Key accomplishments (bullet points)
                2. Unfinished tasks (markdown checklist)
                3. Suggested priorities for tomorrow"""
                
                analysis = self.query_llmstudio(prompt)
                
                # Only append if analysis is new
                if "## AI Review" not in content:
                    f.write(f"\n\n## AI Review\n{analysis}")
            
            return f"Successfully processed: {os.path.basename(note_path)}"
            
        except Exception as e:
            error_msg = f"Daily review error: {type(e).__name__} - {str(e)}"
            logging.error(error_msg)
            return f"⚠️ {error_msg}\nPlease check your daily notes configuration"

    def find_note(self, search_query):
        """Find notes recursively through all subfolders with flexible matching"""
        matches = []
        search_normalized = search_query.lower().replace(" ", "").replace("-", "").replace("_", "")
        
        for root, _, files in os.walk(self.config['vault_path']):
            # Skip excluded folders
            if any(excl in root for excl in self.config.get('excluded_folders', [])):
                continue
                
            for file in files:
                if file.endswith('.md'):
                    file_normalized = file.lower().replace(" ", "").replace("-", "").replace("_", "").replace(".md", "")
                    
                    # Flexible matching:
                    # 1. Exact match (case insensitive)
                    # 2. Partial match
                    # 3. Acronym match
                    if (search_normalized == file_normalized or 
                        search_normalized in file_normalized or
                        "".join([word[0] for word in search_query.split()]).lower() in file_normalized):
                        
                        full_path = os.path.join(root, file)
                        matches.append(full_path)
        
        # Handle results
        if not matches:         
            print(f"\n🔍 No matches found for '{search_query}' in:")
            print(f"Vault: {self.config['vault_path']}")
            print("\nTry these similar notes:")
            os.system(f"find '{self.config['vault_path']}' -name '*.md' | grep -i '{search_query[:5]}' | head -5")
            return None
        elif len(matches) == 1:
            return matches[0]
        else:
            print(f"\n🔍 Found {len(matches)} matches:")
            for i, match in enumerate(matches[:5], 1):
                rel_path = os.path.relpath(match, self.config['vault_path'])
                print(f"{i}. {rel_path}")
            choice = input("Select (1-5) or 'c' to cancel: ")
            return matches[int(choice)-1] if choice.isdigit() else None

class ObsidianHandler(FileSystemEventHandler):
    def __init__(self, brain, debounce_sec):
        self.brain = brain
        self.debounce_sec = debounce_sec
        self.debounce_timers = {}

    def on_modified(self, event):
        if (event.is_directory or 
            not event.src_path.endswith('.md') or 
            not os.path.exists(event.src_path)):
            return

        if event.src_path in self.debounce_timers:
            self.debounce_timers[event.src_path].cancel()

        timer = threading.Timer(
            self.debounce_sec,
            self._process_with_retry,
            [event.src_path]
        )
        self.debounce_timers[event.src_path] = timer
        timer.start()
        logging.info(f"🔄 Detected change: {os.path.basename(event.src_path)}")

    def _process_with_retry(self, path, retries=3):
        try:
            if os.path.exists(path):
                self.brain.process_note(path)
            if path in self.debounce_timers:
                del self.debounce_timers[path]
        except Exception as e:
            if retries > 0:
                logging.warning(f"Retrying {path} ({retries} left)...")
                time.sleep(1)
                self._process_with_retry(path, retries-1)
            else:
                logging.error(f"Failed to process {path}: {str(e)}")

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

def interactive_query(brain):
    """Command line interactive query mode"""
    print("\n" + "="*40)
    print("Second Brain Query Mode")
    print("="*40)
    while True:
        try:
            print("\nOptions:")
            print("1. Query about a note")
            print("2. Compare two notes")
            print("3. Daily review")
            print("4. Exit")
            
            choice = input("Select option (1-4): ").strip()
            
            if choice == "1":
                note_name = input("Note name (without .md): ").strip()
                question = input("Your question: ").strip()
                print("\n" + "="*40)
                print(brain.query_about_note(note_name, question))
                
            elif choice == "2":
                note1 = input("First note name: ").strip()
                note2 = input("Second note name: ").strip()
                print("\n" + "="*40)
                print(brain.analyze_connections(note1, note2))
                
            elif choice == "3":
                print("\n" + "="*40)
                print(brain.daily_review())
                
            elif choice == "4":
                break
                
            print("="*40)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    config = load_config()
    brain = SecondBrain(config)
    
    # Command line mode detection
    if len(sys.argv) > 1:
        if sys.argv[1] == "--query":
            interactive_query(brain)
            sys.exit(0)
        elif sys.argv[1] == "--daily":
            print(brain.daily_review())
            sys.exit(0)
    
    # Start file watcher if no special mode
    event_handler = ObsidianHandler(brain, config['watchdog']['debounce_seconds'])
    observer = Observer()
    observer.schedule(event_handler, path=config['vault_path'], recursive=True)
    observer.start()
    
    try:
        print(f"🔮 Second Brain active | Watching: {config['vault_path']}")
        print(f"Model: {config['llmstudio']['model']} | Ctrl+C to exit")
        print("Tip: Run with --query for interactive mode")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
