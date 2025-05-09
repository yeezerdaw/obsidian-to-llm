import os
import sys
import time
import json
import logging
import threading
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime, date
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Body, Path, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
import re # For daily summary update

# --- Configuration Loading ---
def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error("Configuration file 'config.json' not found.")
        raise
    except json.JSONDecodeError:
        logging.error("Error decoding 'config.json'.")
        raise

CONFIG = load_config()

# --- SecondBrain Class (Adapted for new config) ---
class SecondBrain:
    def __init__(self, config):
        self.config = config
        self.setup_folders()
        logging.info(f"Loaded model: {self.config['llmstudio']['model']}")

    def setup_logging(self):
        os.makedirs('logs', exist_ok=True)
        log_file = self.config.get("log_file", 'logs/processing_api.log')
        logging.basicConfig(
            filename=log_file,
            level=self.config.get("log_level", "INFO").upper(),
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(console_handler)
        logging.getLogger().setLevel(self.config.get("log_level", "INFO").upper())

    def setup_folders(self):
        self.response_folder = os.path.join(
            self.config['vault_path'],
            self.config['response_folder']
        )
        os.makedirs(self.response_folder, exist_ok=True)

        # Ensure daily notes folder exists if enabled
        daily_notes_config = self.config.get('daily_notes', {})
        if daily_notes_config.get('enabled', False):
            daily_notes_base_rel = daily_notes_config.get('folder', 'Daily Notes') # Default if not specified
            daily_notes_base_abs = os.path.join(self.config['vault_path'], daily_notes_base_rel)
            os.makedirs(daily_notes_base_abs, exist_ok=True)


    def should_process(self, note_path):
        rel_path = os.path.relpath(note_path, self.config['vault_path'])
        return not any(
            f in rel_path.split(os.sep)
            for f in self.config.get('excluded_folders', [])
        )

    def process_note(self, note_path_relative: str):
        full_note_path = os.path.join(self.config['vault_path'], note_path_relative)

        if not os.path.exists(full_note_path):
            logging.error(f"Note not found for processing: {full_note_path}")
            raise FileNotFoundError(f"Note not found: {full_note_path}")

        if not self.should_process(full_note_path):
            logging.info(f"Skipping processing (excluded folder): {os.path.basename(full_note_path)}")
            return {"message": "Skipped processing due to exclusion rules.", "note_path": full_note_path}

        try:
            with open(full_note_path, 'r', encoding='utf-8') as f:
                content = f.read()

            min_content_length = self.config.get("min_processing_length", 25)
            if len(content) < min_content_length:
                logging.info(f"Skipping (too short, less than {min_content_length} chars): {os.path.basename(full_note_path)}")
                return {"message": f"Skipped processing, content too short (min {min_content_length} chars).", "note_path": full_note_path}

            logging.info(f"Processing: {os.path.basename(full_note_path)}")
            analysis = self.query_llmstudio(content)
            output_file_rel_path = self.save_output(full_note_path, analysis)
            return {
                "message": "Note processed successfully.",
                "original_note": note_path_relative,
                "analysis_file": output_file_rel_path
            }
        except Exception as e:
            logging.error(f"Error processing {full_note_path}: {str(e)}")
            raise RuntimeError(f"Error processing {full_note_path}: {str(e)}") from e

    def query_llmstudio(self, content_to_query: str, system_prompt_override: Optional[str] = None):
        llm_config = self.config['llmstudio']
        headers = {"Content-Type": "application/json"}
        system_message = system_prompt_override if system_prompt_override else self.config['system_prompt']
        
        payload = {
            "model": llm_config['model'],
            "messages": [
                {
                    "role": "system",
                    "content": system_message
                },
                {
                    "role": "user",
                    "content": content_to_query[:llm_config['context_window']]
                }
            ],
            "temperature": llm_config['temperature'],
            "max_tokens": llm_config['max_tokens'],
            "stream": False
        }

        try:
            response = requests.post(
                llm_config['api_url'],
                headers=headers,
                json=payload,
                timeout=llm_config.get('timeout', 90)
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            logging.error(f"API Error querying LLM: {str(e)}")
            raise HTTPException(status_code=503, detail=f"LLM API Error: {str(e)}")
        except (KeyError, IndexError) as e:
            logging.error(f"LLM response format error: {str(e)}. Response: {response.text if 'response' in locals() else 'No response object'}")
            raise HTTPException(status_code=500, detail=f"LLM response format error: {str(e)}")

    def save_output(self, note_path, analysis):
        note_name = os.path.basename(note_path).replace('.md', '')
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        rel_path_for_link = os.path.relpath(note_path, self.config['vault_path'])

        response_content = f'''# Second Brain Analysis
**Original Note:** [[{rel_path_for_link.replace('.md', '')}]]

## 🔍 Key Analysis
{analysis}

_Processed at {timestamp}_'''

        output_file_basename = f"SB_{note_name}_{timestamp}.md"
        output_path_full = os.path.join(self.response_folder, output_file_basename)
        
        with open(output_path_full, 'w', encoding='utf-8') as f:
            f.write(response_content)
        
        logging.info(f"Created analysis: {output_file_basename}")
        return os.path.join(self.config['response_folder'], output_file_basename)

    def find_note(self, search_query: str) -> List[str]:
        matches_relative_paths = []
        search_normalized = search_query.lower().replace(" ", "").replace("-", "").replace("_", "")
        vault_path = self.config['vault_path']

        for root, _, files in os.walk(vault_path):
            if any(os.path.join(vault_path, excl_folder) in root for excl_folder in self.config.get('excluded_folders', [])):
                continue
                
            for file in files:
                if file.endswith('.md'):
                    file_normalized = file.lower().replace(" ", "").replace("-", "").replace("_", "").replace(".md", "")
                    
                    if (search_normalized == file_normalized or 
                        search_normalized in file_normalized or
                        ("".join([word[0] for word in search_query.split() if word]).lower() in file_normalized if search_query.strip() else False)):
                        
                        full_path = os.path.join(root, file)
                        matches_relative_paths.append(os.path.relpath(full_path, vault_path))
        return matches_relative_paths

    def query_about_note(self, note_name_or_relative_path: str, question: str):
        if not note_name_or_relative_path.endswith(".md") and '/' not in note_name_or_relative_path and '\\' not in note_name_or_relative_path:
            found_notes = self.find_note(note_name_or_relative_path)
            if not found_notes:
                raise FileNotFoundError(f"Note '{note_name_or_relative_path}' not found by search.")
            if len(found_notes) > 1:
                raise ValueError(f"Ambiguous note name '{note_name_or_relative_path}'. Found: {', '.join(found_notes)}. Provide specific path or use /notes/find.")
            note_relative_path = found_notes[0]
        else:
            note_relative_path = note_name_or_relative_path

        full_note_path = os.path.join(self.config['vault_path'], note_relative_path)
        if not os.path.exists(full_note_path):
            raise FileNotFoundError(f"Note file not found at: {full_note_path}")
        
        try:
            with open(full_note_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            context_window = self.config['llmstudio']['context_window']
            prompt = f"""Analyze this note and answer the question:
            
Note File: {os.path.basename(full_note_path)}
Question: {question}

Content:
{content[:context_window]}"""
            return self.query_llmstudio(prompt)
        except Exception as e:
            logging.error(f"Error querying about note {full_note_path}: {str(e)}")
            raise RuntimeError(f"Error querying about note: {str(e)}") from e

    def analyze_connections(self, note1_name_or_rel_path: str, note2_name_or_rel_path: str):
        notes_content = []
        note_names_for_prompt = []

        for i, name_or_path in enumerate([note1_name_or_rel_path, note2_name_or_rel_path]):
            if not name_or_path.endswith(".md") and '/' not in name_or_path and '\\' not in name_or_path:
                found_notes = self.find_note(name_or_path)
                if not found_notes:
                    raise FileNotFoundError(f"Note '{name_or_path}' (note {i+1}) not found.")
                if len(found_notes) > 1:
                     raise ValueError(f"Ambiguous note name '{name_or_path}' (note {i+1}). Found: {', '.join(found_notes)}. Provide specific path.")
                relative_path = found_notes[0]
            else:
                relative_path = name_or_path

            full_path = os.path.join(self.config['vault_path'], relative_path)
            if not os.path.exists(full_path):
                raise FileNotFoundError(f"Note file not found: {full_path}")

            with open(full_path, 'r', encoding='utf-8') as f:
                notes_content.append(f.read())
            note_names_for_prompt.append(os.path.basename(relative_path).replace('.md',''))
        
        content_for_llm = f"Note 1 ({note_names_for_prompt[0]}):\n{notes_content[0]}\n\nNote 2 ({note_names_for_prompt[1]}):\n{notes_content[1]}"
        
        prompt = f"""Analyze connections between these notes:

{content_for_llm[:self.config['llmstudio']['context_window']]}

1. List conceptual overlaps
2. Identify contradictions
3. Suggest synthesis points"""
        try:
            return self.query_llmstudio(prompt)
        except Exception as e:
            logging.error(f"Error analyzing connections: {str(e)}")
            raise RuntimeError(f"Error analyzing connections: {str(e)}") from e

    # --- Daily Review Methods (Adapted for new config) ---
    def _format_string_with_date(self, format_str: str, target_date: datetime, date_formats_config: dict) -> str:
        formatted_str = format_str
        # Replace based on date_formats from config
        for key, strftime_pattern in date_formats_config.items():
            placeholder = f"{{{key}}}"
            formatted_str = formatted_str.replace(placeholder, target_date.strftime(strftime_pattern))
        
        # Common general placeholders (add more if needed)
        extra_placeholders = {
            "weekday": target_date.strftime('%A'),
            "year": target_date.strftime('%Y'),
            "month_num": target_date.strftime('%m'),
            "month_name_short": target_date.strftime('%b'),
            "month_name_full": target_date.strftime('%B'),
            "day_of_year": target_date.strftime('%j'),
            "week_of_year": target_date.strftime('%U'), # Sunday as first day
        }
        for key, value in extra_placeholders.items():
            placeholder = f"{{{key}}}"
            formatted_str = formatted_str.replace(placeholder, value)
        return formatted_str

    def _find_daily_note_path(self, target_date: datetime) -> Optional[str]:
        daily_notes_config = self.config.get('daily_notes', {})
        if not daily_notes_config.get('enabled', False):
            logging.warning("Daily notes feature is disabled in config.")
            return None

        base_daily_folder_rel = daily_notes_config.get('folder', 'Daily Notes')
        base_daily_folder_abs = os.path.join(self.config['vault_path'], base_daily_folder_rel)
        
        file_formats = daily_notes_config.get('file_formats', ['{full_date}.md']) # Default if not specified
        date_formats_rules = daily_notes_config.get('date_formats', {'full_date': '%Y-%m-%d'})

        for fmt_template in file_formats:
            filename = self._format_string_with_date(fmt_template, target_date, date_formats_rules)
            test_path_full = os.path.join(base_daily_folder_abs, filename)
            if os.path.exists(test_path_full):
                return os.path.relpath(test_path_full, self.config['vault_path'])
        return None

    def _create_daily_note(self, target_date: datetime) -> str:
        daily_notes_config = self.config.get('daily_notes', {})
        if not daily_notes_config.get('enabled', False):
            raise RuntimeError("Daily notes feature is disabled, cannot create note.")

        base_daily_folder_rel = daily_notes_config.get('folder', 'Daily Notes')
        base_daily_folder_abs = os.path.join(self.config['vault_path'], base_daily_folder_rel)
        os.makedirs(base_daily_folder_abs, exist_ok=True) # Ensure base daily folder exists

        file_formats = daily_notes_config.get('file_formats', ['{full_date}.md'])
        # Use the first format in the list as the creation format, or a specific config key for it
        creation_format_template = daily_notes_config.get('creation_format', file_formats[0] if file_formats else '{full_date}.md')
        date_formats_rules = daily_notes_config.get('date_formats', {'full_date': '%Y-%m-%d'})
        
        note_basename = self._format_string_with_date(creation_format_template, target_date, date_formats_rules)
        note_path_full = os.path.join(base_daily_folder_abs, note_basename)
        
        # Ensure parent directories for the note itself exist (if format creates them e.g. YYYY/MM/DD.md)
        os.makedirs(os.path.dirname(note_path_full), exist_ok=True)

        template_content_raw = daily_notes_config.get('default_template', '# Daily Note - {full_date}\n')
        template_content_final = self._format_string_with_date(template_content_raw, target_date, date_formats_rules)
        
        with open(note_path_full, 'w', encoding='utf-8') as f:
            f.write(template_content_final)
        
        logging.info(f"Created daily note: {note_path_full}")
        return os.path.relpath(note_path_full, self.config['vault_path'])

    def get_or_create_daily_note(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        daily_notes_config = self.config.get('daily_notes', {})
        if not daily_notes_config.get('enabled', False):
            raise HTTPException(status_code=403, detail="Daily notes feature is disabled in configuration.")

        target_date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.now()
        
        note_rel_path = self._find_daily_note_path(target_date)
        status = "found"
        if not note_rel_path:
            note_rel_path = self._create_daily_note(target_date)
            status = "created"
        
        return {
            "status": status,
            "date": target_date.strftime('%Y-%m-%d'),
            "note_relative_path": note_rel_path,
            "note_absolute_path": os.path.join(self.config['vault_path'], note_rel_path)
        }

    def refresh_daily_template(self, note_rel_path: str, target_date: datetime) -> str:
        daily_notes_config = self.config.get('daily_notes', {})
        if not daily_notes_config.get('enabled', False):
            raise RuntimeError("Daily notes feature is disabled.")

        full_note_path = os.path.join(self.config['vault_path'], note_rel_path)
        if not os.path.exists(full_note_path):
            raise FileNotFoundError(f"Daily note not found: {full_note_path}")

        template_content_raw = daily_notes_config.get('default_template', '# Daily Note - {full_date}\n')
        date_formats_rules = daily_notes_config.get('date_formats', {'full_date': '%Y-%m-%d'})
        template_content_final = self._format_string_with_date(template_content_raw, target_date, date_formats_rules)
        
        with open(full_note_path, 'w', encoding='utf-8') as f:
            f.write(template_content_final)
        logging.info(f"Template refreshed for: {full_note_path}")
        return f"Template refreshed in {os.path.basename(full_note_path)}"

    def generate_daily_summary(self, note_rel_path: str) -> str:
        # ... (rest of the method from previous version, ensure context window fallback)
        full_note_path = os.path.join(self.config['vault_path'], note_rel_path)
        if not os.path.exists(full_note_path):
            raise FileNotFoundError(f"Daily note not found: {full_note_path}")

        with open(full_note_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if len(content.strip()) < 20: # Or make this configurable
            return "Note is too short or empty - nothing to summarize."
        
        # Use specific context window if configured, else fallback to general, else default
        llm_config = self.config['llmstudio']
        context_window = llm_config.get('context_window_daily_summary', llm_config['context_window'])

        prompt = f"""Create a concise summary of this daily note:

{content[:context_window]}

Include:
1. Key accomplishments
2. Pending tasks
3. Important insights"""
        
        summary = self.query_llmstudio(prompt)
        
        with open(full_note_path, 'r+', encoding='utf-8') as f:
            current_content = f.read()
            review_section_header = self.config.get('daily_notes', {}).get('review_section_header', "## 🔄 Review")
            summary_section_header = self.config.get('daily_notes', {}).get('generated_summary_header', "### 💡 Generated Summary")
            
            new_summary_text = f"\n{summary_section_header}\n{summary}\n_Summary generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n"

            # Improved logic to replace or insert summary
            summary_start_marker = current_content.find(summary_section_header)
            
            if summary_start_marker != -1:
                # Find end of existing summary (next H2/H3 or end of file)
                next_heading_pattern = r"\n## |\n### "
                match_after_summary = re.search(next_heading_pattern, current_content[summary_start_marker + len(summary_section_header):])
                if match_after_summary:
                    end_index = summary_start_marker + len(summary_section_header) + match_after_summary.start()
                    new_content = current_content[:summary_start_marker] + new_summary_text + current_content[end_index:]
                else: # Summary section is the last thing
                    new_content = current_content[:summary_start_marker] + new_summary_text
            elif review_section_header in current_content:
                new_content = current_content.replace(review_section_header, f"{review_section_header}{new_summary_text}", 1)
            else:
                new_content = f"{current_content}\n\n{review_section_header}{new_summary_text}"
            
            f.seek(0)
            f.write(new_content)
            f.truncate()
        
        return f"Summary added/updated in {os.path.basename(full_note_path)}"


    def restructure_daily_content(self, note_rel_path: str) -> str:
        # ... (rest of the method, ensure context window fallback)
        full_note_path = os.path.join(self.config['vault_path'], note_rel_path)
        if not os.path.exists(full_note_path):
            raise FileNotFoundError(f"Daily note not found: {full_note_path}")

        with open(full_note_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        llm_config = self.config['llmstudio']
        context_window = llm_config.get('context_window_daily_restructure', llm_config['context_window'])
        
        # Allow desired structure to be part of config
        daily_notes_config = self.config.get('daily_notes', {})
        desired_structure_prompt = daily_notes_config.get('restructure_prompt_structure', """
# {full_date} ({weekday})
## 🎯 Focus Areas
- ...
## 📝 Notes
- ...
## ✅ Tasks
- [ ] ...
## 🔄 Review
- ... (Insights, reflections)
""")
        # We need the target_date to fill placeholders in desired_structure_prompt
        # This is a bit tricky as restructure_daily_content only gets note_rel_path
        # For now, let's assume the LLM can infer date from content or we skip date substitution in prompt.
        # A better way would be to pass target_date to this method.
        # For now, if placeholders exist, try to fill with current date or generic terms.
        target_date_for_prompt = datetime.now() # Fallback
        try:
            # Attempt to parse date from filename if it's a daily note filename
            base_name = os.path.basename(note_rel_path)
            # This is a very naive date parsing. Better to pass target_date if available.
            match = re.search(r"(\d{4}-\d{2}-\d{2})", base_name)
            if match:
                target_date_for_prompt = datetime.strptime(match.group(1), "%Y-%m-%d")
        except Exception:
            pass # Use now() as fallback

        final_desired_structure_prompt = self._format_string_with_date(
            desired_structure_prompt, 
            target_date_for_prompt, 
            daily_notes_config.get('date_formats', {'full_date': '%Y-%m-%d'})
        )


        prompt = f"""Reorganize this daily note into clear sections based on the provided standard template.
Current Content:
{content[:context_window]}

Desired Structure:
{final_desired_structure_prompt}

Please:
1. Maintain all important information.
2. Use the provided heading levels and titles from the 'Desired Structure'.
3. Group related items logically under these standard sections.
4. Retain original language and details as much as possible.
5. If content doesn't fit neatly, try to place it in 'Notes' or 'Review'.
"""
        restructured = self.query_llmstudio(prompt)
        
        with open(full_note_path, 'w', encoding='utf-8') as f:
            f.write(restructured)
        
        return f"Successfully restructured {os.path.basename(full_note_path)}"


# --- FastAPI App and Global Brain Instance ---
brain_instance: Optional[SecondBrain] = None
observer_instance: Optional[Observer] = None
watchdog_thread: Optional[threading.Thread] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global brain_instance, observer_instance, watchdog_thread
    brain_instance = SecondBrain(CONFIG)
    brain_instance.setup_logging() # Setup logging once
    logging.info("SecondBrain FastAPI application starting...")
    logging.info(f"Vault path: {CONFIG['vault_path']}")

    watchdog_config = CONFIG.get("watchdog", {})
    # Enable watchdog if "watchdog" key exists and "enabled" is not explicitly false
    if watchdog_config and watchdog_config.get("enabled", True): 
        debounce_seconds = float(watchdog_config.get('debounce_seconds', 5.0)) # Ensure float
        logging.info(f"Watchdog is enabled. Debounce: {debounce_seconds}s. Starting file observer...")
        
        event_handler = ObsidianHandler(brain_instance, debounce_seconds)
        observer_instance = Observer()
        observer_instance.schedule(event_handler, path=CONFIG['vault_path'], recursive=True)
        
        watchdog_thread = threading.Thread(target=observer_instance.start, daemon=True)
        watchdog_thread.start()
        logging.info(f"Observer started watching: {CONFIG['vault_path']}")
    else:
        logging.info("Watchdog is disabled in config or 'watchdog' section missing.")

    yield 

    logging.info("SecondBrain FastAPI application shutting down...")
    if observer_instance and observer_instance.is_alive():
        observer_instance.stop()
        logging.info("Watchdog observer stopped.")
    if watchdog_thread and watchdog_thread.is_alive():
        try:
            if observer_instance: observer_instance.join(timeout=5) # Join observer first
        except Exception as e:
            logging.error(f"Error joining observer: {e}")
        watchdog_thread.join(timeout=5) 
        logging.info("Watchdog thread joined.")
    logging.info("Shutdown complete.")


app = FastAPI(
    title="Second Brain API",
    description="API for interacting with your Second Brain (Obsidian Vault)",
    version="0.2.0", # Incremented version
    lifespan=lifespan
)

# --- Pydantic Models for Requests and Responses (mostly unchanged) ---
class ProcessNoteRequest(BaseModel):
    note_path_relative: str = Field(..., description="Relative path to the note from the vault root, e.g., 'Notes/MyNote.md'")

class ProcessNoteResponse(BaseModel):
    message: str
    original_note: Optional[str] = None
    analysis_file: Optional[str] = None

class QueryNoteRequest(BaseModel):
    note_name_or_relative_path: str = Field(..., description="Name of the note (e.g., 'My Project Idea') or relative path (e.g., 'Projects/MyProject.md')")
    question: str

class AnalyzeConnectionsRequest(BaseModel):
    note1_name_or_relative_path: str
    note2_name_or_relative_path: str

class DailyNoteResponse(BaseModel):
    status: str 
    date: str
    note_relative_path: str
    note_absolute_path: str

class StandardMessageResponse(BaseModel):
    message: str
    details: Optional[Any] = None

class FoundNotesResponse(BaseModel):
    search_query: str
    matches: List[str] 

# --- API Endpoints (mostly unchanged, but will use updated brain_instance methods) ---
@app.get("/")
async def root():
    return {"message": "Second Brain API is running. See /docs for available endpoints."}

@app.post("/notes/process", response_model=ProcessNoteResponse, tags=["Notes"])
async def process_single_note_endpoint(request: ProcessNoteRequest):
    if not brain_instance:
        raise HTTPException(status_code=503, detail="Service not fully initialized")
    try:
        result = brain_instance.process_note(request.note_path_relative)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logging.exception("Unexpected error in /notes/process")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.post("/notes/query", response_model=StandardMessageResponse, tags=["Notes"])
async def query_note_endpoint(request: QueryNoteRequest):
    if not brain_instance:
        raise HTTPException(status_code=503, detail="Service not fully initialized")
    try:
        answer = brain_instance.query_about_note(request.note_name_or_relative_path, request.question)
        return StandardMessageResponse(message="Query successful", details=answer)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e: 
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logging.exception("Unexpected error in /notes/query")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.get("/notes/find", response_model=FoundNotesResponse, tags=["Notes"])
async def find_note_endpoint(query: str = Query(..., description="Search term for the note name.")):
    if not brain_instance:
        raise HTTPException(status_code=503, detail="Service not fully initialized")
    try:
        matches = brain_instance.find_note(query)
        return FoundNotesResponse(search_query=query, matches=matches) # Always return, even if empty list
    except Exception as e:
        logging.exception("Unexpected error in /notes/find")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.post("/notes/analyze-connections", response_model=StandardMessageResponse, tags=["Notes"])
async def analyze_connections_endpoint(request: AnalyzeConnectionsRequest):
    if not brain_instance:
        raise HTTPException(status_code=503, detail="Service not fully initialized")
    try:
        analysis = brain_instance.analyze_connections(request.note1_name_or_relative_path, request.note2_name_or_relative_path)
        return StandardMessageResponse(message="Connection analysis successful", details=analysis)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e: 
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logging.exception("Unexpected error in /notes/analyze-connections")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

ISO_DATE_REGEX = r"^\d{4}-\d{2}-\d{2}$"

@app.get("/daily/{date_str}", response_model=DailyNoteResponse, tags=["Daily Review"])
@app.post("/daily/{date_str}", response_model=DailyNoteResponse, tags=["Daily Review"]) 
async def get_or_create_daily_note_endpoint(
    date_str: str = Path(..., description="Date in YYYY-MM-DD format. Use 'today' for current date.", regex=ISO_DATE_REGEX + "|today")
):
    if not brain_instance:
        raise HTTPException(status_code=503, detail="Service not fully initialized")
    
    actual_date_str = date.today().strftime('%Y-%m-%d') if date_str == "today" else date_str
    try:
        datetime.strptime(actual_date_str, '%Y-%m-%d') 
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD or 'today'.")

    try:
        result = brain_instance.get_or_create_daily_note(actual_date_str)
        return result
    except HTTPException as e: # Re-raise HTTP exceptions from brain_instance (like 403 for disabled daily notes)
        raise e
    except Exception as e:
        logging.exception(f"Unexpected error in /daily/{actual_date_str}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.post("/daily/{date_str}/template", response_model=StandardMessageResponse, tags=["Daily Review"])
async def refresh_daily_template_endpoint(
    date_str: str = Path(..., description="Date in YYYY-MM-DD format or 'today'", regex=ISO_DATE_REGEX + "|today")
):
    if not brain_instance:
        raise HTTPException(status_code=503, detail="Service not fully initialized")
    
    actual_date_str = date.today().strftime('%Y-%m-%d') if date_str == "today" else date_str
    try:
        target_dt = datetime.strptime(actual_date_str, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD or 'today'.")

    try:
        daily_note_info = brain_instance.get_or_create_daily_note(actual_date_str)
        note_rel_path = daily_note_info["note_relative_path"]
        
        message = brain_instance.refresh_daily_template(note_rel_path, target_dt)
        return StandardMessageResponse(message=message, details={"note_relative_path": note_rel_path})
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException as e: 
        raise e
    except Exception as e:
        logging.exception(f"Unexpected error in /daily/{actual_date_str}/template")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.post("/daily/{date_str}/summary", response_model=StandardMessageResponse, tags=["Daily Review"])
async def generate_daily_summary_endpoint(
    date_str: str = Path(..., description="Date in YYYY-MM-DD format or 'today'", regex=ISO_DATE_REGEX + "|today")
):
    if not brain_instance:
        raise HTTPException(status_code=503, detail="Service not fully initialized")

    actual_date_str = date.today().strftime('%Y-%m-%d') if date_str == "today" else date_str
    try:
        datetime.strptime(actual_date_str, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD or 'today'.")
    
    try:
        daily_note_info = brain_instance.get_or_create_daily_note(actual_date_str) 
        note_rel_path = daily_note_info["note_relative_path"]

        message = brain_instance.generate_daily_summary(note_rel_path)
        return StandardMessageResponse(message=message, details={"note_relative_path": note_rel_path})
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException as e: 
        raise e
    except Exception as e:
        logging.exception(f"Unexpected error in /daily/{actual_date_str}/summary")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.post("/daily/{date_str}/restructure", response_model=StandardMessageResponse, tags=["Daily Review"])
async def restructure_daily_content_endpoint(
    date_str: str = Path(..., description="Date in YYYY-MM-DD format or 'today'", regex=ISO_DATE_REGEX + "|today")
):
    if not brain_instance:
        raise HTTPException(status_code=503, detail="Service not fully initialized")

    actual_date_str = date.today().strftime('%Y-%m-%d') if date_str == "today" else date_str
    try:
        datetime.strptime(actual_date_str, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD or 'today'.")

    try:
        daily_note_info = brain_instance.get_or_create_daily_note(actual_date_str) 
        note_rel_path = daily_note_info["note_relative_path"]

        message = brain_instance.restructure_daily_content(note_rel_path)
        return StandardMessageResponse(message=message, details={"note_relative_path": note_rel_path})
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException as e: 
        raise e
    except Exception as e:
        logging.exception(f"Unexpected error in /daily/{actual_date_str}/restructure")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# --- Watchdog Handler (Adapted for new config access) ---
class ObsidianHandler(FileSystemEventHandler):
    def __init__(self, brain: SecondBrain, debounce_sec: float):
        self.brain = brain
        self.debounce_sec = debounce_sec
        self.debounce_timers: Dict[str, threading.Timer] = {} 

    def on_modified(self, event):
        if (event.is_directory or
            not event.src_path.endswith('.md') or
            not os.path.exists(event.src_path)):
            return

        try:
            relative_path = os.path.relpath(event.src_path, self.brain.config['vault_path'])
        except ValueError: 
            logging.debug(f"Modified file {event.src_path} is outside the vault path. Skipping.")
            return

        if relative_path in self.debounce_timers:
            self.debounce_timers[relative_path].cancel()

        timer = threading.Timer(
            self.debounce_sec,
            self._process_with_retry,
            [relative_path] 
        )
        self.debounce_timers[relative_path] = timer
        timer.start()
        logging.info(f"Watchdog detected change: {os.path.basename(event.src_path)}. Debouncing for {self.debounce_sec}s...")

    def _process_with_retry(self, note_path_relative: str, retries: int = 3):
        full_path = os.path.join(self.brain.config['vault_path'], note_path_relative)
        try:
            # Check if path is in an excluded folder *before* processing
            # This check is also inside brain.process_note, but good to have early exit
            if not self.brain.should_process(full_path):
                logging.info(f"Watchdog: Skipping {note_path_relative} (excluded or doesn't meet criteria).")
                if note_path_relative in self.debounce_timers:
                    del self.debounce_timers[note_path_relative]
                return

            if os.path.exists(full_path): 
                logging.info(f"Watchdog processing: {note_path_relative}")
                self.brain.process_note(note_path_relative) 
            else:
                logging.warning(f"Watchdog: File {full_path} no longer exists. Skipping.")

            if note_path_relative in self.debounce_timers:
                del self.debounce_timers[note_path_relative]
        except Exception as e:
            logging.error(f"Watchdog: Error processing {note_path_relative}: {str(e)}")
            if retries > 0:
                logging.warning(f"Watchdog: Retrying {note_path_relative} ({retries} left)...")
                time.sleep(self.brain.config.get("watchdog",{}).get("retry_delay", 2.0)) # Configurable retry delay
                self._process_with_retry(note_path_relative, retries - 1)
            else:
                logging.error(f"Watchdog: Failed to process {note_path_relative} after multiple retries.")

# --- To run the app ---
if __name__ == "__main__":
    import uvicorn
    
    if not os.path.exists('config.json'):
        print("ERROR: config.json not found. Please create it before running.", file=sys.stderr)
        sys.exit(1)
        
    print("Starting Second Brain API with Uvicorn...")
    print(f"Open http://127.0.0.1:8000/docs to see API documentation.")
    
    watchdog_cfg = CONFIG.get("watchdog", {})
    if watchdog_cfg and watchdog_cfg.get("enabled", True):
         print("Watchdog file monitoring is ENABLED in config and will run in a background thread.")
    else:
         print("Watchdog file monitoring is DISABLED in config.")
         print("To process notes, use the POST /notes/process endpoint or enable watchdog in config.json.")

    uvicorn.run("main:app", host=CONFIG.get("api_host", "0.0.0.0"), port=CONFIG.get("api_port", 8000), reload=CONFIG.get("api_reload", False))