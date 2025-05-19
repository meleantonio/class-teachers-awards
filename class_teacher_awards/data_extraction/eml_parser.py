import email
import re
from email import policy
from email.parser import BytesParser
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Set
from ..config import EML_FILE_PATHS
from ..llm.alias_generator import generate_teacher_aliases

def parse_eml_content(file_path: str) -> str:
    """Parses an EML file and returns its text content."""
    try:
        with open(file_path, 'rb') as fp:
            msg = BytesParser(policy=policy.default).parse(fp)
        
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                
                if content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or 'utf-8' # Fallback to utf-8
                    try:
                        body += payload.decode(charset)
                    except (UnicodeDecodeError, AttributeError):
                        # If decoding fails, try default charsets or skip if it's not bytes
                        if isinstance(payload, bytes):
                            try: body += payload.decode('utf-8')
                            except UnicodeDecodeError: 
                                try: body += payload.decode('latin-1')
                                except UnicodeDecodeError: pass # Skip if all fail
                        elif isinstance(payload, str):
                             body += payload # Already a string
                elif content_type == "text/html":
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or 'utf-8'
                    try:
                        html_content = payload.decode(charset)
                        soup = BeautifulSoup(html_content, 'html.parser')
                        body += soup.get_text()
                    except (UnicodeDecodeError, AttributeError):
                        if isinstance(payload, bytes):
                            try: html_content = payload.decode('utf-8')
                            except UnicodeDecodeError: 
                                try: html_content = payload.decode('latin-1')
                                except UnicodeDecodeError: html_content = None
                            if html_content:
                                soup = BeautifulSoup(html_content, 'html.parser')
                                body += soup.get_text()
                        elif isinstance(payload, str):
                             soup = BeautifulSoup(payload, 'html.parser') # Already a string
                             body += soup.get_text()
                body += "\n" # Ensure separation between parts

        else: # Not multipart, try to get body directly
            payload = msg.get_payload(decode=True)
            charset = msg.get_content_charset() or 'utf-8'
            content_type = msg.get_content_type()
            try:
                decoded_payload = payload.decode(charset)
                if content_type == 'text/html':
                    soup = BeautifulSoup(decoded_payload, 'html.parser')
                    body = soup.get_text()
                elif content_type == 'text/plain':
                    body = decoded_payload
                else: # Fallback for other types like text/* if not html/plain
                    body = decoded_payload 
            except (UnicodeDecodeError, AttributeError): # Similar fallback for non-multipart
                if isinstance(payload, bytes):
                    try: decoded_payload = payload.decode('utf-8')
                    except UnicodeDecodeError: 
                        try: decoded_payload = payload.decode('latin-1')
                        except UnicodeDecodeError: decoded_payload = ""
                    if content_type == 'text/html' and decoded_payload:
                        soup = BeautifulSoup(decoded_payload, 'html.parser')
                        body = soup.get_text()
                    else:
                        body = decoded_payload # Use as is if plain or becomes empty
                elif isinstance(payload, str):
                    if content_type == 'text/html':
                        soup = BeautifulSoup(payload, 'html.parser')
                        body = soup.get_text()
                    else:
                        body = payload # Already a string, use as is

        return "\n".join([line.strip() for line in body.splitlines() if line.strip()])
    except Exception as e:
        print(f"Error parsing EML file {file_path}: {e}")
        return ""

def extract_professors_opinions_for_teacher(
    teacher_name: str, 
    eml_texts: List[str], 
    context_window_lines: int = 2,
    teacher_aliases: List[str] = None # Added teacher_aliases parameter
) -> List[str]:
    """Extracts opinions about a specific teacher from EML text content, including aliases."""
    opinions: Set[str] = set() # Use a set to store unique opinions
    
    # Normalize teacher_name and aliases for more robust matching
    normalized_teacher_name = " ".join(teacher_name.lower().split())
    search_terms = [normalized_teacher_name]
    if teacher_aliases:
        search_terms.extend([" ".join(alias.lower().split()) for alias in teacher_aliases if alias.strip()])

    for text_content in eml_texts:
        lines = text_content.splitlines()
        for i, line in enumerate(lines):
            normalized_line = " ".join(line.lower().split()) # Normalize line for searching
            for term in search_terms:
                # Use word boundaries for more precise matching of names/aliases
                # This helps avoid matching "Tom" in "Tomorrow" if "Tom" is an alias for Thomas.
                # Regex:  (term)  - case insensitive due to prior .lower() and normalization
                if re.search(rf'(?<!\w){re.escape(term)}(?!\w)', normalized_line):
                    start_index = max(0, i - context_window_lines)
                    end_index = min(len(lines), i + context_window_lines + 1)
                    context_snippet = "\n".join(lines[start_index:end_index]).strip()
                    if context_snippet: # Ensure snippet is not empty
                        opinions.add(context_snippet)
                    break # Found a term in this line, move to next line
    return sorted(list(opinions))

def get_all_professors_opinions(teachers_list: List[str]) -> Dict[str, List[str]]:
    """Gets all professor opinions for a list of teachers from EML files, using aliases."""
    all_opinions: Dict[str, List[str]] = {name: [] for name in teachers_list}
    
    if not EML_FILE_PATHS:
        print("No EML file paths configured. Skipping professor opinion extraction.")
        return all_opinions

    print(f"Parsing {len(EML_FILE_PATHS)} EML files for professor opinions...")
    eml_contents = [parse_eml_content(file_path) for file_path in EML_FILE_PATHS if file_path]
    # Filter out any empty strings that might result from parsing errors
    eml_contents = [content for content in eml_contents if content.strip()]

    if not eml_contents:
        print("No content successfully parsed from EML files.")
        return all_opinions

    print("Extracting opinions for each teacher...")
    for teacher_name in teachers_list:
        print(f"  Generating aliases for {teacher_name}...")
        # Pass the full teachers_list for context to alias generator
        aliases = generate_teacher_aliases(teacher_name, teachers_list)
        if aliases:
            print(f"    Found aliases for {teacher_name}: {aliases}")
        else:
            print(f"    No distinct aliases found or suggested for {teacher_name}.")
        
        # Pass aliases to the extraction function
        opinions = extract_professors_opinions_for_teacher(teacher_name, eml_contents, teacher_aliases=aliases)
        all_opinions[teacher_name] = opinions
        if opinions:
            print(f"    Found {len(opinions)} opinion snippets for {teacher_name}.")

    return all_opinions

# Example usage (for testing)
if __name__ == '__main__':
    # Dummy config for testing this module directly (paths are relative to this file)
    # Adjust EML_FILE_PATHS if running this script directly and assets are elsewhere.
    # This assumes that if you run this, you are in the `data_extraction` directory
    # and `assets` is two levels up.
    
    # A better way for testing is to have sample EMLs and run from project root.
    # For now, let's assume EML_FILE_PATHS from config are relative to project root.
    
    # To test, you would need the EML files in the `assets` directory.
    # Create dummy .env if it doesn't exist for local testing of this module
    import os
    # This pathing for .env assumes the script might be run from data_extraction folder
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    if not os.path.exists(dotenv_path):
        # Or from project root: os.path.join(os.getcwd(), '.env')
        # Let's assume project root for consistency with how config.py loads it.
        project_root_dotenv = os.path.join(os.getcwd(), '.env') 
        # This check is if you `python class_teacher_awards/data_extraction/eml_parser.py` from root.
        if not os.path.exists(project_root_dotenv) and not os.path.exists('../../.env'):
             with open(project_root_dotenv, 'w') as f: # Create in current dir if not found elsewhere
                f.write('OPENAI_API_KEY="test_key_for_eml_parser"\n')
    
    # Sample teacher names for testing (replace with actual names if possible)
    sample_teachers = ["Dr. Example Person", "Prof. Another Name"] 
    # You would get this list from the excel parser or other source in a real run.

    print(f"EML files to be processed (from config): {EML_FILE_PATHS}\n")

    print("Parsing EML files...")
    raw_eml_contents = []
    for fp in EML_FILE_PATHS:
        # Assuming EML_FILE_PATHS in config.py are relative to project root
        # If running this script from `data_extraction`, path needs to be `../../assets/...`
        # For robust testing, best to run from project root or use absolute paths in temp config.
        # Let's try to make path relative to this script for simple `python eml_parser.py` test.
        abs_path = os.path.join(os.path.dirname(__file__), '..', '..', fp)
        if not os.path.exists(abs_path):
            print(f"Warning: EML file {fp} (resolved to {abs_path}) not found. Skipping.")
            # Fallback to assuming it's already a correct path if run from project root
            if os.path.exists(fp):
                abs_path = fp # use it as is
            else:
                continue

        print(f"Reading: {abs_path}")
        content = parse_eml_content(abs_path)
        if content:
            print(f"Successfully parsed: {abs_path} (length: {len(content)} chars)")
            raw_eml_contents.append(content)
        else:
            print(f"Failed to parse or empty content: {abs_path}")

    if not raw_eml_contents:
        print("\nNo EML content could be parsed. Ensure EML files exist at specified paths.")
    else:
        print(f"\nSuccessfully parsed {len(raw_eml_contents)} EML files.")

        # Test extraction for sample teachers
        print("\nExtracting opinions for sample teachers:")
        for teacher in sample_teachers:
            opinions = extract_professors_opinions_for_teacher(teacher, raw_eml_contents)
            if opinions:
                print(f"\nOpinions found for {teacher}:")
                for i, op in enumerate(opinions):
                    print(f"  Opinion {i+1}:\n{op}\n---")
            else:
                print(f"\nNo specific opinions found for {teacher}.")
        
        print("\nTesting aggregated opinions function:")
        all_opinions_map = get_all_professors_opinions(sample_teachers)
        for teacher, ops_list in all_opinions_map.items():
            if ops_list:
                print(f"\nAggregated opinions for {teacher}:")
                for i, op_text in enumerate(ops_list):
                    print(f"  Aggregated Opinion {i+1}:\n{op_text}\n---")
            else:
                print(f"\nNo aggregated opinions found for {teacher}.")

    print("\nNote: For this example to run correctly, ensure:")
    print("1. The .env file exists or OPENAI_API_KEY is set (dummy created if not found).")
    print("2. The 'assets' directory with specified EML files exists relative to project root.")
    print("3. `extract_professors_opinions_for_teacher` logic might need tuning based on actual EML content and teacher name formats.") 