# Test file for message_generator.py
# TODO: Add actual test cases using pytest
# - Mock openai.OpenAI().chat.completions.create
# - Test generate_recommendation_message with various inputs:
#   - With student feedback and prof opinions
#   - With only student feedback
#   - With only prof opinions
#   - With no feedback or opinions
#   - Test prompt construction
#   - Test final message formatting
#   - Test character limit warning (if possible to mock message length easily)
#   - Test API error handling

# Example (conceptual - needs pytest fixtures and mocks):
# def test_example_message_generator():
#     assert True 

import pytest
from unittest.mock import patch, MagicMock, call
import openai
from class_teacher_awards.llm.message_generator import generate_recommendation_message, GPT_MODEL
# Note: We might need to be careful if OPENAI_API_KEY from config is used directly by the module on import.
# The message_generator module initializes 'client' based on OPENAI_API_KEY at import time.
# For tests, we'll primarily patch 'message_generator.client'.

@pytest.fixture
def mock_openai_client():
    """Fixture to mock the OpenAI client in message_generator module."""
    with patch('class_teacher_awards.llm.message_generator.client') as mock_client_instance:
        mock_chat_completions = MagicMock()
        mock_create_method = MagicMock()
        mock_response = MagicMock()
        mock_message = MagicMock()
        # Set a default LLM output for the fixture
        mock_message.content = "Default generated recommendation text."
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_create_method.return_value = mock_response
        mock_chat_completions.create = mock_create_method
        mock_client_instance.chat.completions = mock_chat_completions
        yield mock_client_instance

def test_generate_recommendation_success(mock_openai_client):
    teacher_name = "Dr. Test"
    positive_feedback = ["Great teacher!", "Very helpful."]
    prof_opinions = ["A true asset.", "Highly recommended for award."]
    
    expected_llm_output = "Generated recommendation text."
    # Update the mock for this specific test if needed, or rely on fixture default
    mock_openai_client.chat.completions.create.return_value.choices[0].message.content = expected_llm_output
    
    result = generate_recommendation_message(teacher_name, positive_feedback, prof_opinions)

    mock_openai_client.chat.completions.create.assert_called_once()
    call_args = mock_openai_client.chat.completions.create.call_args
    assert call_args is not None
    prompt_messages = call_args.kwargs['messages']
    system_prompt = prompt_messages[0]['content']
    user_prompt = prompt_messages[1]['content']
    assert "You are an assistant helping to draft teaching award recommendations." in system_prompt
    assert f"Task: Create a compelling and concise recommendation message (up to 4000 characters) for a teaching award for {teacher_name}." in user_prompt
    assert "- Student 1: \"Great teacher!\"" in user_prompt
    assert "- Student 2: \"Very helpful.\"" in user_prompt
    assert "- Professor Comment 1: \"A true asset.\"" in user_prompt
    assert "- Professor Comment 2: \"Highly recommended for award.\"" in user_prompt

    sources_block_content = (
        "---\n"
        "**Sources Used for Generation:**\n"
        "**Student Feedback:**\n"
        "- \"Great teacher!\"\n"
        "- \"Very helpful.\"\n"  # End student feedback section
        "**Professor Opinions:**\n"   # Start prof opinions (single newline after previous)
        "- \"A true asset.\"\n"
        "- \"Highly recommended for award.\""
    )
    expected_output = (
        f"# {teacher_name}\n\n"
        f"# Recommendation message:\n\n"
        f"{expected_llm_output.strip()}\n\n"
        f"{sources_block_content}\n\n"
        f"Fantastic job, {teacher_name}!"
    )
    assert result == expected_output

def test_prof_opinion_cleaning_in_prompt(mock_openai_client):
    # This test primarily checks prompt content, not final output structure for sources.
    # However, if we want to be thorough, the final output check could be added too.
    teacher_name = "Prof. Clean"
    positive_feedback = []
    prof_opinions = ["Opinion with\nnewlines.", "Another one\r\nwith mixed newlines."]
    expected_llm_output = "Cleaned opinion output."
    mock_openai_client.chat.completions.create.return_value.choices[0].message.content = expected_llm_output

    result = generate_recommendation_message(teacher_name, positive_feedback, prof_opinions)
    
    mock_openai_client.chat.completions.create.assert_called_once()
    call_args = mock_openai_client.chat.completions.create.call_args
    user_prompt = call_args.kwargs['messages'][1]['content']
    
    assert "- Professor Comment 1: \"Opinion with newlines.\"" in user_prompt
    assert "- Professor Comment 2: \"Another one with mixed newlines.\"" in user_prompt
    assert "\n" not in user_prompt.split("Professor Comment 1: \"")[1].split('\"')[0]
    assert "\n" not in user_prompt.split("Professor Comment 2: \"")[1].split('\"')[0]

    sources_block_content = (
        "---\n"
        "**Sources Used for Generation:**\n"
        "**Student Feedback:**\n"
        "- No specific student feedback provided.\n"
        "**Professor Opinions:**\n" # Single newline after previous
        "- \"Opinion with newlines.\"\n"
        "- \"Another one with mixed newlines.\""
    )
    expected_output = (
        f"# {teacher_name}\n\n"
        f"# Recommendation message:\n\n"
        f"{expected_llm_output.strip()}\n\n"
        f"{sources_block_content}\n\n"
        f"Fantastic job, {teacher_name}!"
    )
    assert result == expected_output

def test_generate_recommendation_no_student_feedback(mock_openai_client):
    teacher_name = "Dr. NoStudentFeedback"
    positive_feedback = []
    prof_opinions = ["Still a great colleague."]
    expected_llm_output = "Recommendation based on prof opinion."
    mock_openai_client.chat.completions.create.return_value.choices[0].message.content = expected_llm_output

    result = generate_recommendation_message(teacher_name, positive_feedback, prof_opinions)
    call_args = mock_openai_client.chat.completions.create.call_args
    user_prompt = call_args.kwargs['messages'][1]['content']

    assert "Student Positive Feedback: No specific quotes provided, but generally positive performance is implied." in user_prompt
    assert "- Professor Comment 1: \"Still a great colleague.\"" in user_prompt
    
    sources_block_content = (
        "---\n"
        "**Sources Used for Generation:**\n"
        "**Student Feedback:**\n"
        "- No specific student feedback provided.\n"
        "**Professor Opinions:**\n" # Single newline after previous
        "- \"Still a great colleague.\""
    )
    expected_output = (
        f"# {teacher_name}\n\n"
        f"# Recommendation message:\n\n"
        f"{expected_llm_output.strip()}\n\n"
        f"{sources_block_content}\n\n"
        f"Fantastic job, {teacher_name}!"
    )
    assert result == expected_output

def test_generate_recommendation_no_prof_opinions(mock_openai_client):
    teacher_name = "Ms. NoProfOpinion"
    positive_feedback = ["Students love her."]
    prof_opinions = []
    expected_llm_output = "Recommendation based on student feedback."
    mock_openai_client.chat.completions.create.return_value.choices[0].message.content = expected_llm_output

    result = generate_recommendation_message(teacher_name, positive_feedback, prof_opinions)
    call_args = mock_openai_client.chat.completions.create.call_args
    user_prompt = call_args.kwargs['messages'][1]['content']

    assert "- Student 1: \"Students love her.\"" in user_prompt
    assert "Professor's Opinions/Comments: No specific quotes provided." in user_prompt

    sources_block_content = (
        "---\n"
        "**Sources Used for Generation:**\n"
        "**Student Feedback:**\n"
        "- \"Students love her.\"\n"
        "**Professor Opinions:**\n" # Single newline after previous
        "- No specific professor opinions provided."
    )
    expected_output = (
        f"# {teacher_name}\n\n"
        f"# Recommendation message:\n\n"
        f"{expected_llm_output.strip()}\n\n"
        f"{sources_block_content}\n\n"
        f"Fantastic job, {teacher_name}!"
    )
    assert result == expected_output

def test_generate_recommendation_no_feedback_or_opinions(mock_openai_client):
    teacher_name = "Mr. NoData"
    positive_feedback = []
    prof_opinions = []
    expected_llm_output = "Generic positive recommendation."
    mock_openai_client.chat.completions.create.return_value.choices[0].message.content = expected_llm_output
    
    result = generate_recommendation_message(teacher_name, positive_feedback, prof_opinions)
    call_args = mock_openai_client.chat.completions.create.call_args
    user_prompt = call_args.kwargs['messages'][1]['content']

    assert "Student Positive Feedback: No specific quotes provided, but generally positive performance is implied." in user_prompt
    assert "Professor's Opinions/Comments: No specific quotes provided." in user_prompt

    sources_block_content = (
        "---\n"
        "**Sources Used for Generation:**\n"
        "**Student Feedback:**\n"
        "- No specific student feedback provided.\n"
        "**Professor Opinions:**\n" # Single newline after previous
        "- No specific professor opinions provided."
    )
    expected_output = (
        f"# {teacher_name}\n\n"
        f"# Recommendation message:\n\n"
        f"{expected_llm_output.strip()}\n\n"
        f"{sources_block_content}\n\n"
        f"Fantastic job, {teacher_name}!"
    )
    assert result == expected_output

def test_generate_recommendation_api_error(mock_openai_client, capsys):
    teacher_name = "Dr. APIError"
    test_api_error_message = "Test API connection error"
    mock_openai_client.chat.completions.create.side_effect = openai.APIError(message=test_api_error_message, request=None, body=None)
    result = generate_recommendation_message(teacher_name, ["Good."], ["Also good."])
    expected_error_text_in_msg = f"[Automated generation failed due to an error: {test_api_error_message}. Please review available data for {teacher_name} manually.]"
    # Reverted to simple f-string as this error path does not include sources block formatting
    expected_output = f"# {teacher_name}\n\n# Recommendation message:\n\n{expected_error_text_in_msg}\n\nFantastic job, {teacher_name}!"
    assert result == expected_output
    captured = capsys.readouterr()
    assert f"Error calling OpenAI API for {teacher_name}: {test_api_error_message}" in captured.out

# Need to import openai for the APIError
# import openai # Removed from here

# Test for client not initialized (OPENAI_API_KEY is None)
def test_generate_recommendation_client_not_initialized_no_key(): # Removed arguments
    teacher_name = "Dr. NoKey"
    positive_feedback = []
    prof_opinions = []

    # The generate_recommendation_message function checks client first.
    # If client is None due to no API key at import or patched, it should return the error.
    
    # Using patch as context managers
    with patch('class_teacher_awards.llm.message_generator.OPENAI_API_KEY', None):
        with patch('class_teacher_awards.llm.message_generator.client', None):
            result = generate_recommendation_message(teacher_name, positive_feedback, prof_opinions)
    
    expected_error_text = "Error: OpenAI client not initialized. Check API key."
    expected_output = expected_error_text 
    assert result == expected_output


def test_generate_recommendation_character_limit_warning(mock_openai_client, capsys):
    teacher_name = "Dr. LongBio"
    positive_feedback = ["Feedback"]
    prof_opinions = ["Opinion"]
    long_llm_output = "a" * 3900 # Adjusted to make space for sources section potentially
    mock_openai_client.chat.completions.create.return_value.choices[0].message.content = long_llm_output
    
    result = generate_recommendation_message(teacher_name, positive_feedback, prof_opinions)
    
    sources_block_content = (
        "---\n"
        "**Sources Used for Generation:**\n"
        "**Student Feedback:**\n"
        "- \"Feedback\"\n"
        "**Professor Opinions:**\n" # Single newline after previous
        "- \"Opinion\""
    )
    # Main point is to check capsys for the warning if length > 4000.

    # expected_output_structure_start for startswith should end at the end of sources_block_content
    expected_output_structure_start = (
        f"# {teacher_name}\n\n"
        f"# Recommendation message:\n\n"
        f"{long_llm_output.strip()}\n\n"
        f"{sources_block_content}" # No trailing \n\n for startswith check of this block
    )
    # This full check is more comprehensive and preferred.
    expected_full_content_for_warning_check = (
        f"# {teacher_name}\n\n"
        f"# Recommendation message:\n\n"
        f"{long_llm_output.strip()}\n\n"
        f"{sources_block_content}\n\n"
        f"Fantastic job, {teacher_name}!"
    )
    # assert result.startswith(expected_output_structure_start) # This can be an additional check if desired
    assert result == expected_full_content_for_warning_check # Primary assertion for content
    
    captured = capsys.readouterr()
    warning_message = f"Warning: Generated message for {teacher_name} exceeds 4000 characters"
    # This assertion might need adjustment if the total length changes significantly
    # due to the sources section. The core functionality is the warning print.
    if len(result) > 4000:
        assert warning_message in captured.out
        assert f"(length: {len(result)})" in captured.out
    else:
        # If by chance it's not over 4000 with sources, the warning shouldn't appear
        assert warning_message not in captured.out 


# Test for limits on feedback and opinions
def test_feedback_and_opinion_limits_in_prompt(mock_openai_client):
    # This test primarily checks prompt content, final output format also updated.
    teacher_name = "Dr. Limits"
    student_feedback = [f"Student feedback {i}" for i in range(10)]
    prof_opinions = [f"Prof opinion {i}\nwith newlines" for i in range(5)]
    expected_llm_output = "Limited feedback output."
    mock_openai_client.chat.completions.create.return_value.choices[0].message.content = expected_llm_output

    result = generate_recommendation_message(teacher_name, student_feedback, prof_opinions)
    call_args = mock_openai_client.chat.completions.create.call_args
    user_prompt = call_args.kwargs['messages'][1]['content']

    # Check that only 5 student feedbacks are included
    for i in range(5):
        assert f"- Student {i+1}: \"{student_feedback[i]}\"" in user_prompt
    assert f"- Student 6: \"{student_feedback[5]}\"" not in user_prompt
    
    # Check that only 3 professor opinions are included and cleaned
    for i in range(3):
        cleaned_opinion_in_prompt = f"Prof opinion {i} with newlines" # Original has \n
        assert f"- Professor Comment {i+1}: \"{cleaned_opinion_in_prompt}\"" in user_prompt
    assert f"- Professor Comment 4: \"Prof opinion 3 with newlines\"" not in user_prompt 

    # This test should use the builder logic correctly as it was nearly right before edits confused it.
    sources_builder_parts = [
        "---",
        "**Sources Used for Generation:**",
        "**Student Feedback:**"
    ]
    for i in range(5): # Only first 5 student feedbacks are used
        sources_builder_parts.append(f"- \"{student_feedback[i]}\"")
    sources_builder_parts.append("**Professor Opinions:**") # This correctly adds it for single \n join
    for i in range(3): # Only first 3 (cleaned) prof opinions are used
        sources_builder_parts.append(f"- \"Prof opinion {i} with newlines\"") 
    sources_block_content = "\n".join(sources_builder_parts)

    expected_output = (
        f"# {teacher_name}\n\n"
        f"# Recommendation message:\n\n"
        f"{expected_llm_output.strip()}\n\n"
        f"{sources_block_content}\n\n"
        f"Fantastic job, {teacher_name}!"
    )
    assert result == expected_output 