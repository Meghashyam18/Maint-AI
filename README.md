# 🤖 MAINT AI — AI Field Maintenance Report Generator

**MAINT AI** is an AI-powered equipment maintenance history and reporting system. It is designed to assist field technicians in looking up historical equipment service logs, conducting new machine inspections with photographic evidence, and automatically generating professional, structured PDF maintenance reports using **Gemini 2.5 Flash**.

---

## 💡 What is the Project About?
MAINT AI acts as an intelligent assistant for industrial field maintenance technicians. In large factories, manufacturing plants, or utility fields, machines generate massive amounts of maintenance tickets. Technicians often write brief, unstructured notes, and take pictures of faults. 

This project solves two major industrial bottlenecks:
1. **Disorganized Historical Data**: It provides an interface to instantly access, query, and search through 20,000 historical service records.
2. **Time-Consuming Manual Reporting**: Instead of requiring a technician to return to an office and manually draft a PDF document, they simply upload a photo and write a few sentences. The system's multimodal LLM automatically formats it into an official, structured report with actionable suggestions.

---

## 🛠️ Where is it Useful?
* **Heavy Manufacturing & Factories**: Keeping track of machine lifecycles (Lathes, Presses, Milling machines) to trace recurring faults.
* **On-Site Field Services**: Field engineers servicing telecom towers, power grids, or HVAC systems can document repairs on the go.
* **Quality Assurance & Safety Inspections**: Automating safety audits where physical proof (a photograph) must be paired with structured textual records.
* **Predictive Maintenance Preparation**: Turning messy, unstructured notes into clean, categorized, and structured datasets suitable for future machine learning and trend modeling.

---


## 📁 Directory Structure & Component Mapping

Below is the layout of the project files and directories, along with their roles in the system:

```text
SHYAM_NV_CODE/
├── data/
│   └── maintenance.csv        # Core dataset with 20,000 historical service records
├── pages/
│   ├── maintenance_history.py  # Browse equipment history, metrics, and filter logs
│   ├── new_inspection.py      # The MAINT AI diagnostic page (New Inspection & PDF creator)
│   └── generated_reports.py   # Repository for viewing/downloading generated reports
├── prompts/
│   └── report_prompt.txt      # Versioned AI system prompt and instructions
├── reports/                   # Output folder where generated PDF reports are saved
├── uploads/                   # Temporary directory for uploaded technician photos
├── utils/
│   ├── data_loader.py         # Standardizes and caches Pandas DataFrame loads
│   └── report_utils.py        # Helper routines to build filenames and format metadata
├── app.py                     # App entrypoint and sidebar navigation layout
├── config.py                  # Single source of truth for column keys, models, and paths
├── llm.py                     # Multimodal Gemini API client integration & schema verification
├── report_generator.py        # ReportLab engine formatting text/image data to PDF
├── .env                       # Environment variables containing local configurations (e.g. API keys)
└── requirements.txt           # Python dependency specifications
```

---

## 📊 Dataset Specifications
The system utilizes a structured tabular dataset of historical maintenance events stored in `data/maintenance.csv`. 

* **Volume**: **20,000 records** logged between **January 14, 2015** and **January 13, 2016**.
* **Assets**: **99 unique machines** labeled `A1` through `A99`.
* **Servicing Frequency**: An average of **~202 tickets per machine** per year.
* **Workforce**: **7 individual technicians** who perform repairs either individually or in teams.

### Ingestion Data Schema:
1. `mach` (Machine ID): Primary asset identifier (e.g., `A71`).
2. `date_received`: Log date (ingested in `%d/%m/%Y` format).
3. `issue`: The symptom or fault reported.
4. `info`: Repair details and technician diagnostic notes.
5. `tech`: The name(s) of the service technician(s).

---

## ⚙️ How the Application Works

### 1. Navigation Menu (app.py)
A sidebar menu allows users to switch between three core interfaces:
* **Maintenance History**: Review machine statistics, browse complete servicing logs, look up issues, and see logs of individual technicians who worked on that machine.
* **MAINT AI**: Conduct a real-time inspection.
* **Generated Reports**: Check, search, and download generated PDF logs.

### 2. Live Inspection Workflow (MAINT AI)
1. **Asset Selection**: Technicians select an existing machine from the dropdown menu (sorted numerically from `A1` to `A99`) or choose the **"➕ Enter new machine ID…"** option to manually key in a custom ID (e.g., a new production line or asset identifier).
2. **Details & Photo Upload**: Technicians enter observations and upload a machine/fault photo.
3. **AI Generation**: Clicking **"Generate AI Maintenance Report"** triggers the multimodal pipeline.
4. **PDF Generation**: ReportLab compiles a structured layout including a table of metadata, technician notes, AI summary, and visual recommendations.

### 3. AI Cognitive Engine (llm.py)
* **Model**: `gemini-2.5-flash-lite` (or chosen Gemini API model).
* **Multimodal input**: Feeds both the technician notes and the raw image data to the model.
* **Schema Validation**: The AI is instructed to return a structured JSON response. The application validates this payload to ensure it contains key fields (`maintenance_summary`, `image_observations`, `current_machine_status`, `recommendations`) and that `current_machine_status` is one of the allowed categories:
  * `Operational`
  * `Maintenance Required`
  * `Requires Further Inspection`
* **Metadata Protection**: Authoritative metadata (like machine ID, inspection date, technician name, and reported issue) is **injected by the system**, overwriting any AI fields to ensure zero hallucination of factual registry values.
* **Retry Capability**: Includes connection error guards that automatically retry transient failures (e.g., connection reset or timeout).

---

## 🚀 Setup & Execution Guide

### Prerequisites
* Python 3.10+
* A valid **Gemini API Key** from Google AI Studio.

### 1. Installation & Environment Configuration
When setting up this project, the following core Python libraries are installed to power the application:

* **`streamlit`**: The web application framework. It provides the reactive UI components (buttons, file uploaders, dataframes, dropdowns) and handles page routing in `app.py`.
* **`pandas`**: The analytical library. It processes the large-scale `maintenance.csv` database containing 20,000 service logs, enabling lightning-fast grouping, filtering, and metric calculation.
* **`google-genai`**: The Google GenAI SDK. It integrates the application with Google's large language models (specifically **Gemini 2.5 Flash**) for multimodal inputs (analyzing both raw text notes and raw images together).
* **`reportlab`**: The document rendering engine. It dynamically constructs custom multi-page PDF maintenance documents containing status tables, observations, and recommendations.
* **`Pillow`**: The image processing library. It parses, reads, and formats the raw JPG/PNG photograph uploads before they are sent to the Gemini API.
* **`python-dotenv`**: The secure settings manager. It reads API credentials from a local hidden `.env` file and safely injects them into the running script.

To install these modules, navigate to the project directory, establish an isolated environment, and run the dependency installer:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
.\venv\Scripts\activate

# Install required libraries
pip install -r requirements.txt
```


### 2. Configure Environment Variables
Create a file named `.env` in the root folder and add your Gemini API Key:
```env
GEMINI_API_KEY=your_actual_api_key_here
```

### 3. Launching the App
Run the Streamlit server from the command line:
```bash
streamlit run app.py
```
Open the local URL displayed (usually `http://localhost:8501`) in your browser.

---

## 🔮 Future Scope
* **Predictive Diagnostics**: Train regression or classification models on the 20,000 historical records to predict machine failure intervals and estimate when a specific asset (e.g. `A72`) is next due for breakdown.
* **Voice-to-Text Integration**: Enable hands-free operation so technicians can dictate their observations directly into the system, which are then transcribed and analyzed.
* **Database Integration**: Connect the system to a live SQL database (e.g., PostgreSQL or Oracle) to dynamically read and update records in real time instead of working with a local static CSV file.
* **Offline Synchronization Capability**: A mobile companion client that lets field technicians draft reports in offline mode (e.g., in a basement or remote field with no cell service) and upload/sync them once a connection is re-established.
* **Automated Parts Requisition**: Integrate with enterprise ERP systems (like SAP) to automatically initiate replacement parts ordering based on the AI recommendations.

