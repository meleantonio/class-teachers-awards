import os
import glob # Import glob module
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env file

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_MODEL = "gpt-4o"

# Excel file paths and sheet names
ECONOMICS_AT24_RESULTS_FILE = "assets/Economics AT 24 Results.xlsx"
ECONOMICS_WT25_SURVEY_FILE = "assets/WT25 Course Survey Qualitative comments - Economics v2.xlsx"
POSITIVE_FEEDBACK_SHEET_NAME = "Instructor feedback - positive"

# EML file paths - now dynamically finds all .eml files in assets
EML_FILE_PATHS = glob.glob("assets/*.eml")

# Example DOCX file paths for guiding style and tone
EXAMPLE_DOCX_FILES = glob.glob("examples/*.docx")

# Output directory
RECOMMENDATION_DIR = "recommendation_messages" 