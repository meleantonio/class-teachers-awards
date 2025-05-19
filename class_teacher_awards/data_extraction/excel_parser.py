import pandas as pd
from typing import List, Dict, Any
from ..config import ECONOMICS_AT24_RESULTS_FILE, ECONOMICS_WT25_SURVEY_FILE, POSITIVE_FEEDBACK_SHEET_NAME

def get_teacher_names_from_excel(file_path: str, sheet_name: str, instructor_column_name: str = "Instructor") -> List[str]:
    """
    Extracts a unique list of teacher names from the specified Excel file and sheet.
    Assumes teacher names are in a column named 'Instructor'.
    """
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        if instructor_column_name not in df.columns:
            # Try to find a likely instructor column by checking for common variations
            possible_cols = [col for col in df.columns if isinstance(col, str) and "instructor" in col.lower()]
            if not possible_cols:
                 # Fallback: try to infer by looking for 'name' or 'teacher' if 'instructor' is not found
                possible_cols = [col for col in df.columns if isinstance(col, str) and ('name' in col.lower() or 'teacher' in col.lower())]
            
            if possible_cols:
                # Try the first likely column found
                original_instructor_column_name = instructor_column_name
                instructor_column_name = possible_cols[0]
                print(f"Warning: Column '{original_instructor_column_name}' not found in {file_path} -> {sheet_name}. Using '{instructor_column_name}' instead.")

            else:
                print(f"Error: Column '{instructor_column_name}' not found in {file_path} -> {sheet_name} and no alternative found.")
                return []
        
        # Drop rows where the instructor name is NaN or empty, then get unique names
        teacher_names = df[instructor_column_name].dropna().astype(str).str.strip().unique().tolist()
        return [name for name in teacher_names if name] # Filter out any empty strings after stripping
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return []
    except Exception as e:
        print(f"Error reading or processing Excel file {file_path}, sheet {sheet_name}: {e}")
        return []

def extract_positive_feedback_for_teacher(file_path: str, sheet_name: str, teacher_name: str, 
                                          instructor_column_name: str = "Instructor", 
                                          comment_column_name: str = "Positive comments") -> List[str]:
    """
    Extracts positive feedback for a specific teacher from an Excel file.
    Assumes teacher names are in 'Instructor' column and comments in 'Positive comments' column.
    Returns a list of comments.
    """
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        # Attempt to find the instructor column if the default is not present
        actual_instructor_column = instructor_column_name
        if instructor_column_name not in df.columns:
            possible_cols = [col for col in df.columns if isinstance(col, str) and "instructor" in col.lower()]
            if not possible_cols:
                possible_cols = [col for col in df.columns if isinstance(col, str) and ('name' in col.lower() or 'teacher' in col.lower())]

            if possible_cols:
                actual_instructor_column = possible_cols[0]
                print(f"Warning: Column '{instructor_column_name}' not found for instructor names in {file_path} -> {sheet_name}. Using '{actual_instructor_column}' instead.")
            else:
                print(f"Error: Instructor column '{instructor_column_name}' not found in {file_path} -> {sheet_name} and no alternative found.")
                return []

        # Attempt to find the comment column if the default is not present
        actual_comment_column = comment_column_name
        if comment_column_name not in df.columns:
            possible_cols = [col for col in df.columns if isinstance(col, str) and ("positive" in col.lower() and "comment" in col.lower())]
            if not possible_cols: # Broader search if specific "positive comment" not found
                 possible_cols = [col for col in df.columns if isinstance(col, str) and "comment" in col.lower()]

            if possible_cols:
                actual_comment_column = possible_cols[0]
                print(f"Warning: Column '{comment_column_name}' not found for comments in {file_path} -> {sheet_name}. Using '{actual_comment_column}' instead.")
            else:
                print(f"Error: Comment column '{comment_column_name}' not found in {file_path} -> {sheet_name} and no alternative found.")
                return []

        # Normalize teacher name for comparison (e.g., strip whitespace, lower case)
        normalized_teacher_name = teacher_name.strip().lower()
        
        # Filter DataFrame for the specific teacher (case-insensitive and whitespace-insensitive)
        # Ensure the column exists before trying to access .str
        if actual_instructor_column in df:
            teacher_df = df[df[actual_instructor_column].astype(str).str.strip().str.lower() == normalized_teacher_name]
        else: # Should have been caught above, but as a safeguard
            return []

        if teacher_df.empty:
            # print(f"No data found for teacher: {teacher_name} in {file_path} -> {sheet_name} using column '{actual_instructor_column}'")
            return []
        
        # Extract comments, drop NaN values, and convert to list
        comments = teacher_df[actual_comment_column].dropna().astype(str).tolist()
        return comments
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return []
    except Exception as e:
        print(f"Error reading or processing Excel file {file_path}, sheet {sheet_name} for teacher {teacher_name}: {e}")
        return []

def get_all_teacher_feedback(teachers_list: List[str]) -> Dict[str, List[str]]:
    """
    Aggregates positive feedback for a list of teachers from all configured Excel files.
    """
    all_feedback: Dict[str, List[str]] = {teacher: [] for teacher in teachers_list}
    
    files_to_process = [
        (ECONOMICS_AT24_RESULTS_FILE, POSITIVE_FEEDBACK_SHEET_NAME),
        (ECONOMICS_WT25_SURVEY_FILE, POSITIVE_FEEDBACK_SHEET_NAME)
    ]
    
    for teacher_name in teachers_list:
        for file_path, sheet_name in files_to_process:
            # The prompt implies that the column names for instructor and positive comments are consistent
            # across the 'Instructor feedback - positive' tabs in different files.
            # However, the Excel files provided in the prompt:
            # - "assets/Economics AT 24 Results.xlsx"
            # - "assets/WT25 Course Survey Qualitative comments - Economics v2.xlsx"
            # The third one "Economics AT 24 Results.xlsx" seems like a duplicate and likely refers to exam results, not feedback.
            # The prompt mentions "Instructor feedback - positive" tab for the first two for comments.
            # I'll assume the default column names 'Instructor' and 'Positive comments' are standard for these tabs.
            # If they differ, the `extract_positive_feedback_for_teacher` function has some fallback logic.

            # Let's try to determine actual column names for instructor and comments for each sheet.
            # For this, we'd ideally inspect the files or have more robust column name detection.
            # For now, relying on the function's internal fallback or specified defaults.
            # Based on the prompt, the relevant tab is "Instructor feedback - positive".
            # The column names are not explicitly given in the prompt for these tabs, so we rely on common names
            # or the fallback logic in `extract_positive_feedback_for_teacher`.
            
            # The prompt mentions the tab name specifically "Instructor feedback - positive"
            # For column names:
            # `Economics AT 24 Results.xlsx` in `Instructor feedback - positive` has "Instructor Name" and "If you would like to add any positive comments about this instructor, please do so here:"
            # `WT25 Course Survey Qualitative comments - Economics v2.xlsx` in `Instructor feedback - positive` has "Instructor" and "If you would like to add any positive comments about this class teacher, please do so here:"

            # We need to adjust column names per file or make the function more robust.
            # Given the exact column names aren't in the prompt for the *parser function arguments*,
            # the current implementation tries 'Instructor' and 'Positive comments' and has some fuzzy fallbacks.
            # Let's try to be more specific if possible based on typical Excel structures.

            instructor_col = "Instructor" # Default
            comment_col = "Positive comments" # Default

            if "AT 24 Results" in file_path:
                instructor_col = "Instructor Name" # More specific for this file
                comment_col = "If you would like to add any positive comments about this instructor, please do so here:"
            elif "WT25 Course Survey" in file_path:
                instructor_col = "Instructor" # Default seems okay here from file name
                comment_col = "If you would like to add any positive comments about this class teacher, please do so here:"


            feedback = extract_positive_feedback_for_teacher(
                file_path, 
                sheet_name, # This is POSITIVE_FEEDBACK_SHEET_NAME
                teacher_name,
                instructor_column_name=instructor_col,
                comment_column_name=comment_col
            )
            all_feedback[teacher_name].extend(feedback)
            
    return all_feedback

def get_all_teacher_names_from_sources() -> List[str]:
    """
    Collects all unique teacher names from all relevant Excel data sources.
    This can be used if a definitive list of teachers isn't provided upfront.
    """
    all_names = set()
    
    # Source 1: Economics AT 24 Results
    # Instructor column: "Instructor Name"
    # Comment column: "If you would like to add any positive comments about this instructor, please do so here:"
    names_at24 = get_teacher_names_from_excel(
        ECONOMICS_AT24_RESULTS_FILE, 
        POSITIVE_FEEDBACK_SHEET_NAME,
        instructor_column_name="Instructor Name" # Specific to this file's structure
    )
    all_names.update(names_at24)
    
    # Source 2: WT25 Course Survey
    # Instructor column: "Instructor"
    # Comment column: "If you would like to add any positive comments about this class teacher, please do so here:"
    names_wt25 = get_teacher_names_from_excel(
        ECONOMICS_WT25_SURVEY_FILE, 
        POSITIVE_FEEDBACK_SHEET_NAME,
        instructor_column_name="Instructor" # Assumed, or use default and let fallback work
    )
    all_names.update(names_wt25)
    
    return sorted(list(name for name in all_names if name)) # Ensure names are not empty

# Example usage (for testing purposes, will be removed or moved to a test file)
if __name__ == '__main__':
    # Create dummy .env if it doesn't exist for local testing of this module
    import os
    if not os.path.exists('../../.env'):
        with open('../../.env', 'w') as f:
            f.write('OPENAI_API_KEY="test_key"\n')

    # Make sure config can be loaded (adjust path if running this script directly)
    # This assumes running from project root for assets to be found with 'assets/...'
    # If running this script directly, paths in config might need adjustment or use absolute paths.
    
    print("Attempting to load teacher names from all sources...")
    all_available_teachers = get_all_teacher_names_from_sources()
    if all_available_teachers:
        print(f"Found {len(all_available_teachers)} unique teacher names: {all_available_teachers}")
        
        # Test with the first teacher found, or a known teacher name
        if all_available_teachers:
            test_teacher = all_available_teachers[0] 
            print(f"\nFetching feedback for teacher: {test_teacher}")
            
            feedback_at24 = extract_positive_feedback_for_teacher(
                ECONOMICS_AT24_RESULTS_FILE, 
                POSITIVE_FEEDBACK_SHEET_NAME, 
                test_teacher,
                instructor_column_name="Instructor Name",
                comment_column_name="If you would like to add any positive comments about this instructor, please do so here:"
            )
            print(f"Feedback from AT24 for {test_teacher}: {len(feedback_at24)} comments")
            # for comment in feedback_at24:
            #     print(f"- {comment}")

            feedback_wt25 = extract_positive_feedback_for_teacher(
                ECONOMICS_WT25_SURVEY_FILE, 
                POSITIVE_FEEDBACK_SHEET_NAME, 
                test_teacher,
                instructor_column_name="Instructor", # Assuming 'Instructor' is the column here
                comment_column_name="If you would like to add any positive comments about this class teacher, please do so here:"
            )
            print(f"Feedback from WT25 for {test_teacher}: {len(feedback_wt25)} comments")
            # for comment in feedback_wt25:
            #     print(f"- {comment}")

            print(f"\nFetching aggregated feedback for teacher: {test_teacher}")
            aggregated_feedback = get_all_teacher_feedback([test_teacher])
            if test_teacher in aggregated_feedback:
                print(f"Total comments for {test_teacher}: {len(aggregated_feedback[test_teacher])}")
                # for comment in aggregated_feedback[test_teacher]:
                #     print(f"  - {comment}")
            else:
                print(f"No aggregated feedback found for {test_teacher}")

        # Test with a teacher name that might exist in files (replace with actual name if known)
        # For example, if 'Dr. Example Name' is a teacher.
        # some_known_teacher = "Dr. Example Name" 
        # print(f"\nFetching feedback for a specific teacher: {some_known_teacher}")
        # specific_teacher_feedback = get_all_teacher_feedback([some_known_teacher])
        # if specific_teacher_feedback.get(some_known_teacher):
        #     print(f"Found comments for {some_known_teacher}:")
        #     for comment in specific_teacher_feedback[some_known_teacher]:
        #         print(f"  - {comment}")
        # else:
        #     print(f"No comments found for {some_known_teacher} or teacher not in the list.")

    else:
        print("Could not retrieve any teacher names from the Excel files.")

    # To make this testable, you'd need sample Excel files in `assets` matching the structure.
    # The paths are relative to the project root.
    # If running this file directly: python class_teacher_awards/data_extraction/excel_parser.py
    # Ensure your CWD is the project root or adjust paths.
    print("\nNote: For this example to run correctly, ensure:")
    print("1. The .env file exists at project root or OPENAI_API_KEY is set.")
    print("2. The 'assets' directory with specified Excel files exists at the project root.")
    print("3. `pandas` and `openpyxl` are installed.")
    print("4. Column names in the Excel files match expectations or fallbacks.") 