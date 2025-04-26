// voice_control.js

// --- Elements ---
const voiceBtn = document.getElementById('voice-assistant-btn');
const avatar = document.getElementById('voice-assistant-avatar'); // Make sure this element exists in your HTML
const messageInput = document.getElementById('messageInput'); // Chatbot input
const sendButton = document.getElementById('sendButton'); // Chatbot send button
const dateInput = document.getElementById('date'); // Upload date input
const fileInput = document.getElementById('file'); // Upload file input
const uploadBtn = document.getElementById('upload-btn'); // Process button
const themeToggleBtn = document.getElementById('theme-toggle');
const logContainer = document.getElementById('log-container');
const downloadProcessedBtn = document.getElementById('download-btn'); // Button in upload results
const refreshPreviewBtn = document.getElementById('refresh-preview'); // In data preview

// --- Web Speech API Setup ---
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const synth = window.speechSynthesis;
let recognition;

// Check if SpeechRecognition is supported
if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.interimResults = false; // We want final results
    recognition.maxAlternatives = 1; // Get the most likely result
} else {
    console.error("Speech Recognition not supported in this browser.");
    // Optionally disable the voice button or show a message
    if (voiceBtn) voiceBtn.disabled = true;
    // You could show a toast message here as well using showToast() from script.js
    showToast("Voice control is not supported in this browser.", "error");
}

// --- State ---
let isListening = false;
let currentLang = 'en-US'; // Default language
let lastSpokenBotResponse = ''; // To store the last chatbot response for reading aloud
let activationPhrase = "hello sync voice"; // Optional phrase to start interaction

// --- Core Functions ---

/**
 * Speaks the given text using the Web Speech Synthesis API.
 * @param {string} text The text to speak.
 * @param {string} [lang=currentLang] The language code (e.g., 'en-US', 'es-ES').
 * @returns {Promise<void>} A promise that resolves when speaking finishes.
 */
function speak(text, lang = currentLang) {
    return new Promise((resolve, reject) => {
        if (!synth) {
           console.error("Speech Synthesis not supported.");
           return reject(new Error("Speech Synthesis not supported."));
        }
        // If already speaking, cancel it to avoid overlap
        if (synth.speaking) {
            console.log("Cancelling previous speech...");
            synth.cancel();
            // Add a tiny delay to ensure cancellation completes
            setTimeout(() => proceedWithSpeech(text, lang, resolve, reject), 50);
        } else {
            proceedWithSpeech(text, lang, resolve, reject);
        }
    });
}

function proceedWithSpeech(text, lang, resolve, reject) {
     try {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = lang;
        utterance.volume = 1; // Max volume
        utterance.rate = 1; // Normal rate
        utterance.pitch = 1; // Normal pitch

        utterance.onstart = () => {
            console.log(`Speaking: "${text}" in ${lang}`);
            updateAvatar('speaking');
        };

        utterance.onend = () => {
            console.log("Finished speaking.");
            updateAvatar('idle'); // Return to idle after speaking
            resolve();
        };

        utterance.onerror = (event) => {
            console.error("Speech synthesis error:", event.error);
            updateAvatar('idle');
            // Try to provide a user-friendly error message
             let errorMsg = "Sorry, I couldn't speak the response.";
            if (event.error === 'language-unavailable') {
                 errorMsg = `Sorry, the language ${lang} is not available for speaking.`;
            } else if (event.error === 'synthesis-failed') {
                 errorMsg = "Sorry, there was an error generating the speech.";
            }
            // You might want to show this error via a toast
            // showToast(errorMsg, 'error');
            reject(new Error(event.error));
        };

        synth.speak(utterance);
    } catch (error) {
        console.error("Error creating SpeechSynthesisUtterance:", error);
        updateAvatar('idle');
        reject(error);
    }
}


/**
 * Starts the speech recognition process.
 */
function startListening() {
    if (!recognition) {
        console.error("Speech Recognition not initialized.");
        speak("Sorry, voice recognition is not available right now.");
        return;
    }
    if (!isListening) {
         // Stop any ongoing speech before listening
        if (synth && synth.speaking) {
            synth.cancel();
        }
        try {
            isListening = true;
            recognition.lang = currentLang; // Set language for recognition
            recognition.start();
            updateAvatar('listening');
            console.log(`Started listening (${currentLang})...`);
        } catch (error) {
            // Handle cases like microphone permission issues or recognition already started
            console.error("Error starting recognition:", error);
            speak("Sorry, I couldn't start listening. Please check microphone permissions.");
            isListening = false;
            updateAvatar('idle');
        }
    } else {
        console.log("Already listening.");
    }
}

/**
 * Stops the speech recognition process.
 */
function stopListening() {
    if (recognition && isListening) {
        recognition.stop();
        isListening = false;
        updateAvatar('idle');
        console.log("Stopped listening.");
    }
}

/**
 * Updates the visual state of the voice assistant avatar.
 * @param {'idle' | 'listening' | 'processing' | 'speaking'} state The new state.
 */
function updateAvatar(state) {
    if (!avatar) return;
    avatar.classList.remove('avatar-idle', 'avatar-listening', 'avatar-processing', 'avatar-speaking');
    avatar.classList.add(`avatar-${state}`);
}

/**
 * Processes the recognized transcript by sending it to the backend.
 * @param {string} transcript The recognized speech text.
 */
async function processTranscript(transcript) {
    console.log(`Processing transcript: "${transcript}"`);
    updateAvatar('processing'); // Show processing state

    // Optional: Check for activation phrase if desired
    // if (!transcript.toLowerCase().startsWith(activationPhrase)) {
    //     console.log("Activation phrase not detected.");
    //     updateAvatar('idle');
    //     startListening(); // Or just stop and wait for button press
    //     return;
    // }
    // const command = transcript.toLowerCase().replace(activationPhrase, "").trim();
    const command = transcript; // Process the whole transcript for now

    if (!command) {
        console.log("Empty command after processing.");
        updateAvatar('idle');
        speak("I didn't catch that clearly. Could you try again?").then(startListening);
        return;
    }

    try {
        const response = await fetch('/voice_command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: command })
        });

        if (!response.ok) {
            // Handle HTTP errors (e.g., 500 Internal Server Error)
            console.error(`Server error: ${response.status} ${response.statusText}`);
            const errorText = await response.text(); // Try to get more details
            logger.error(`Server response text: ${errorText}`);
            throw new Error(`Server responded with status ${response.status}`);
        }

        const data = await response.json();
        console.log("Received action data from backend:", data);
        updateAvatar('idle'); // Temporarily idle before speaking response or acting

        // --- Execute Action ---
        await handleBackendAction(data);

    } catch (error) {
        console.error("Error processing command:", error);
        updateAvatar('idle');
        await speak(`Sorry, there was an error processing your command: ${error.message}. Please try again.`);
        // Optionally restart listening after error
        startListening();
    }
}

/**
 * Executes the action received from the backend.
 * @param {object} data The action data from the backend JSON response.
 */
async function handleBackendAction(data) {
    const action = data.action;
    const responseMessage = data.response || "Okay."; // Default response
    const responseLang = data.lang || currentLang; // Use specified lang or current

    // Always try to speak the confirmation/response first, unless stopping
    if (action !== 'stop' && action !== 'error') {
        await speak(responseMessage, responseLang);
    }

    try {
        switch (action) {
            case 'navigate':
                if (data.section) {
                    console.log(`Executing navigation to: ${data.section}`);
                    // Use existing function from script.js if available
                    if (typeof showSection === 'function') {
                        showSection(data.section);
                        // Ensure the corresponding nav link is visually activated
                        document.querySelectorAll('.nav-link').forEach(link => {
                           link.classList.toggle('active', link.getAttribute('data-section') === data.section);
                        });
                    } else {
                         console.warn('showSection function not found. Cannot perform navigation.');
                         // Fallback: Try scrolling
                         const sectionElement = document.getElementById(data.section);
                         sectionElement?.scrollIntoView({ behavior: 'smooth' });
                    }
                } else {
                    console.error("Navigation action missing section parameter.");
                    await speak("I couldn't navigate because the destination was unclear.");
                }
                break;

            case 'chatbot_query':
                if (data.query && messageInput && sendButton) {
                    console.log(`Executing chatbot query: ${data.query}`);
                    messageInput.value = data.query;
                    sendButton.click(); // Simulate click to send message via chatbot.js
                    // Note: Reading the response requires coordination with chatbot.js
                    // We'll store the request and chatbot.js needs to update `lastSpokenBotResponse`
                    // Then, a separate "read chatbot response" command can be used.
                } else {
                     console.error("Chatbot query action missing query or elements.");
                     await speak("I couldn't send the message to the chatbot.");
                }
                break;

            case 'read_chatbot_response':
                 // Requires chatbot.js to update `lastSpokenBotResponse` when a message arrives
                 if (lastSpokenBotResponse) {
                     console.log("Reading last chatbot response.");
                     await speak(lastSpokenBotResponse, responseLang);
                     lastSpokenBotResponse = ''; // Clear after reading
                 } else {
                     console.log("No recent chatbot response to read.");
                     await speak("There's no recent chatbot response available to read.", responseLang);
                 }
                 break;

            case 'visualization_summary':
                console.log("Executing visualization summary.");
                // Assumes a function exists in script.js or here to get the summary text
                if (typeof summarizeCharts === 'function') {
                    const summary = summarizeCharts(); // Get text summary from charts
                    await speak(summary || "I couldn't summarize the charts right now.", responseLang);
                } else {
                    console.warn("summarizeCharts function not found.");
                    await speak("I can't summarize the charts at the moment.", responseLang);
                }
                break;

            case 'trigger_file_input_click':
                 if (fileInput) {
                     console.log("Triggering file input click.");
                     fileInput.click(); // Open the browser's file selection dialog
                 } else {
                     console.error("File input element not found.");
                     await speak("I couldn't open the file selection window.");
                 }
                 break;

            case 'trigger_process_button':
                 if (uploadBtn) {
                      console.log("Triggering process button click.");
                      uploadBtn.click();
                 } else {
                      console.error("Process button element not found.");
                      await speak("I couldn't start the processing.");
                 }
                 break;

            case 'read_upload_summary':
                 console.log("Executing read upload summary.");
                 if (typeof summarizeUploadResults === 'function') {
                     const summary = summarizeUploadResults();
                     await speak(summary || "No upload summary is available to read.", responseLang);
                 } else {
                      console.warn("summarizeUploadResults function not found.");
                      await speak("I can't read the upload summary right now.", responseLang);
                 }
                 break;

             case 'trigger_download_processed':
                 if (downloadProcessedBtn && !downloadProcessedBtn.disabled) {
                      console.log("Triggering download processed file button click.");
                      downloadProcessedBtn.click();
                 } else {
                      console.error("Download processed file button not found or disabled.");
                      await speak("I couldn't download the processed file. Please ensure processing is complete.");
                 }
                 break;

            case 'set_date':
                if (data.date && dateInput) {
                    console.log(`Executing set date: ${data.date}`);
                    dateInput.value = data.date;
                } else {
                     console.error("Set date action missing date or element.");
                     await speak("I couldn't set the date.");
                }
                break;

            case 'theme_toggle':
                 if (themeToggleBtn) {
                      console.log("Executing theme toggle.");
                      themeToggleBtn.click();
                 } else {
                     console.error("Theme toggle button not found.");
                     // Don't speak error here, the spoken response was already "Toggling theme."
                 }
                 break;

            case 'read_logs':
                 console.log("Executing read logs.");
                 if (typeof readLogs === 'function') {
                     const logs = readLogs();
                     await speak(logs || "There are no recent logs to read.", responseLang);
                 } else {
                      console.warn("readLogs function not found.");
                      await speak("I can't read the logs right now.", responseLang);
                 }
                 break;

            case 'clear_logs':
                 console.log("Executing clear logs.");
                 if (typeof clearLogs === 'function') {
                     clearLogs(); // Assumes clearLogs() exists in script.js
                 } else {
                      console.warn("clearLogs function not found.");
                      // Response already spoken
                 }
                 break;

            case 'trigger_refresh_preview':
                  if (refreshPreviewBtn) {
                      console.log("Triggering refresh preview button click.");
                      refreshPreviewBtn.click();
                  } else {
                       console.error("Refresh preview button not found.");
                       await speak("I couldn't refresh the data preview.");
                  }
                  break;

             case 'read_metrics':
                 console.log("Executing read metrics.");
                 if (typeof summarizeMetrics === 'function') {
                     const metrics = summarizeMetrics();
                     await speak(metrics || "Data metrics are not available right now.", responseLang);
                 } else {
                      console.warn("summarizeMetrics function not found.");
                      await speak("I can't read the data metrics right now.", responseLang);
                 }
                 break;

             case 'trigger_download_all_zip':
                 console.log("Triggering download all files zip.");
                  if (typeof downloadAllFiles === 'function') {
                      downloadAllFiles(); // Assumes downloadAllFiles() exists in script.js
                  } else {
                       console.warn("downloadAllFiles function not found.");
                       await speak("I couldn't start the download for all files.");
                  }
                  break;

            case 'change_language':
                if (data.lang) {
                    console.log(`Changing language to: ${data.lang}`);
                    currentLang = data.lang;
                    // Test speech in new language
                    await speak("Language changed.", currentLang);
                } else {
                    console.error("Change language action missing lang parameter.");
                }
                break;

            case 'stop':
                console.log("Executing stop action.");
                await speak(responseMessage, responseLang); // Speak goodbye message
                // Do not restart listening
                return; // Exit function here

            case 'error':
                console.error(`Backend returned error: ${responseMessage}`);
                await speak(responseMessage, responseLang);
                break; // Break switch, then potentially restart listening

            default:
                console.warn(`Unknown action received: ${action}`);
                await speak("I received an action I don't know how to handle.", responseLang);
        }

        // --- Restart Listening (unless stopped) ---
        if (action !== 'stop') {
            startListening();
        }

    } catch (error) {
        console.error(`Error executing action '${action}':`, error);
        await speak(`Sorry, I encountered an error while trying to perform the action: ${error.message}`);
         // Optionally restart listening after execution error
         if (action !== 'stop') {
             startListening();
         }
    }
}


// --- Event Listeners ---
if (voiceBtn && recognition) {
    voiceBtn.addEventListener('click', () => {
        if (!isListening) {
            // Initial activation message
            speak("Hello, I’m SyncVoice. How can I help?", currentLang)
               .then(startListening)
               .catch(err => console.error("Error during initial speak/listen:", err));
        } else {
            stopListening();
        }
    });
} else if (voiceBtn) {
     voiceBtn.addEventListener('click', () => {
          showToast("Voice control not supported or initialized.", "error");
     });
}


if (recognition) {
    // --- Recognition Event Handlers ---
    recognition.onstart = () => {
        console.log("Recognition service started.");
        // Ensure synth is stopped if recognition starts (e.g., via external trigger)
         if (synth && synth.speaking) {
             synth.cancel();
         }
        updateAvatar('listening'); // Double ensure avatar state
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        console.log(`Recognition result: "${transcript}"`);
        stopListening(); // Stop listening now that we have a result
        processTranscript(transcript); // Process the result
    };

    recognition.onerror = (event) => {
        console.error("Recognition error:", event.error);
        isListening = false;
        updateAvatar('idle');
        let errorMsg = "An unknown speech recognition error occurred.";
        if (event.error === 'no-speech') {
            errorMsg = "I didn't hear anything. Please try speaking again.";
        } else if (event.error === 'audio-capture') {
            errorMsg = "I couldn't access the microphone. Please check permissions.";
        } else if (event.error === 'not-allowed') {
            errorMsg = "Microphone access was denied. Please allow access to use voice control.";
        } else if (event.error === 'network') {
            errorMsg = "A network error occurred during speech recognition.";
        } else if (event.error === 'aborted') {
            // Often happens when stopListening() is called, usually benign
            console.log("Recognition aborted, likely intentional stop.");
            return; // Don't speak an error in this case
        } else if (event.error === 'service-not-allowed' || event.error === 'bad-grammar') {
             errorMsg = "There seems to be an issue with the voice recognition service.";
        }
        speak(errorMsg); // Inform the user
    };

    recognition.onend = () => {
        console.log("Recognition service ended.");
        // This is called automatically when recognition stops, including after a result or error
        if (isListening) { // Check if it ended unexpectedly
             console.log("Recognition ended unexpectedly, attempting restart.");
             isListening = false; // Reset state before trying again
             updateAvatar('idle');
             // Optional: Automatically restart listening after a short delay
             // setTimeout(startListening, 500);
        }
    };
}


// --- Keyboard Shortcut ---
window.addEventListener('keydown', (e) => {
    // Example: Ctrl + Space to toggle listening
    if (e.ctrlKey && e.code === 'Space') {
        e.preventDefault(); // Prevent default space behavior
        if (voiceBtn) {
            voiceBtn.click(); // Simulate button click
        }
    }
});

// --- Helper functions to get text summaries from the UI ---
// These need to be implemented based on your specific HTML structure and data population in script.js

function summarizeCharts() {
    // Example: Check if charts have content or a 'no data' message
    const brandChart = document.getElementById('brand-chart');
    const categoryChart = document.getElementById('category-chart');
    // ... check other charts ...
    let summary = "Here's a summary of the visualizations: ";
    if (brandChart && !brandChart.textContent.includes('No data')) summary += "The brand chart shows sales and purchase quantities for top brands. ";
    else summary += "No brand data is currently displayed. ";
    if (categoryChart && !categoryChart.textContent.includes('No data')) summary += "The category chart shows similar data for top categories. ";
    else summary += "No category data is currently displayed. ";
    // Add summaries for monthly/weekly charts if available
    return summary;
}

function summarizeUploadResults() {
    const resultSummaryDiv = document.getElementById('result-summary');
    if (!resultSummaryDiv || resultSummaryDiv.classList.contains('d-none')) {
        return "No upload results are currently visible.";
    }
    try {
        const date = document.getElementById('result-date')?.textContent || 'N/A';
        const records = document.getElementById('result-records')?.textContent || 'N/A';
        const newRecords = document.getElementById('result-new')?.textContent || 'N/A';
        const updated = document.getElementById('result-updated')?.textContent || 'N/A';
        const sales = document.getElementById('result-daily-sales')?.textContent || 'N/A';
        const purchases = document.getElementById('result-daily-purchases')?.textContent || 'N/A';
        return `The latest upload summary for date ${date} shows: Total records processed ${records}. New records added: ${newRecords}. Existing records updated: ${updated}. Daily sales total: ${sales}. Daily purchases total: ${purchases}.`;
    } catch (err) {
        console.error("Error summarizing upload results:", err);
        return "I couldn't read the upload summary details.";
    }
}

function summarizeMetrics() {
    try {
        const totalRecords = document.getElementById('metric-total-records')?.textContent || 'N/A';
        const uniqueBrands = document.getElementById('metric-unique-brands')?.textContent || 'N/A';
        const uniqueCategories = document.getElementById('metric-unique-categories')?.textContent || 'N/A';
        const ratio = document.getElementById('metric-ratio')?.textContent || 'N/A';
        return `The current data preview metrics are: Total records: ${totalRecords}. Unique brands: ${uniqueBrands}. Unique categories: ${uniqueCategories}. Sales to purchase ratio: ${ratio}.`;
    } catch (err) {
        console.error("Error summarizing metrics:", err);
        return "I couldn't read the data preview metrics.";
    }
}

function readLogs() {
    if (!logContainer) return "The log container is not available.";
    const logEntries = logContainer.querySelectorAll('.log-entry');
    if (!logEntries || logEntries.length === 0) {
        return "There are no recent logs to read.";
    }
    // Read the last few logs (e.g., last 5)
    const recentLogs = Array.from(logEntries)
                          .slice(-5) // Get last 5 entries
                          .map(entry => entry.textContent.replace(/\[.*?\]\s*\d{4}-...-\d{2}\s*\d{2}:\d{2}:\d{2}\s*-\s*/, '')) // Clean up timestamps/levels
                          .join('. '); // Join with pauses
    return `Recent activity: ${recentLogs}`;
}


// --- Coordination with Chatbot ---
// Add an observer or modify chatbot.js to update lastSpokenBotResponse
// Example using MutationObserver (simplified):
const chatMessages = document.getElementById('chatMessages');
if (chatMessages) {
    const observer = new MutationObserver(mutations => {
        mutations.forEach(mutation => {
            if (mutation.addedNodes.length) {
                const lastMessage = chatMessages.lastElementChild;
                 // Check if the last message added is from the AI
                if (lastMessage && lastMessage.classList.contains('message') && lastMessage.classList.contains('ai')) {
                     // Extract text content, stripping HTML might be needed depending on chatbot.js formatting
                     lastSpokenBotResponse = lastMessage.innerText || lastMessage.textContent || "";
                     console.log("Updated lastSpokenBotResponse:", lastSpokenBotResponse);
                }
            }
        });
    });
    observer.observe(chatMessages, { childList: true });
}


console.log("Voice control script loaded.");
// Initial avatar state
updateAvatar('idle');