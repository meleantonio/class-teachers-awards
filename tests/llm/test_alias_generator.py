import pytest
from unittest.mock import patch, MagicMock
from class_teacher_awards.llm.alias_generator import generate_teacher_aliases
import openai # For openai.APIError if needed for error testing

# Path to the client in alias_generator for patching
ALIAS_GENERATOR_CLIENT_PATH = 'class_teacher_awards.llm.alias_generator.client'
ALIAS_GENERATOR_API_KEY_PATH = 'class_teacher_awards.llm.alias_generator.OPENAI_API_KEY'

@pytest.fixture
def mock_openai_client_for_aliases(monkeypatch):
    """Fixture to mock the OpenAI client in alias_generator module."""
    mock_client_instance = MagicMock()
    mock_chat_completions = MagicMock()
    mock_create_method = MagicMock()
    
    # Default behavior: return an empty string for aliases
    mock_response = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "" 
    mock_response.choices = [MagicMock(message=mock_message)]
    mock_create_method.return_value = mock_response
    
    mock_chat_completions.create = mock_create_method
    mock_client_instance.chat.completions = mock_chat_completions
    
    monkeypatch.setattr(ALIAS_GENERATOR_CLIENT_PATH, mock_client_instance)
    monkeypatch.setattr(ALIAS_GENERATOR_API_KEY_PATH, "test_api_key") # Ensure API key is seen as set
    return mock_client_instance

def test_generate_aliases_success_simple(mock_openai_client_for_aliases):
    teacher_name = "Professor Thomas Anderson"
    all_teachers = ["Professor Thomas Anderson", "Dr. Jane Smith"]
    expected_llm_response = "Tom, Tommy, T. Anderson"
    
    mock_openai_client_for_aliases.chat.completions.create.return_value.choices[0].message.content = expected_llm_response
    
    aliases = generate_teacher_aliases(teacher_name, all_teachers)
    
    mock_openai_client_for_aliases.chat.completions.create.assert_called_once()
    call_args = mock_openai_client_for_aliases.chat.completions.create.call_args
    prompt_content = call_args.kwargs['messages'][1]['content']
    assert f"Given the teacher's full name: '{teacher_name}'" in prompt_content
    assert "Dr. Jane Smith" in prompt_content # Check context is passed
    
    assert sorted(aliases) == sorted(["Tom", "Tommy", "T. Anderson"])

def test_generate_aliases_llm_returns_none_or_empty(mock_openai_client_for_aliases):
    teacher_name = "Professor Unique Name"
    all_teachers = ["Professor Unique Name"]
    
    # Test with LLM returning "None"
    mock_openai_client_for_aliases.chat.completions.create.return_value.choices[0].message.content = "None"
    aliases_none = generate_teacher_aliases(teacher_name, all_teachers)
    assert aliases_none == []

    # Test with LLM returning empty string
    mock_openai_client_for_aliases.chat.completions.create.return_value.choices[0].message.content = ""
    aliases_empty = generate_teacher_aliases(teacher_name, all_teachers)
    assert aliases_empty == []

def test_generate_aliases_filters_original_name_and_duplicates(mock_openai_client_for_aliases):
    teacher_name = "Dr. Eleanor Vance"
    all_teachers = ["Dr. Eleanor Vance", "Dr. Tom Smith"] # Tom Smith is another teacher
    # LLM might suggest "Eleanor", "Dr. Vance", "Ellie", "Eleanor Vance" (original), "Tom"
    llm_response = "Eleanor, Dr. Vance, Ellie, Dr. Eleanor Vance, Ellie, Tom"
    mock_openai_client_for_aliases.chat.completions.create.return_value.choices[0].message.content = llm_response
    
    aliases = generate_teacher_aliases(teacher_name, all_teachers)
    
    # Expected: "Eleanor", "Dr. Vance", "Ellie"
    # "Dr. Eleanor Vance" (original) should be filtered.
    # "Tom" should be filtered as it might be part of "Dr. Tom Smith" or a generic name the prompt tries to avoid.
    # The filtering logic also checks against `other_faculty_names`, so if "Tom" was returned and "Dr. Tom Smith" is in context, "Tom" would be filtered if it fully matches "Tom".
    # Let's refine this: the filtering checks if an alias *is* another full name. "Tom" is not "Dr. Tom Smith".
    # The LLM is prompted to avoid collisions. Assuming LLM is good, we test parsing and filtering of original name.
    # If LLM returns "Tom Smith" as an alias, it should be filtered.
    
    # For this test, assume LLM provided "Tom" and we need to ensure our direct name collision filter works.
    # Let's test the case where an alias IS another teacher's name.
    llm_response_collision = "Ellie, Dr. Tom Smith, Ellie"
    mock_openai_client_for_aliases.chat.completions.create.return_value.choices[0].message.content = llm_response_collision
    aliases_collision = generate_teacher_aliases(teacher_name, all_teachers)
    assert sorted(aliases_collision) == sorted(["Ellie"]) # "Dr. Tom Smith" is filtered


def test_generate_aliases_filters_original_name_case_insensitive(mock_openai_client_for_aliases):
    teacher_name = "Dr. Yi Chen"
    all_teachers = ["Dr. Yi Chen"]
    llm_response = "Yi, dr. yi chen, Y. Chen" # LLM returns original name in different case
    mock_openai_client_for_aliases.chat.completions.create.return_value.choices[0].message.content = llm_response
    
    aliases = generate_teacher_aliases(teacher_name, all_teachers)
    assert sorted(aliases) == sorted(["Yi", "Y. Chen"])


def test_generate_aliases_no_context_faculty(mock_openai_client_for_aliases):
    teacher_name = "Solo Professor"
    all_teachers = ["Solo Professor"] # Only one teacher
    expected_llm_response = "Solo, Prof. S"
    mock_openai_client_for_aliases.chat.completions.create.return_value.choices[0].message.content = expected_llm_response
    
    aliases = generate_teacher_aliases(teacher_name, all_teachers)
    
    call_args = mock_openai_client_for_aliases.chat.completions.create.call_args
    prompt_content = call_args.kwargs['messages'][1]['content']
    assert "other distinct full names of teachers in the same faculty: None available" in prompt_content
    assert sorted(aliases) == sorted(["Solo", "Prof. S"])

def test_generate_aliases_api_error(mock_openai_client_for_aliases, capsys):
    teacher_name = "Professor ErrorProne"
    all_teachers = [teacher_name]
    
    mock_openai_client_for_aliases.chat.completions.create.side_effect = openai.APIError(message="Test API error", request=None, body=None)
    
    aliases = generate_teacher_aliases(teacher_name, all_teachers)
    assert aliases == []
    captured = capsys.readouterr()
    assert f"Error calling OpenAI API for alias generation for {teacher_name}: Test API error" in captured.out

def test_generate_aliases_client_not_initialized(monkeypatch, capsys):
    # Test when client is None from the start
    monkeypatch.setattr(ALIAS_GENERATOR_CLIENT_PATH, None)
    teacher_name = "Professor NoClient"
    all_teachers = [teacher_name]
    
    aliases = generate_teacher_aliases(teacher_name, all_teachers)
    assert aliases == []
    captured = capsys.readouterr()
    assert f"Error: OpenAI client not initialized in alias_generator for {teacher_name}" in captured.out

def test_generate_aliases_api_key_not_set(mock_openai_client_for_aliases, monkeypatch, capsys):
    # Client is initially mocked by the fixture, which also sets a test API key.
    # We then set the API_KEY for the module to None for this test.
    monkeypatch.setattr(ALIAS_GENERATOR_API_KEY_PATH, None)
    teacher_name = "Professor NoApiKey"
    all_teachers = [teacher_name]
    
    aliases = generate_teacher_aliases(teacher_name, all_teachers)
    assert aliases == []
    captured = capsys.readouterr()
    # Since client is NOT None (due to fixture), but API_KEY IS None,
    # the function should hit the 'OPENAI_API_KEY not configured' check.
    assert f"Error: OPENAI_API_KEY not configured in alias_generator for {teacher_name}" in captured.out

@patch(ALIAS_GENERATOR_API_KEY_PATH, "fake_key") # Applied second
@patch(ALIAS_GENERATOR_CLIENT_PATH)               # Applied first
def test_generate_aliases_api_key_becomes_none_after_init(mock_client, monkeypatch, capsys):
    # mock_client is the MagicMock from @patch(ALIAS_GENERATOR_CLIENT_PATH)
    # The patch for API_KEY_PATH just sets the module global, its mock object isn't needed here.
    
    teacher_name = "Professor KeyGone"
    all_teachers = [teacher_name]
    
    assert mock_client is not None 

    monkeypatch.setattr(ALIAS_GENERATOR_API_KEY_PATH, None) 

    aliases = generate_teacher_aliases(teacher_name, all_teachers)
    assert aliases == []
    captured = capsys.readouterr()
    assert f"Error: OPENAI_API_KEY not configured in alias_generator for {teacher_name}" in captured.out 