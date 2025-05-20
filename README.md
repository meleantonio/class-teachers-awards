# Class Teacher Awards Recommendation Generator

This Python package automates the generation of recommendation messages for class teaching awards. It extracts information about teachers from Excel files (student feedback) and EML files (professor opinions), then uses OpenAI's GPT-4o model to craft personalized recommendation messages. The style and tone of these messages can be guided by providing example recommendation documents (.docx files) in an `examples` folder.

## Features

- Parses student feedback from multiple Excel files.
- Extracts professor opinions from EML email files (dynamically discovers all `.eml` files in the `assets` folder).
- Reads example recommendation `.docx` files from an `examples` folder to guide generation style.
- Utilizes OpenAI GPT-4o for generating recommendation narratives.
- Formats messages in Markdown, ready for submission.
- Saves each recommendation to a separate file named after the teacher.

## Project Structure

```
class-teachers-awards/
├── class_teacher_awards/       # Main package source code
│   ├── __init__.py
│   ├── data_extraction/    # Modules for parsing Excel and EML files
│   │   ├── __init__.py
│   │   ├── excel_parser.py
│   │   └── eml_parser.py
│   ├── llm/                  # Module for OpenAI API interaction
│   │   ├── __init__.py
│   │   ├── alias_generator.py
│   │   └── message_generator.py
│   ├── utils/                # Utility functions (e.g., file saving, docx reading)
│   │   ├── __init__.py
│   │   └── file_utils.py
│   ├── config.py           # Configuration (file paths, API model)
│   └── main.py             # Main script to orchestrate the process
├── tests/                  # Unit tests
│   └── ... 
├── assets/                 # Input data files (Excel, EML)
│   └── ... 
├── examples/               # Example .docx recommendation files for style guidance
│   └── ...
├── recommendation_messages/  # Output directory for generated Markdown files
├── .env                    # For storing OpenAI API Key (MUST BE CREATED MANUALLY)
├── .gitignore
├── README.md
├── pyproject.toml          # Project metadata and build system configuration
├── requirements.txt        # Runtime dependencies (includes pandas, openpyxl, python-dotenv, openai, python-docx)
└── requirements-dev.txt    # Development dependencies
```

## Setup and Installation

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd class-teachers-awards
    ```

2.  **Create a Virtual Environment:**
    It's highly recommended to use a virtual environment to manage project dependencies.
    ```bash
    python3 -m venv .venv
    ```

3.  **Activate the Virtual Environment:**
    -   On macOS and Linux:
        ```bash
        source .venv/bin/activate
        ```
    -   On Windows:
        ```bash
        .\venv\Scripts\activate
        ```

4.  **Install Dependencies:**
    Install the runtime dependencies (this includes `python-docx` for reading example files):
    ```bash
    pip install -r requirements.txt
    ```
    Install the development dependencies (for testing and linting):
    ```bash
    pip install -r requirements-dev.txt
    ```

5.  **Create `.env` file:**
    In the project root directory, create a file named `.env` and add your OpenAI API key:
    ```env
    OPENAI_API_KEY="your_openai_api_key_here"
    ```
    Replace `"your_openai_api_key_here"` with your actual key.

6.  **(Optional) Create `examples` folder:**
    If you wish to guide the style and tone of the generated recommendations, create a folder named `examples` in the project root. Place one or more `.docx` files containing example recommendation messages in this folder. The system will automatically detect and use them.

## Usage

Once the setup is complete, the virtual environment is activated, and your `assets` directory is populated with the required data files (and optionally, the `examples` directory with your `.docx` files), you can run the main script.

To generate recommendation messages for **all** teachers found in the data sources:

```bash
python -m class_teacher_awards.main
```

To generate recommendation messages for **specific** teachers using command-line arguments:

Use the `-t` or `--teachers` flag followed by the list of teacher names. If a teacher's name contains spaces, enclose it in quotes. This option is mutually exclusive with `--teachers-file`.

Example for one teacher:
```bash
python -m class_teacher_awards.main -t "Dr. Ada Lovelace"
```

Example for multiple teachers:
```bash
python -m class_teacher_awards.main -t "Dr. Ada Lovelace" "Mr. Charles Babbage"
```

To generate recommendation messages for **specific** teachers listed in a file:

Use the `--teachers-file` flag followed by the path to a `.txt` or `.csv` file. This option is mutually exclusive with `-t`/`--teachers`.

-   **`.txt` file format:** One teacher name per line.
    Example (`my_teachers.txt`):
    ```
    Dr. Ada Lovelace
    Mr. Charles Babbage
    Prof. Grace Hopper
    ```

-   **`.csv` file format:** Teacher names in the first column. The script currently does not expect a header row.
    Example (`my_teachers.csv`):
    ```csv
    Dr. Ada Lovelace,Department A
    Mr. Charles Babbage,Department B
    Prof. Grace Hopper,Department A 
    ```
    (Only "Dr. Ada Lovelace", "Mr. Charles Babbage", "Prof. Grace Hopper" will be extracted)

Example command:
```bash
python -m class_teacher_awards.main --teachers-file path/to/my_teachers.txt
```
Or for a CSV file:
```bash
python -m class_teacher_awards.main --teachers-file path/to/my_teachers.csv
```

The generated markdown files will be saved in the `recommendation_messages/` directory.

## Data Files

The application expects the following data files (paths can be configured in `class_teacher_awards/config.py`):

-   **Student Feedback (Excel):**
    -   `assets/Economics AT 24 Results.xlsx` (Sheet: `Instructor feedback - positive`)
    -   `assets/WT25 Course Survey Qualitative comments - Economics v2.xlsx` (Sheet: `Instructor feedback - positive`)
    *(Note: The Excel parser attempts to find instructor and comment columns dynamically but works best if column names like "Instructor Name" or "Instructor" and comment columns with "positive comments" are used.)*

-   **Professor Opinions (EML):**
    -   All `.eml` files placed in the `assets/` directory will be automatically processed.

-   **Example Recommendation Files (.docx) (Optional):**
    -   Any `.docx` files placed in an `examples/` directory at the project root will be used to guide the style and tone of the generated recommendations.

## Development

### Testing

Unit tests are located in the `tests/` directory. Ensure you have activated your virtual environment and installed development dependencies (`pip install -r requirements-dev.txt`).

To run tests:

```bash
pytest
```

### Linting and Formatting

This project uses Ruff for linting and formatting. Ensure development dependencies are installed.

To check for linting issues:
```bash
ruff check .
```

To automatically format the code:
```bash
ruff format .
```

## Configuration

Key configurations are managed in `class_teacher_awards/config.py`:
-   OpenAI Model (`GPT_MODEL`)
-   File paths for Excel data sources (`ECONOMICS_AT24_RESULTS_FILE`, `ECONOMICS_WT25_SURVEY_FILE`).
-   Path pattern for EML files (`EML_FILE_PATHS = glob.glob("assets/*.eml")`).
-   Path pattern for example DOCX files (`EXAMPLE_DOCX_FILES = glob.glob("examples/*.docx")`).
-   Output directory for recommendations (`RECOMMENDATION_DIR`).

The OpenAI API key is loaded from the `.env` file. 