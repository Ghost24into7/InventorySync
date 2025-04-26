# voice_control.py
import os
import logging
import json
from flask import request, jsonify
from google.generativeai import GenerativeModel
import google.generativeai as genai
from datetime import datetime
import dateparser # You might need to install this: pip install dateparser
from dotenv import load_dotenv
import re

# Configure logging (consider adjusting level and filename)
logging.basicConfig(
    filename='assistant.log',
    level=logging.INFO, # Changed to INFO for production, DEBUG for development
    format='%(asctime)s %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables (.env file should contain GEMINI_API_KEY)
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY not found in environment variables. Please set it.")
    # Depending on your error handling strategy, you might want to raise an error here
    # For now, we'll let it fail during Gemini client configuration if key is missing

try:
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    logger.error(f"Failed to configure Gemini API: {e}")
    # Handle API key configuration error appropriately

class VoiceAssistant:
    def __init__(self):
        try:
            # Use a Gemini model suitable for complex instruction following
            # Consider 'gemini-1.5-pro-latest' if 'flash' struggles, but be mindful of cost/latency
            self.model = GenerativeModel("gemini-1.5-flash") # Or "gemini-1.5-pro-latest"
            logger.info("VoiceAssistant initialized with Gemini model.")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            self.model = None # Ensure model is None if initialization fails

        # Enhanced prompt covering all requested actions
        self.prompt_template = """
        You are SyncVoice, an advanced, professional, and conversational voice assistant for InventorySync.
        InventorySync is a web application with these main sections/pages: 'upload', 'data-preview', 'local-files', 'visualizations' (or 'insights'), and 'chatbot'.
        Your primary function is to interpret user voice commands accurately and translate them into specific actions to control the web application.
        You need to provide responses in a JSON format ONLY, enclosed in ```json ... ```.

        **Capabilities & Actions:**

        1.  **Navigation:** Navigate between sections.
            - Keywords: "go to", "show", "open", "navigate to"
            - Sections: 'upload', 'data-preview', 'local-files', 'visualizations'/'insights', 'chatbot'
            - JSON Action: `navigate`, Parameters: `section`, `response` (e.g., "Navigating to Upload section.")

        2.  **Chatbot Interaction:** Send user queries to the application's chatbot. Handle requests to read the response aloud, possibly in different languages.
            - Keywords: "ask chatbot", "tell chatbot", "what does chatbot say about", "read chatbot response"
            - JSON Action: `chatbot_query`, Parameters: `query`, `response`, `lang` (optional language code for response dictation, e.g., 'en-US', 'es-ES')
            - JSON Action: `read_chatbot_response`, Parameters: `response`, `lang` (optional)

        3.  **Chart/Visualization Analysis:** Describe or summarize the data shown in the charts on the 'visualizations'/'insights' page.
            - Keywords: "analyze charts", "explain insights", "what do the graphs show", "summarize visualizations", "read chart summary"
            - JSON Action: `visualization_summary`, Parameters: `response` (e.g., "Fetching visualization summary...")

        4.  **File Operations (Upload Section):**
            - **Select File:** Guide the user to manually select a file (cannot be done programmatically). Trigger the file input click.
                - Keywords: "upload file", "select file", "choose file"
                - JSON Action: `trigger_file_input_click`, Parameters: `response` (e.g., "Okay, opening file selection. Please choose your Excel file.")
            - **Process File:** Trigger the 'Process' button after a file and date are selected.
                - Keywords: "process file", "submit data", "upload now", "run processing"
                - JSON Action: `trigger_process_button`, Parameters: `response` (e.g., "Starting data processing...")
            - **Read/Explain Upload Summary:** Read out the results shown after processing is complete.
                - Keywords: "read upload summary", "what were the upload results", "explain processing results"
                - JSON Action: `read_upload_summary`, Parameters: `response` (e.g., "Reading the upload summary...")
            - **Download Processed File:** Trigger the download button for the last processed file.
                - Keywords: "download processed file", "get the processed file"
                - JSON Action: `trigger_download_processed`, Parameters: `response` (e.g., "Downloading the last processed file...")

        5.  **Date Input:** Set the date in the upload form. Parse various date formats (e.g., "today", "yesterday", "April 15th, 2025").
            - Keywords: "set date", "change date", "date is"
            - JSON Action: `set_date`, Parameters: `date` (YYYY-MM-DD), `response` (e.g., "Setting date to 2025-04-16.")

        6.  **Theme Control:** Toggle between light and dark themes.
            - Keywords: "change theme", "toggle theme", "dark mode", "light mode"
            - JSON Action: `theme_toggle`, Parameters: `response` (e.g., "Toggling theme.")

        7.  **Log Management:**
            - **Read Logs:** Read the recent activity logs.
                - Keywords: "read logs", "show activity", "what are the logs"
                - JSON Action: `read_logs`, Parameters: `response` (e.g., "Reading recent activity logs...")
            - **Clear Logs:** Clear the activity log display.
                - Keywords: "clear logs", "erase activity"
                - JSON Action: `clear_logs`, Parameters: `response` (e.g., "Clearing activity logs.")

        8.  **Data Preview Actions:**
            - **Refresh Preview:** Trigger the refresh button on the data preview page.
                - Keywords: "refresh preview", "update data table", "reload preview"
                - JSON Action: `trigger_refresh_preview`, Parameters: `response` (e.g., "Refreshing data preview...")
            - **Read Metrics:** Read the summary metrics (total records, unique brands, etc.) from the data preview page.
                - Keywords: "read metrics", "what are the data stats", "summarize preview data"
                - JSON Action: `read_metrics`, Parameters: `response` (e.g., "Reading data preview metrics...")

        9.  **Local Files Actions:**
            - **Download All:** Trigger the download of all daily files as a ZIP archive.
                - Keywords: "download all files", "get zip archive", "download daily files"
                - JSON Action: `trigger_download_all_zip`, Parameters: `response` (e.g., "Initiating download of all daily files...")

        10. **Language Control:** Change the language for TTS responses.
            - Keywords: "speak in", "change language to", "use [language]" (e.g., "speak in Spanish", "use French")
            - JSON Action: `change_language`, Parameters: `lang` (e.g., 'es-ES', 'fr-FR'), `response` (e.g., "Okay, switching to Spanish.")

        11. **Stop/Deactivate:** Stop listening and deactivate the assistant temporarily.
            - Keywords: "stop", "cancel", "exit", "goodbye"
            - JSON Action: `stop`, Parameters: `response` (e.g., "Goodbye! Let me know if you need help again.")

        12. **Error/Fallback:** Handle unrecognized commands.
            - JSON Action: `error`, Parameters: `response` (e.g., "Sorry, I couldn't understand that. Could you please rephrase?")

        **Context:**
        - Current Date: {current_date}
        - User Location: {current_location} (Use for context if relevant, e.g., interpreting relative times)

        **Instructions:**
        1. Analyze the user's command text below.
        2. Determine the single most appropriate action from the list above.
        3. Extract necessary parameters (like section name, date, query text, language code).
        4. For dates, parse relative terms (today, yesterday) based on the current date and convert to YYYY-MM-DD format.
        5. Formulate a concise, user-friendly text response confirming the action or providing the requested information/guidance.
        6. **CRITICAL:** Output *only* a valid JSON object enclosed in triple backticks json format (```json ... ```). Do not include *any* text outside this JSON block.

        **User Command:** "{user_command}"

        **JSON Output:**
        ```json
        {{
            "action": "...",
            "section": "..." (if applicable),
            "query": "..." (if applicable),
            "date": "..." (if applicable),
            "lang": "..." (if applicable),
            "response": "..."
        }}
        ```
        """

    def _parse_gemini_response(self, raw_response: str) -> dict:
        """Extracts and parses JSON from the Gemini response."""
        logger.debug(f"Attempting to parse raw response: {raw_response}")
        match = re.search(r'```json\s*({.*?})\s*```', raw_response, re.DOTALL)
        if not match:
            logger.error(f"Could not find JSON block in response: {raw_response}")
            # Fallback: try parsing the whole string if it looks like JSON
            if raw_response.strip().startswith('{') and raw_response.strip().endswith('}'):
                json_str = raw_response.strip()
            else:
              return {"action": "error", "response": "I received an unexpected response format. Please try again."}
        else:
            json_str = match.group(1).strip()

        logger.debug(f"Extracted JSON string: {json_str}")
        try:
            result = json.loads(json_str)
            # Basic validation
            if "action" not in result or "response" not in result:
                logger.error(f"Parsed JSON missing required keys ('action', 'response'): {result}")
                raise ValueError("Missing required keys in JSON")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"JSONDecodeError: {e}. String was: {json_str}")
            return {"action": "error", "response": "There was an issue understanding the command format. Please try again."}
        except ValueError as e:
             logger.error(f"ValueError during parsing: {e}. Parsed result: {result}")
             return {"action": "error", "response": "There was an issue interpreting the command structure. Please try again."}


    def _get_current_context(self) -> dict:
         """Gets current date and location for the prompt."""
         # In a real app, location might be determined differently
         return {
             "current_date": datetime.now().strftime('%Y-%m-%d'),
             "current_location": "Virar, Maharashtra, India" # Or get dynamically if needed
         }

    def process_command(self):
        """Processes a voice command using Gemini API."""
        if not self.model:
             logger.error("Gemini model not initialized. Cannot process command.")
             return jsonify({"action": "error", "response": "Voice assistant is currently unavailable due to a configuration issue."})

        logger.debug("Processing new voice command request")
        data = request.get_json()
        if not data or 'command' not in data:
            logger.error("Invalid request: No JSON data or 'command' key found.")
            return jsonify({"action": "error", "response": "Invalid command request received."}), 400

        command = data.get('command', '').strip().lower()

        if not command:
            logger.warning("Received empty command.")
            return jsonify({"action": "error", "response": "I didn't hear anything. Could you please repeat?"})

        logger.info(f"Received user command: '{command}'")

        try:
            # Prepare the full prompt with current context
            context = self._get_current_context()
            full_prompt = self.prompt_template.format(
                current_date=context["current_date"],
                current_location=context["current_location"],
                user_command=command
            )

            logger.debug("Sending command to Gemini API...")
            response = self.model.generate_content(full_prompt)
            raw_response = response.text.strip()
            logger.debug(f"Gemini API raw response:\n{raw_response}")

            # Parse and validate the response
            result = self._parse_gemini_response(raw_response)

            # Log details based on action
            action = result.get("action", "unknown")
            log_details = {k: v for k, v in result.items() if k != 'response'} # Don't log the spoken response itself unless needed
            logger.info(f"Action determined: '{action}'. Details: {log_details}")

            return jsonify(result)

        except Exception as e:
            # Catch potential API errors or other exceptions
            logger.error(f"Error processing command '{command}': {str(e)}", exc_info=True) # Include traceback
            # Provide a generic error message to the user
            return jsonify({"action": "error", "response": "Sorry, I encountered an issue while processing your command. Please try again."})

