import openai
from typing import List, Dict
from ..config import OPENAI_API_KEY, GPT_MODEL

# Initialize OpenAI client
# It's good practice to initialize the client once, possibly here or in config.
# However, if the API key might not be set when the module is imported,
# it might be better to initialize it within the function or ensure config loads first.
if OPENAI_API_KEY:
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
else:
    # This will cause an error if the key isn't set and the function is called.
    # Consider raising a custom error or handling it more gracefully in the main script.
    print("Warning: OPENAI_API_KEY is not set. OpenAI API calls will fail.")
    client = None # Explicitly set to None

def generate_recommendation_message(teacher_name: str, 
                                  positive_feedback: List[str], 
                                  prof_opinions: List[str]) -> str:
    """
    Generates a recommendation message for a teacher using OpenAI GPT-4o.
    """
    if not client:
        return f"Error: OpenAI client not initialized. Check API key."
    if not OPENAI_API_KEY:
         return f"Error: OPENAI_API_KEY is not configured."

    # Extract first name
    parts = teacher_name.split(' ')
    first_name_part = parts[0]
    # Common titles, ensuring period is optional and comparison is case-insensitive
    titles = ["dr", "mr", "ms", "mrs", "prof", "professor"] 
    
    first_name = ""
    if first_name_part.lower().rstrip('.') in titles and len(parts) > 1:
        first_name = parts[1]
    else:
        first_name = first_name_part
    
    # Ensure first_name is not empty if parts was empty or contained only a title
    if not first_name and len(parts) > 0 : # Fallback if title logic left it empty but parts exist
        first_name = parts[-1] # Default to last part if complex name or only title provided.
    elif not first_name: # Fallback if teacher_name was empty or very unusual
        first_name = teacher_name # Use full name if first name extraction fails

    # Construct the prompt for GPT-4o
    prompt_parts = []
    prompt_parts.append(f"Task: Create a compelling and concise recommendation message (up to 4000 characters) for a teaching award for {teacher_name}.")
    prompt_parts.append("The message should highlight their strengths based on student feedback and professor opinions.")
    prompt_parts.append("Begin the recommendation text directly, without any preamble like 'Here is the recommendation message'.")
    prompt_parts.append("The overall tone should be positive, celebratory, and professional.")

    prompt_parts.append("\nKey Information:")
    prompt_parts.append(f"- Teacher's Name: {teacher_name}")

    # Initialize lists to store items included in the prompt for the "Sources Used" section
    feedback_to_include = [] 
    cleaned_opinions_for_prompt = []

    if positive_feedback:
        prompt_parts.append("\nStudent Positive Feedback (selected quotes):")
        feedback_to_include = positive_feedback[:5] # Select actual feedback for prompt
        for i, feedback in enumerate(feedback_to_include):
            prompt_parts.append(f"  - Student {i+1}: \"{feedback}\"")
    else:
        prompt_parts.append("\nStudent Positive Feedback: No specific quotes provided, but generally positive performance is implied.")

    if prof_opinions:
        prompt_parts.append("\nProfessor's Opinions/Comments (selected quotes):")
        opinions_to_include_raw = prof_opinions[:3] # Select raw opinions for prompt
        for i, opinion in enumerate(opinions_to_include_raw):
            cleaned_opinion = " ".join(opinion.splitlines()).strip()
            cleaned_opinions_for_prompt.append(cleaned_opinion) # Store cleaned version for "Sources Used"
            prompt_parts.append(f"  - Professor Comment {i+1}: \"{cleaned_opinion}\"")
    else:
        prompt_parts.append("\nProfessor's Opinions/Comments: No specific quotes provided.")

    prompt_parts.append("\nInstructions for the message content:")
    prompt_parts.append("- Synthesize the provided feedback and opinions into a coherent and impactful recommendation.")
    prompt_parts.append("- Focus on specific qualities or achievements if evident from the information.")
    prompt_parts.append("- Ensure the message flows well and is engaging.")
    prompt_parts.append("- The message itself should be the core content, avoid introductory or concluding phrases not part of the specified final output format.")
    prompt_parts.append("- Do NOT include a title like 'Recommendation Message:' in your generated text. The surrounding template will handle titles.")
    prompt_parts.append("- The generated text will be placed within a template, so just provide the message body.")

    full_prompt = "\n".join(prompt_parts)

    # print(f"\n--- OpenAI Prompt for {teacher_name} ---")
    # print(full_prompt)
    # print("--- End of Prompt ---\n")

    try:
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": "You are an assistant helping to draft teaching award recommendations. Your output should be only the recommendation message text itself, ready to be embedded in a larger document. Adhere strictly to character limits if specified elsewhere, though the primary goal is a strong recommendation based on provided inputs. Do not add any extra conversational text or markdown formatting like ## or titles within your direct output."},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=1000  # Adjust as needed, 4000 chars is ~1000 tokens. Prompt says "up to 4000 characters" for the *final message including template*.
                               # The LLM-generated part should be less.
        )
        llm_generated_message = response.choices[0].message.content.strip()
        
        # Construct the "Sources Used" section block
        source_details_parts = ["---", "**Sources Used for Generation:**"]
        
        source_details_parts.append("**Student Feedback:**")
        if feedback_to_include: # feedback_to_include was from earlier in the function
            for feedback_item in feedback_to_include:
                source_details_parts.append(f"- \"{feedback_item}\"")
        else:
            source_details_parts.append("- No specific student feedback provided.")
        
        source_details_parts.append("**Professor Opinions:**")
        # cleaned_opinions_for_prompt was from earlier in the function
        if cleaned_opinions_for_prompt:
            for opinion_item in cleaned_opinions_for_prompt:
                source_details_parts.append(f"- \"{opinion_item}\"")
        elif not prof_opinions: # Original prof_opinions list was empty
            source_details_parts.append("- No specific professor opinions provided.")
        else: # prof_opinions was not empty, but cleaned_opinions_for_prompt is (e.g. all opinions were empty strings)
            source_details_parts.append("- No professor opinions were included in the prompt.")

        sources_block_content = "\n".join(source_details_parts)

        # Final formatting
        final_output = (
            f"# {teacher_name}\n\n"
            f"# Recommendation message:\n\n"
            f"{llm_generated_message}\n\n"
            f"Fantastic job, {first_name}!\n\n" 
            f"{sources_block_content}"
        )
        
        # Check character limit (overall message)
        if len(final_output) > 4000:
            print(f"Warning: Generated message for {teacher_name} exceeds 4000 characters (length: {len(final_output)}). Consider shortening.")
            # Potentially, one could try to truncate or ask the LLM to shorten it here.
            # For now, just a warning.

        return final_output

    except Exception as e:
        print(f"Error calling OpenAI API for {teacher_name}: {e}")
        # Fallback message in case of API error
        # Include teacher name and standard formatting even for API errors
        error_message_text = f"[Automated generation failed due to an error: {e}. Please review available data for {teacher_name} manually.]"
        
        # Use the already extracted first_name from the top of the function
        return f"# {teacher_name}\n\n# Recommendation message:\n\n{error_message_text}\n\nFantastic job, {first_name}!"

# Example usage (for testing)
if __name__ == '__main__':
    # Ensure OPENAI_API_KEY is loaded from .env or environment
    # This test assumes the .env file is in the project root.
    import os
    from dotenv import load_dotenv
    # Construct path to .env from the location of this script
    # class_teacher_awards/llm/message_generator.py -> ../../.env
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
    else:
        # Fallback if running from project root: `python class_teacher_awards/llm/message_generator.py`
        project_root_dotenv = os.path.join(os.getcwd(), '.env')
        if os.path.exists(project_root_dotenv):
            load_dotenv(project_root_dotenv)
        else:
            print("Warning: .env file not found. Please ensure OPENAI_API_KEY is set.")

    if not OPENAI_API_KEY or not client:
        print("OpenAI API key not configured or client not initialized. Skipping example.")
    else:
        print(f"Using OpenAI model: {GPT_MODEL}")
        sample_teacher = "Dr. Ada Lovelace"
        sample_feedback = [
            "Incredibly clear explanations, made complex topics easy to understand.",
            "Always supportive and approachable during office hours.",
            "Her passion for the subject was truly infectious!",
            "Provided excellent examples that helped solidify my learning."
        ]
        sample_opinions = [
            "Dr. Lovelace is a standout instructor, consistently receiving praise from students.",
            "Her dedication to teaching is evident in her preparation and delivery."
        ]

        print(f"\nGenerating recommendation for: {sample_teacher}")
        recommendation = generate_recommendation_message(sample_teacher, sample_feedback, sample_opinions)
        print("\n--- Generated Recommendation ---")
        print(recommendation)
        print("--- End of Recommendation ---")

        # Test with missing data
        sample_teacher_no_opinions = "Mr. Charles Babbage"
        print(f"\nGenerating recommendation for: {sample_teacher_no_opinions} (no professor opinions)")
        recommendation_no_ops = generate_recommendation_message(sample_teacher_no_opinions, sample_feedback, [])
        print("\n--- Generated Recommendation (No Prof Opinions) ---")
        print(recommend_no_ops)
        print("--- End of Recommendation ---")
        
        sample_teacher_no_feedback = "Ms. Grace Hopper"
        print(f"\nGenerating recommendation for: {sample_teacher_no_feedback} (no student feedback)")
        recommendation_no_feed = generate_recommendation_message(sample_teacher_no_feedback, [], sample_opinions)
        print("\n--- Generated Recommendation (No Student Feedback) ---")
        print(recommend_no_feed)
        print("--- End of Recommendation ---") 