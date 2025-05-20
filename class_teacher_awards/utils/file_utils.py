import os
from ..config import RECOMMENDATION_DIR
import docx # For reading .docx files

def read_docx_file(file_path: str) -> str:
    """Reads the text content from a .docx file."""
    try:
        doc = docx.Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)
    except Exception as e:
        print(f"Error reading DOCX file {file_path}: {e}")
        return ""

def save_markdown_message(teacher_name: str, message_content: str) -> bool:
    """
    Saves the recommendation message to a markdown file.
    The filename will be [Teacher Name].md in the RECOMMENDATION_DIR.
    Returns True if successful, False otherwise.
    """
    # Sanitize teacher_name to be a valid filename
    # Replace spaces with underscores, remove characters not suitable for filenames
    # This is a basic sanitization, might need to be more robust depending on names
    safe_filename = "".join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in teacher_name)
    safe_filename = safe_filename.replace(' ', '_') + ".md"
    
    if not safe_filename.replace('_', '').replace('.md', ''): # check if filename became empty after sanitization
        print(f"Error: Could not generate a valid filename for teacher: {teacher_name}")
        return False

    # Ensure the output directory exists
    if not os.path.exists(RECOMMENDATION_DIR):
        try:
            os.makedirs(RECOMMENDATION_DIR)
            print(f"Created directory: {RECOMMENDATION_DIR}")
        except OSError as e:
            print(f"Error creating directory {RECOMMENDATION_DIR}: {e}")
            return False
            
    file_path = os.path.join(RECOMMENDATION_DIR, safe_filename)
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(message_content)
        print(f"Successfully saved recommendation for {teacher_name} to {file_path}")
        return True
    except IOError as e:
        print(f"Error saving file {file_path}: {e}")
        return False

# Example usage (for testing)
if __name__ == '__main__':
    # Create dummy .env if it doesn't exist for local testing of this module
    # (though this module doesn't directly use .env, config might be imported by other test code)
    import os
    # This pathing for .env assumes the script might be run from utils folder
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    if not os.path.exists(dotenv_path):
        project_root_dotenv = os.path.join(os.getcwd(), '.env') 
        if not os.path.exists(project_root_dotenv) and not os.path.exists('../../.env'):
             with open(project_root_dotenv, 'w') as f: 
                f.write('OPENAI_API_KEY="test_key_for_file_utils"\n')

    # Ensure RECOMMENDATION_DIR exists for the test or is created by the function
    # from ..config import RECOMMENDATION_DIR # Already imported at top
    print(f"Recommendation directory (from config): {RECOMMENDATION_DIR}")

    sample_teacher1 = "Dr. Jane Goodenough"
    sample_message1 = f"""# {sample_teacher1}

# Recommendation message:

Dr. Goodenough is an exceptional educator who consistently inspires students.
Her innovative teaching methods and dedication are truly commendable.

Fantastic job, {sample_teacher1}!"""

    print(f"\nAttempting to save message for: {sample_teacher1}")
    success1 = save_markdown_message(sample_teacher1, sample_message1)
    print(f"Save successful: {success1}")

    sample_teacher2 = "Prof. Albus Dumbledore / Headmaster"
    sample_message2 = f"""# {sample_teacher2}

# Recommendation message:

Professor Dumbledore's wisdom and guidance have profoundly impacted countless students.
He fosters an environment of critical thinking and magical discovery.

Fantastic job, {sample_teacher2}!"""
    print(f"\nAttempting to save message for: {sample_teacher2}")
    success2 = save_markdown_message(sample_teacher2, sample_message2)
    print(f"Save successful: {success2}")

    # Test with a name that might cause issues if not sanitized
    sample_teacher3 = "Teacher O'Malley & Friend*"
    sample_message3 = f"""# {sample_teacher3}

# Recommendation message:

Works well.

Fantastic job, {sample_teacher3}!"""
    print(f"\nAttempting to save message for: {sample_teacher3}")
    success3 = save_markdown_message(sample_teacher3, sample_message3)
    print(f"Save successful: {success3}")

    print(f"\nCheck the '{RECOMMENDATION_DIR}' directory for the generated files.") 