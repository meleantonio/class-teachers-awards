import openai
from typing import List
from ..config import OPENAI_API_KEY, GPT_MODEL

# Client initialization similar to message_generator.py
if OPENAI_API_KEY:
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
else:
    print("Warning: OPENAI_API_KEY is not set in alias_generator. OpenAI API calls will fail.")
    client = None

def generate_teacher_aliases(teacher_name: str, all_teacher_names: List[str]) -> List[str]:
    """
    Generates a list of common aliases for a given teacher name using an LLM.

    Args:
        teacher_name: The full name of the teacher for whom to generate aliases.
        all_teacher_names: A list of all known full teacher names in the faculty/context.

    Returns:
        A list of unique alias strings. Returns an empty list if no distinct aliases
        are generated or in case of an error.
    """
    if not client:
        print(f"Error: OpenAI client not initialized in alias_generator for {teacher_name}. Cannot generate aliases.")
        return []
    if not OPENAI_API_KEY:
        print(f"Error: OPENAI_API_KEY not configured in alias_generator for {teacher_name}. Cannot generate aliases.")
        return []

    # Prepare the list of other teacher names for context
    other_faculty_names = [name for name in all_teacher_names if name.lower() != teacher_name.lower()]
    other_faculty_names_str = ", ".join(other_faculty_names)
    if not other_faculty_names_str:
        other_faculty_names_str = "None available"


    prompt = f"""
Given the teacher's full name: '{teacher_name}'
And a list of other distinct full names of teachers in the same faculty: {other_faculty_names_str}

Task: Provide a comma-separated list of common alternative names, nicknames, or shortened versions that colleagues or students might use for '{teacher_name}'.
Consider the following types of aliases:
1.  Common shortenings of the first name (e.g., Thomas -> Tom, Elizabeth -> Liz, Beth).
2.  Initials if commonly used (e.g., T. Monk, if Thomas Monk is the full name).
3.  Common nicknames (e.g., Raffaele -> Raffi, William -> Bill, Billy).
4.  If the name appears to be of non-Western origin, suggest plausible common English/Westernized equivalents or shortenings that might be adopted in a Western academic setting.
5.  Avoid overly generic or ambiguous aliases that could easily be confused with other names if not strongly associated with the original name.

Constraints:
- The output must be a single line of text containing only the comma-separated aliases.
- Do NOT include the original full name '{teacher_name}' in the alias list.
- If no common, distinct, and plausible aliases are likely, or if generating an alias risks collision with another teacher's name (from the provided list or common knowledge), return an empty string or the word 'None'.
- Do not add any explanatory text, preamble, or markdown formatting. Just the comma-separated list.

Example for 'Thomas Monk' (with no other conflicting names): Tom, T. Monk, Tommy
Example for 'Raffaele Blasone': Raffi, Raf
Example for 'Jennifer Aniston': Jen, Jenny
Example for a name like 'Xiang Li' (assuming 'Li' is family name): Shawn (if a common Western adaptation)

Provide the list for '{teacher_name}':
"""

    # print(f"--- Alias Generation Prompt for {teacher_name} ---")
    # print(prompt)
    # print("--- End of Alias Prompt ---")

    try:
        response = client.chat.completions.create(
            model=GPT_MODEL, # Or a cheaper/faster model if appropriate for this task
            messages=[
                {"role": "system", "content": "You are an expert in names and cultural naming conventions. Your task is to provide a list of common aliases for a given name."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=60,  # Aliases are usually short
            temperature=0.2, # Lower temperature for more predictable, common aliases
            n=1,
            stop=None
        )
        llm_response_content = response.choices[0].message.content.strip()

        if not llm_response_content or llm_response_content.lower() == 'none':
            return []

        # Parse the comma-separated list
        aliases = [alias.strip() for alias in llm_response_content.split(',') if alias.strip()]
        
        # Filter out the original name (case-insensitive) and ensure uniqueness
        final_aliases = []
        seen_aliases = set()
        if aliases:
            for alias in aliases:
                # Ensure alias is not the original name (case-insensitive)
                # And alias is not another full teacher name from the context (case-insensitive)
                is_original_name = alias.lower() == teacher_name.lower()
                is_other_full_name = any(alias.lower() == other_name.lower() for other_name in other_faculty_names)
                
                if not is_original_name and not is_other_full_name and alias.lower() not in seen_aliases:
                    final_aliases.append(alias)
                    seen_aliases.add(alias.lower())
        
        return final_aliases

    except Exception as e:
        print(f"Error calling OpenAI API for alias generation for {teacher_name}: {e}")
        return []

if __name__ == '__main__':
    # This example assumes OPENAI_API_KEY is set in your environment or .env file
    import os
    from dotenv import load_dotenv
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
    else:
        project_root_dotenv = os.path.join(os.getcwd(), '.env')
        if os.path.exists(project_root_dotenv):
            load_dotenv(project_root_dotenv)
        else:
            print("Warning: .env file not found for alias_generator example. Ensure OPENAI_API_KEY is set.")

    if not OPENAI_API_KEY or not client:
        print("OpenAI API key not configured or client not initialized. Skipping alias_generator example.")
    else:
        print(f"Using OpenAI model: {GPT_MODEL} for alias generation.")
        
        faculty = ["Dr. Eleanor Vance", "Professor Thomas Monk", "Dr. Yi Chen", "Raffaele Blasone", "Dr. Benjamin Carter"]
        
        test_names = ["Professor Thomas Monk", "Raffaele Blasone", "Dr. Yi Chen", "Dr. Benjamin Carter", "Dr. Eleanor Vance"]
        
        for name_to_test in test_names:
            print(f"\n--- Generating aliases for: {name_to_test} ---")
            print(f"Context faculty: {faculty}")
            generated_aliases = generate_teacher_aliases(name_to_test, faculty)
            if generated_aliases:
                print(f"Suggested aliases: {generated_aliases}")
            else:
                print("No distinct aliases suggested or an error occurred.")
        
        # Test with a name not in faculty (should still work, context is for collision avoidance)
        name_not_in_faculty = "Dr. Isabella Rossi"
        print(f"\n--- Generating aliases for: {name_not_in_faculty} (not in provided faculty list) ---")
        generated_aliases_external = generate_teacher_aliases(name_not_in_faculty, faculty)
        if generated_aliases_external:
            print(f"Suggested aliases: {generated_aliases_external}")
        else:
            print("No distinct aliases suggested or an error occurred.") 