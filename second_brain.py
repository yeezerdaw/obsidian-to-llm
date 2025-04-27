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

    def daily_review(self, date_str=None):
        """
        Processes the daily note for a given date (or today if None).
        Finds/creates the note, analyzes it via LLM, and inserts/appends
        the review based on configuration (marker, overwrite, heading).

        Args:
            date_str (str, optional): Date in 'YYYY-MM-DD' format. Defaults to None (today).

        Returns:
            str: A message indicating success or failure.
        """
        try:
            # 1. Load configuration with defaults
            dn_config = self.config.get('daily_notes', {})
            if not dn_config.get('enabled', True):
                logging.warning("Daily notes feature disabled in config.")
                return "Daily notes are disabled in config"

            # --- Configuration values ---
            review_heading = dn_config.get('review_heading', '## AI Review')
            append_marker = dn_config.get('append_marker') # Can be None
            overwrite_review = dn_config.get('overwrite_review', False)
            analysis_prompt_template = dn_config.get('analysis_prompt', "Analyze this daily note:\n\n{content}")
            default_template = dn_config.get('default_template', "# Daily Note\n\n## Highlights\n\n## Tasks\n- [ ] ")
            daily_folder_rel = dn_config.get('folder', 'Daily Notes')
            file_formats = dn_config.get('file_formats', ["{full_date}.md"])
            date_format_config = dn_config.get('date_formats', {})
            # --- Determine context window for daily notes ---
            llm_config = self.config.get('llmstudio', {})
            daily_context_window = dn_config.get('context_window') # Might be None
            global_context_window = llm_config.get('context_window', 4000) # Default global
            context_window = daily_context_window if isinstance(daily_context_window, int) else global_context_window

            # 2. Determine target date
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.now()
            except ValueError:
                logging.error(f"Invalid date format provided: {date_str}. Use YYYY-MM-DD.")
                return f"⚠️ Invalid date format: {date_str}. Use YYYY-MM-DD."

            # 3. Prepare date formats for the target date
            date_vars = {
                'day': target_date.strftime(date_format_config.get('day', '%d')),
                'full_date': target_date.strftime(date_format_config.get('full_date', '%Y-%m-%d')),
                'weekday': target_date.strftime('%A'),
                'month': target_date.strftime('%B'),
                'year': target_date.strftime('%Y')
            }
            logging.debug(f"Processing daily review for: {date_vars['full_date']}")
            logging.debug(f"Date variables: {date_vars}")

            # 4. Build and find the note path
            daily_folder_abs = os.path.join(self.config['vault_path'], daily_folder_rel)
            note_path = None
            possible_files = []
            for fmt in file_formats:
                try:
                    filename = fmt.format(**date_vars)
                    possible_files.append(filename)
                    test_path = os.path.join(daily_folder_abs, filename)
                    if os.path.exists(test_path):
                        note_path = test_path
                        logging.info(f"Found existing daily note: {filename}")
                        break # Found the note
                except KeyError as e:
                    logging.warning(f"Skipping invalid daily note format '{fmt}': Missing key {e}")
                    continue

            # 5. Create note if it doesn't exist
            if not note_path:
                os.makedirs(daily_folder_abs, exist_ok=True)
                # Use the first valid format for the new filename, or a fallback
                try:
                    new_filename = file_formats[0].format(**date_vars)
                except KeyError:
                     # Fallback if the first format is also bad (should be rare)
                    new_filename = f"{date_vars['full_date']}.md"
                    logging.warning(f"Primary daily note format invalid, using fallback: {new_filename}")

                note_path = os.path.join(daily_folder_abs, new_filename)
                try:
                    note_content = default_template.format(**date_vars)
                except KeyError as e:
                    logging.warning(f"Error formatting template for {new_filename}: Missing key {e}. Using raw template.")
                    note_content = default_template # Use template string as is

                with open(note_path, 'w', encoding='utf-8') as f:
                    f.write(note_content)
                logging.info(f"Created new daily note: {new_filename}")
                # If newly created, no need to analyze empty template immediately?
                # Maybe return a specific message or analyze anyway if needed.
                # For now, we proceed to analyze it.

            # 6. Read note content
            try:
                with open(note_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                 logging.error(f"Error reading daily note {note_path}: {str(e)}")
                 return f"⚠️ Error reading daily note: {os.path.basename(note_path)}"

            # Handle potentially empty notes gracefully before sending to LLM
            if not content.strip():
                content = "# Empty Note\n" # Give LLM *something*
                logging.warning(f"Daily note {os.path.basename(note_path)} was empty.")

            # 7. Query LLM for analysis
            # Use the specific prompt template from config
            prompt = analysis_prompt_template.format(content=content[:context_window], **date_vars)

            logging.info(f"Querying LLM for daily review of {os.path.basename(note_path)}")
            analysis = self.query_llmstudio(prompt) # Use the existing method

            if analysis.startswith("⚠️"): # Check if LLM query failed
                 logging.error(f"LLM analysis failed for {note_path}: {analysis}")
                 return f"⚠️ LLM analysis failed for {os.path.basename(note_path)}"

            # 8. Update the note with the analysis (Insert/Append/Overwrite)
            new_review_section = f"{review_heading}\n{analysis.strip()}"

            try:
                with open(note_path, 'r+', encoding='utf-8') as f:
                    content = f.read()
                    original_content = content # Keep a copy for comparison if needed
                    marker_found = False
                    heading_found = False
                    # Use word boundaries (\b) for more precise heading matching if needed,
                    # but simple escape is often sufficient for headings starting a line.
                    heading_pattern = re.compile(f"^{re.escape(review_heading)}$", re.MULTILINE)
                    heading_match = heading_pattern.search(content)

                    if heading_match:
                        heading_found = True
                        logging.debug(f"Found existing heading '{review_heading}'")

                    # --- Strategy 1: Marker takes precedence ---
                    if append_marker and append_marker in content:
                        logging.debug(f"Found append marker '{append_marker}'")
                        # Replace the line containing the marker
                        lines = content.splitlines()
                        new_lines = []
                        marker_replaced = False
                        for line in lines:
                            # Be careful with strip(): ensure marker isn't just part of another word
                            # Check if the marker is the main content of the line
                            if append_marker in line and line.strip() == append_marker:
                                new_lines.append(new_review_section)
                                marker_replaced = True
                                logging.info(f"Replacing marker in {os.path.basename(note_path)}")
                            else:
                                new_lines.append(line)
                        # If marker was found but not replaced (e.g., commented out differently)
                        if marker_replaced:
                            content = "\n".join(new_lines)
                            marker_found = True
                        else:
                            logging.warning(f"Append marker '{append_marker}' found in content but not on its own line. Marker replacement skipped.")
                            # Proceed as if marker wasn't found for replacement purposes
                            marker_found = False

                    # --- Strategy 2: Overwrite if enabled and heading exists (and marker wasn't used/replaced) ---
                    elif overwrite_review and heading_found and not marker_found:
                        logging.info(f"Overwriting existing review section in {os.path.basename(note_path)}")
                        # Find the start of the section (the heading itself)
                        start_index = heading_match.start()
                        # Find the end of the section (next heading of same/lower level, or EOF)
                        # This regex looks for the next line starting with '#', respecting heading level
                        next_heading_level = len(review_heading.split(' ')[0]) # Count '#'
                        next_heading_pattern_str = f"^#{'{'}{next_heading_level}{'}'}[^#]" # e.g., ^##[^#]
                        # Or simply find next ## heading if review_heading is ##
                        if review_heading.startswith('## '):
                             next_heading_pattern_str = r"^##\s"
                        elif review_heading.startswith('# '):
                             next_heading_pattern_str = r"^#\s" # Next H1 or H2 etc. will stop it
                        else: # Non-standard heading
                            next_heading_pattern_str = r"^##?\s" # Default to stopping at H2 or H1

                        next_heading_pattern = re.compile(next_heading_pattern_str, re.MULTILINE)

                        next_match = next_heading_pattern.search(content, pos=heading_match.end()) # Search *after* current heading
                        end_index = next_match.start() if next_match else len(content)

                        # Ensure we don't leave excessive newlines
                        pre_content = content[:start_index].rstrip()
                        post_content = content[end_index:].lstrip()
                        # Add appropriate spacing
                        content = f"{pre_content}\n\n{new_review_section}\n\n{post_content}".strip() + "\n" # Ensure trailing newline


                    # --- Strategy 3: Append if heading doesn't exist (and marker wasn't used/replaced) ---
                    elif not heading_found and not marker_found:
                        logging.info(f"Appending new review section to {os.path.basename(note_path)}")
                        content = content.rstrip() + f"\n\n{new_review_section}\n"

                    # --- Strategy 4: Do Nothing (if heading exists, overwrite=False, no marker used/replaced) ---
                    elif heading_found and not overwrite_review and not marker_found:
                         logging.info(f"Review section already exists and overwrite is false. No changes made to {os.path.basename(note_path)}.")
                         # No need to write if content hasn't changed
                         if content == original_content:
                              return f"Review already exists (overwrite=false): {os.path.basename(note_path)}"


                    # --- Write changes back to the file ---
                    if content != original_content:
                         f.seek(0)
                         f.write(content)
                         f.truncate()
                         logging.info(f"Successfully updated daily note: {os.path.basename(note_path)}")
                         return f"Successfully processed: {os.path.basename(note_path)}"
                    else:
                        # This path might be reached if marker reported but not found, and append fallback happened but heading existed etc.
                        # Or simply if no change was needed (Strategy 4).
                        logging.info(f"No effective changes needed for {os.path.basename(note_path)}.")
                        return f"No changes needed for: {os.path.basename(note_path)}"


            except Exception as e:
                logging.error(f"Error writing updated daily note {note_path}: {str(e)}")
                return f"⚠️ Error writing updated daily note: {os.path.basename(note_path)}"


        except Exception as e:
            # Catch-all for unexpected errors during setup/finding file
            error_msg = f"Unexpected daily review error: {type(e).__name__} - {str(e)}"
            logging.exception(error_msg) # Log full traceback for unexpected errors
            return f"⚠️ {error_msg}\nPlease check logs and configuration."
        
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
            print("3. Daily review (today or specific date)")
            print("4. Exit")

            choice = input("Select option (1-4): ").strip()

            if choice == "1":
                note_name = input("Note name (without .md): ").strip()
                question = input("Your question: ").strip()
                print("\n" + "="*40)
                print("Processing...")
                print(brain.query_about_note(note_name, question))

            elif choice == "2":
                note1 = input("First note name: ").strip()
                note2 = input("Second note name: ").strip()
                print("\n" + "="*40)
                print("Processing...")
                print(brain.analyze_connections(note1, note2))

            elif choice == "3":
                date_input = input("Enter date (YYYY-MM-DD) or leave blank for today: ").strip()
                print("\n" + "="*40)
                print("Processing...")
                if not date_input:
                    print(brain.daily_review())
                else:
                    print(brain.daily_review(date_str=date_input))

            elif choice == "4":
                break

            print("="*40)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
            logging.exception("Error during interactive query")

if __name__ == "__main__":
    try: # Add top-level error handling for startup
        config = load_config()
        brain = SecondBrain(config)

        # Command line mode detection
        if len(sys.argv) > 1:
            if sys.argv[1] == "--query":
                interactive_query(brain)
                sys.exit(0)
            elif sys.argv[1] == "--daily":
                date_arg = sys.argv[2] if len(sys.argv) > 2 else None
                print(brain.daily_review(date_str=date_arg))
                sys.exit(0)

        # Start file watcher if no special mode
        event_handler = ObsidianHandler(brain, config['watchdog']['debounce_seconds'])
        observer = Observer()
        observer.schedule(event_handler, path=config['vault_path'], recursive=True)
        observer.start()

        print(f"🔮 Second Brain active | Watching: {config['vault_path']}")
        print(f"Model: {config['llmstudio']['model']} | Ctrl+C to exit")
        print("Tip: Run with --query for interactive mode or --daily [YYYY-MM-DD] for specific review")
        while True:
            time.sleep(1)
    except FileNotFoundError as e:
         print(f"Error: Configuration file 'config.json' not found or vault path invalid.")
         print(e)
         logging.error("Startup failed: config.json or vault path not found.")
         sys.exit(1)
    except KeyError as e:
         print(f"Error: Missing key in 'config.json': {e}")
         logging.error(f"Startup failed: Missing key in config.json: {e}")
         sys.exit(1)
    except KeyboardInterrupt:
        if 'observer' in locals() and observer.is_alive():
            observer.stop()
            observer.join()
        print("\nExiting Second Brain.")
    except Exception as e:
         print(f"An unexpected error occurred: {e}")
         logging.exception("Unexpected error during startup or main loop.")
         if 'observer' in locals() and observer.is_alive():
             observer.stop()
             observer.join()
         sys.exit(1)

    if 'observer' in locals() and observer.is_alive():
         observer.join() # Wait for observer thread to finish
