import os
import argparse
import csv # Added for CSV file reading
from typing import List, Optional

from .config import OPENAI_API_KEY # To check if API key is set
from .data_extraction.excel_parser import get_all_teacher_feedback, get_all_teacher_names_from_sources
from .data_extraction.eml_parser import get_all_professors_opinions
from .llm.message_generator import generate_recommendation_message
from .utils.file_utils import save_markdown_message

def process_teacher_awards(specific_teachers: Optional[List[str]] = None):
    """
    Main function to orchestrate the generation of teaching award recommendations.
    If specific_teachers is provided, only those teachers will be processed.
    Otherwise, all teachers from data sources will be processed.
    """
    print("Starting teaching award recommendation process...")

    # Check for OpenAI API Key early
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY is not set in the .env file or environment variables.")
        print("Please set it up to proceed with message generation.")
        return

    # 1. Get list of teachers
    teachers_list: List[str] = []
    if specific_teachers:
        teachers_list = specific_teachers
        print(f"\nStep 1: Using provided list of {len(teachers_list)} specific teachers: {teachers_list}")
    else:
        # Option A: Get all unique teacher names from the Excel data sources
        print("\nStep 1: Retrieving all teacher names from data sources...")
        try:
            teachers_list = get_all_teacher_names_from_sources()
            if not teachers_list:
                print("No teachers found in the data sources. Exiting.")
                return
            print(f"Found {len(teachers_list)} teachers: {teachers_list}")
        except Exception as e:
            print(f"Error retrieving teacher list: {e}")
            return

    # Option B: Use a predefined list (for testing or specific runs)
    # teachers_list = ["Teacher Name 1", "Teacher Name 2"] # Replace with actual names for testing

    # 2. For each teacher, gather data and generate recommendation
    print("\nStep 2: Processing each teacher...")
    
    # Get all feedback and opinions in batch if possible, or one by one
    # The current parsers are designed to take a list of teachers and return dicts
    print("Fetching all student feedback...")
    all_student_feedback = get_all_teacher_feedback(teachers_list)
    
    print("Fetching all professor opinions...")
    all_prof_opinions = get_all_professors_opinions(teachers_list)

    successful_generations = 0
    failed_generations = 0

    for teacher_name in teachers_list:
        print(f"\nProcessing: {teacher_name}")

        # Get specific data for the current teacher
        student_feedback = all_student_feedback.get(teacher_name, [])
        prof_opinions = all_prof_opinions.get(teacher_name, [])

        if not student_feedback and not prof_opinions:
            print(f"No specific student feedback or professor opinions found for {teacher_name}. Generating a general positive recommendation.")
        
        print(f"  Found {len(student_feedback)} student feedback entries.")
        print(f"  Found {len(prof_opinions)} professor opinion snippets.")

        # 3. Generate recommendation message using OpenAI
        print(f"  Generating recommendation message for {teacher_name}...")
        recommendation_content = generate_recommendation_message(
            teacher_name,
            student_feedback,
            prof_opinions
        )
        
        if "Error:" in recommendation_content: # Check if generation itself reported an error
            print(f"  Failed to generate message for {teacher_name}. Reason: {recommendation_content}")
            failed_generations += 1
            # Save the error message file anyway for tracking
            save_markdown_message(teacher_name, recommendation_content)
            continue

        # 4. Save the message
        print(f"  Saving recommendation for {teacher_name}...")
        if save_markdown_message(teacher_name, recommendation_content):
            successful_generations += 1
        else:
            print(f"  Failed to save message for {teacher_name}.")
            failed_generations += 1

    print("\n-------------------------------------------------")
    print("Teaching award recommendation process completed.")
    print(f"Successfully generated and saved: {successful_generations} recommendations.")
    print(f"Failed attempts (generation or saving): {failed_generations} recommendations.")
    print("-------------------------------------------------")

def main():
    """Main entry point with command-line argument parsing."""
    parser = argparse.ArgumentParser(description="Generate teaching award recommendations.")
    group = parser.add_mutually_exclusive_group() # For mutually exclusive --teachers and --teachers-file
    group.add_argument(
        "-t", "--teachers",
        nargs='+',
        metavar='"Teacher Name"',
        help="Specify one or more teacher names to process (enclosed in quotes if spaces). Mutually exclusive with --teachers-file.",
        default=None
    )
    group.add_argument(
        "--teachers-file",
        metavar='FILE_PATH',
        help="Path to a .txt or .csv file containing a list of teacher names (one per line in .txt, or first column in .csv). Mutually exclusive with --teachers.",
        default=None
    )
    args = parser.parse_args()

    teacher_names_to_process: Optional[List[str]] = None

    if args.teachers_file:
        try:
            teacher_names_to_process = []
            file_path = args.teachers_file
            if not os.path.exists(file_path):
                print(f"Error: Teachers file not found at {file_path}")
                return

            if file_path.lower().endswith('.csv'):
                with open(file_path, mode='r', encoding='utf-8', newline='') as csvfile:
                    reader = csv.reader(csvfile)
                    for row in reader:
                        if row: # Ensure row is not empty
                            teacher_name = row[0].strip()
                            if teacher_name: # Ensure name is not empty after strip
                                teacher_names_to_process.append(teacher_name)
            elif file_path.lower().endswith('.txt'):
                with open(file_path, mode='r', encoding='utf-8') as txtfile:
                    for line in txtfile:
                        teacher_name = line.strip()
                        if teacher_name: # Ensure name is not empty
                            teacher_names_to_process.append(teacher_name)
            else:
                print("Error: Invalid file type for --teachers-file. Please use .txt or .csv.")
                return
            
            if not teacher_names_to_process:
                print(f"No teacher names found in the file: {file_path}")
                return

        except Exception as e:
            print(f"Error reading teachers file {args.teachers_file}: {e}")
            return
    elif args.teachers:
        teacher_names_to_process = args.teachers

    # Ensure .env is loaded (important if running as a script)
    from dotenv import load_dotenv
    # Prefer .env in project root, then one level up from this file's package dir (class_teacher_awards/ -> project_root)
    project_root_dotenv = os.path.join(os.getcwd(), '.env')
    package_parent_dotenv = os.path.join(os.path.dirname(__file__), '..', '.env')

    if os.path.exists(project_root_dotenv):
        load_dotenv(project_root_dotenv)
    elif os.path.exists(package_parent_dotenv):
        load_dotenv(package_parent_dotenv)
    else:
        if not OPENAI_API_KEY: # Check if it was set by environment already
            print("Warning: .env file not found in project root or parent directory. Ensure OPENAI_API_KEY is set.")

    process_teacher_awards(specific_teachers=teacher_names_to_process)

if __name__ == '__main__':
    # This allows running the main process directly using:
    # python -m class_teacher_awards.main
    # from the project root directory.
    main() # Call the new main function with argparse 