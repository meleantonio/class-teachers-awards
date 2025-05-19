# Test file for eml_parser.py
# TODO: Add actual test cases using pytest
# - Mock open for EML files
# - Test parse_eml_content with sample EML data (plain text, HTML, multipart, different charsets, file not found)
# - Test extract_professors_opinions_for_teacher (name found, not found, multiple mentions, context window)
# - Test get_all_professors_opinions

# Example (conceptual - needs pytest fixtures and mocks):
# def test_example_eml_parser():
#     assert True 

import pytest
from unittest.mock import patch, mock_open, call, MagicMock
from email.message import Message

from class_teacher_awards.data_extraction.eml_parser import (
    parse_eml_content,
    extract_professors_opinions_for_teacher,
    get_all_professors_opinions
)

# Path for mocking generate_teacher_aliases within eml_parser module
ALIAS_GENERATOR_PATH = 'class_teacher_awards.data_extraction.eml_parser.generate_teacher_aliases'

# --- Tests for parse_eml_content --- 

@patch("builtins.open", new_callable=mock_open)
@patch("class_teacher_awards.data_extraction.eml_parser.BytesParser")
def test_parse_eml_content_plain_text(mock_bytes_parser, mock_file_open):
    mock_msg = Message()
    mock_msg.set_payload(b"Hello Professor X\nThis is a plain text email.", charset="utf-8")
    mock_msg.is_multipart = MagicMock(return_value=False)
    mock_msg.get_content_charset = MagicMock(return_value="utf-8")
    mock_msg.get_content_type = MagicMock(return_value='text/plain')
    mock_bytes_parser.return_value.parse.return_value = mock_msg

    content = parse_eml_content("dummy.eml")
    mock_file_open.assert_called_once_with("dummy.eml", "rb")
    assert "Hello Professor X" in content
    assert "This is a plain text email." in content

@patch("builtins.open", new_callable=mock_open)
@patch("class_teacher_awards.data_extraction.eml_parser.BytesParser")
def test_parse_eml_content_html_only(mock_bytes_parser, mock_file_open):
    mock_msg = Message()
    mock_msg.set_payload(b"<p>Dear Dr. Y,</p><p>An HTML&nbsp;email.</p>", charset="iso-8859-1")
    mock_msg.is_multipart = MagicMock(return_value=False)
    mock_msg.get_content_charset = MagicMock(return_value="iso-8859-1")
    mock_msg.get_content_type = MagicMock(return_value='text/html')
    mock_bytes_parser.return_value.parse.return_value = mock_msg

    content = parse_eml_content("dummy.eml")
    assert "Dear Dr. Y," in content
    assert "An HTML email." in content # &nbsp; should be replaced
    assert "<p>" not in content # HTML tags should be stripped

@patch("builtins.open", new_callable=mock_open)
@patch("class_teacher_awards.data_extraction.eml_parser.BytesParser")
def test_parse_eml_content_multipart_plain_and_html(mock_bytes_parser, mock_file_open):
    plain_part = Message()
    plain_part.set_payload("Plain text part for Prof Z.", charset="utf-8")
    plain_part.get_content_type = MagicMock(return_value='text/plain')
    plain_part.get_content_charset = MagicMock(return_value="utf-8")
    plain_part.get = MagicMock(return_value=None)
    plain_part['Content-Transfer-Encoding'] = '8bit'
    plain_part.get_payload = MagicMock(return_value="Plain text part for Prof Z.")

    html_part = Message()
    html_part.set_payload("<h1>HTML part</h1><p>Also for Prof Z.</p>", charset="utf-8")
    html_part.get_content_type = MagicMock(return_value='text/html')
    html_part.get_content_charset = MagicMock(return_value="utf-8")
    html_part.get = MagicMock(return_value=None)
    html_part['Content-Transfer-Encoding'] = '8bit'
    html_part.get_payload = MagicMock(return_value="<h1>HTML part</h1><p>Also for Prof Z.</p>")
    
    mock_outer_msg = Message()
    mock_outer_msg.is_multipart = MagicMock(return_value=True)
    mock_outer_msg.walk = MagicMock(return_value=[plain_part, html_part])
    mock_bytes_parser.return_value.parse.return_value = mock_outer_msg

    content = parse_eml_content("dummy_multipart.eml")
    assert "Plain text part for Prof Z." in content
    assert "HTML partAlso for Prof Z." in content # Corrected: no space between part and Also

@patch("builtins.open", new_callable=mock_open)
@patch("class_teacher_awards.data_extraction.eml_parser.BytesParser")
def test_parse_eml_content_multipart_with_attachment(mock_bytes_parser, mock_file_open):
    plain_part = Message()
    plain_part.set_payload("Email about Dr. Foo.", charset="utf-8")
    plain_part.get_content_type = MagicMock(return_value='text/plain')
    plain_part.get_content_charset = MagicMock(return_value="utf-8")
    plain_part.get = MagicMock(return_value=None)
    plain_part['Content-Transfer-Encoding'] = '8bit'
    plain_part.get_payload = MagicMock(return_value="Email about Dr. Foo.")

    attachment_part = Message()
    attachment_part.get_content_type = MagicMock(return_value='application/pdf')
    attachment_part.get = MagicMock(return_value='attachment; filename="doc.pdf"') 

    mock_outer_msg = Message()
    mock_outer_msg.is_multipart = MagicMock(return_value=True)
    mock_outer_msg.walk = MagicMock(return_value=[plain_part, attachment_part])
    mock_bytes_parser.return_value.parse.return_value = mock_outer_msg

    content = parse_eml_content("dummy_with_attach.eml")
    assert "Email about Dr. Foo." in content

@patch("builtins.open", side_effect=FileNotFoundError("EML not found"))
def test_parse_eml_content_file_not_found(mock_file_open, capsys):
    content = parse_eml_content("non_existent.eml")
    assert content == ""
    captured = capsys.readouterr()
    assert "Error parsing EML file non_existent.eml: EML not found" in captured.out

@patch("builtins.open", new_callable=mock_open)
@patch("class_teacher_awards.data_extraction.eml_parser.BytesParser")
def test_parse_eml_content_decoding_error(mock_bytes_parser, mock_file_open, capsys):
    mock_msg = Message()
    invalid_utf8_payload = b"Hello \xff Prof Q"
    mock_msg.set_payload(invalid_utf8_payload, charset="utf-8") 
    mock_msg.is_multipart = MagicMock(return_value=False)
    mock_msg.get_content_charset = MagicMock(return_value="utf-8")
    mock_msg.get_content_type = MagicMock(return_value="text/plain")
    mock_bytes_parser.return_value.parse.return_value = mock_msg

    content = parse_eml_content("dummy_bad_encoding.eml")
    assert "Hello ÿ Prof Q" in content 

# --- Tests for extract_professors_opinions_for_teacher --- 

def test_extract_professors_opinions_for_teacher_found():
    eml_texts = [
        "Dr. Alpha is great. Highly recommend her for the award.",
        "Regarding Dr. Beta, he has shown significant improvement. Dr. Alpha also helped.",
        "No comment on Dr. Gamma here."
    ]
    opinions = extract_professors_opinions_for_teacher("Dr. Alpha", eml_texts)
    assert len(opinions) == 2
    assert any("Dr. Alpha is great" in op for op in opinions)
    assert any("Dr. Beta, he has shown significant improvement. Dr. Alpha also helped." in op for op in opinions)

def test_extract_professors_opinions_for_teacher_not_found():
    eml_texts = [
        "Dr. Alpha is great.",
        "Regarding Dr. Beta, he has shown improvement."
    ]
    opinions = extract_professors_opinions_for_teacher("Dr. Gamma", eml_texts)
    assert len(opinions) == 0

def test_extract_professors_opinions_for_teacher_case_insensitive():
    eml_texts = ["Recommendation for dr. alpha. She is fantastic."]
    opinions = extract_professors_opinions_for_teacher("Dr. Alpha", eml_texts)
    assert len(opinions) == 1
    assert "dr. alpha. She is fantastic" in opinions[0]

def test_extract_professors_opinions_for_teacher_context_window():
    eml_texts = [
        "Line 1: Previous unrelated sentence.\nLine 2: Professor Delta is truly outstanding.\nLine 3: Her dedication is clear.\nLine 4: Another sentence after."
    ]
    expected_snippet = "Line 1: Previous unrelated sentence.\nLine 2: Professor Delta is truly outstanding.\nLine 3: Her dedication is clear."
    opinions = extract_professors_opinions_for_teacher("Professor Delta", eml_texts)
    assert len(opinions) == 1
    assert opinions[0] == expected_snippet.strip()

def test_extract_professors_opinions_for_teacher_deduplication():
    eml_texts = [
        "Dr. Epsilon is good. We like Dr. Epsilon.", 
        "Another email. Dr. Epsilon is good."
    ]
    opinions = extract_professors_opinions_for_teacher("Dr. Epsilon", eml_texts)
    assert len(opinions) == 2 
    assert any("Dr. Epsilon is good. We like Dr. Epsilon." in op for op in opinions)
    assert any("Another email. Dr. Epsilon is good." in op for op in opinions)

# --- Tests for get_all_professors_opinions --- 

@patch('class_teacher_awards.data_extraction.eml_parser.parse_eml_content')
@patch('class_teacher_awards.data_extraction.eml_parser.EML_FILE_PATHS', ['file1.eml', 'file2.eml'])
def test_get_all_professors_opinions(mock_parse_eml):
    def parse_side_effect(file_path):
        if file_path == 'file1.eml':
            return "Content from file1 mentioning Dr. Phi and Prof. Chi."
        elif file_path == 'file2.eml':
            return "More about Dr. Phi. Also Prof. Sigma."
        return ""
    mock_parse_eml.side_effect = parse_side_effect
    
    teachers = ["Dr. Phi", "Prof. Chi", "Prof. Zeta"]
    result = get_all_professors_opinions(teachers)

    assert len(result["Dr. Phi"]) == 2 
    assert any("Dr. Phi" in op for op in result["Dr. Phi"]) 

    assert len(result["Prof. Chi"]) == 1
    assert "Prof. Chi" in result["Prof. Chi"][0]

    assert len(result["Prof. Zeta"]) == 0 

    assert mock_parse_eml.call_count == 2
    mock_parse_eml.assert_has_calls([call('file1.eml'), call('file2.eml')], any_order=True)

@patch('class_teacher_awards.data_extraction.eml_parser.parse_eml_content', return_value="")
@patch('class_teacher_awards.data_extraction.eml_parser.EML_FILE_PATHS', ['empty.eml'])
def test_get_all_professors_opinions_empty_eml_content(mock_parse_eml):
    teachers = ["Dr. Omega"]
    result = get_all_professors_opinions(teachers)
    assert len(result["Dr. Omega"]) == 0
    mock_parse_eml.assert_called_once_with('empty.eml') 

@pytest.fixture
def mock_file_open(monkeypatch):
    m = mock_open()
    monkeypatch.setattr("builtins.open", m)
    return m

# Test data for EML content
SAMPLE_EML_TEXT_PLAIN_CONTENT = """
From: sender@example.com
To: recipient@example.com
Subject: Feedback on Professor Alpha

Professor Alpha is an excellent educator. She is very knowledgeable.
We also think Professor Beta is doing a great job.
Regarding Professor Alpha, her dedication is commendable.
"""

SAMPLE_EML_HTML_CONTENT = """
From: sender@example.com
To: recipient@example.com
Subject: HTML Feedback
Content-Type: text/html

<p>Dear Committee,</p><p>I would like to nominate <b>Professor Gamma</b>. He is great.</p>
<p>Also, <i>Professor Delta</i> is quite good.</p>
"""

@patch("class_teacher_awards.data_extraction.eml_parser.BytesParser")
def test_parse_eml_content_text_plain(mock_bytes_parser, mock_file_open):
    mock_msg = Message()
    # Simulate a simple text/plain message
    mock_msg.set_payload(SAMPLE_EML_TEXT_PLAIN_CONTENT.split("\n\n", 1)[1].encode('utf-8'), charset='utf-8')
    mock_msg.is_multipart = MagicMock(return_value=False)
    mock_msg.get_content_type = MagicMock(return_value='text/plain')
    mock_bytes_parser.return_value.parse.return_value = mock_msg

    content = parse_eml_content("dummy.eml")
    assert "Professor Alpha is an excellent educator." in content
    assert "Professor Beta is doing a great job." in content
    assert "her dedication is commendable." in content

@patch("class_teacher_awards.data_extraction.eml_parser.BytesParser")
def test_parse_eml_content_html_only(mock_bytes_parser, mock_file_open):
    mock_msg = Message()
    mock_msg.set_payload(SAMPLE_EML_HTML_CONTENT.split("\n\n", 1)[1].encode('iso-8859-1'), charset="iso-8859-1")
    mock_msg.is_multipart = MagicMock(return_value=False)
    mock_msg.get_content_charset = MagicMock(return_value="iso-8859-1")
    mock_msg.get_content_type = MagicMock(return_value='text/html')
    mock_bytes_parser.return_value.parse.return_value = mock_msg

    content = parse_eml_content("dummy.eml")
    assert "Dear Committee," in content
    assert "I would like to nominate Professor Gamma." in content # Check for text extraction
    assert "He is great." in content
    assert "Also, Professor Delta is quite good." in content

def test_extract_professors_opinions_for_teacher_no_aliases():
    eml_texts = ["Professor Alpha is great. Alpha is dedicated.", "More about Professor Beta."]
    opinions = extract_professors_opinions_for_teacher("Professor Alpha", eml_texts, context_window_lines=0)
    assert len(opinions) == 1
    assert opinions[0] == "Professor Alpha is great. Alpha is dedicated."

    opinions_beta = extract_professors_opinions_for_teacher("Professor Beta", eml_texts, context_window_lines=0)
    assert len(opinions_beta) == 1
    assert opinions_beta[0] == "More about Professor Beta."

def test_extract_professors_opinions_for_teacher_with_aliases():
    eml_texts = [
        "Prof. Alpha is great.", 
        "Also, Dr. A. did a fantastic job this semester.",
        "Regarding Prof. Beta, some feedback."
    ]
    teacher_name = "Professor Alpha"
    aliases = ["Prof. Alpha", "Dr. A."]
    
    opinions = extract_professors_opinions_for_teacher(
        teacher_name, 
        eml_texts, 
        context_window_lines=0, 
        teacher_aliases=aliases
    )
    assert len(opinions) == 2
    assert "Prof. Alpha is great." in opinions
    assert "Also, Dr. A. did a fantastic job this semester." in opinions

def test_extract_professors_opinions_for_teacher_context_window():
    eml_texts = [
        "Line 1: Previous unrelated sentence.\nLine 2: Professor Delta is truly outstanding.\nLine 3: Her dedication is clear.\nLine 4: Another sentence after."
    ]
    # Aliases not critical for this specific context test, but can be None
    expected_snippet = "Line 1: Previous unrelated sentence.\nLine 2: Professor Delta is truly outstanding.\nLine 3: Her dedication is clear."
    opinions = extract_professors_opinions_for_teacher("Professor Delta", eml_texts, context_window_lines=1, teacher_aliases=None)
    assert len(opinions) == 1
    assert opinions[0] == expected_snippet.strip() # Ensure comparison handles potential strip in func

def test_extract_professors_opinions_word_boundaries():
    eml_texts = ["Thomas is a good teacher. Thom Yorke is a musician. Mr. Thomas said so."]
    teacher_name = "Thomas"
    aliases = ["Tom"] # No alias "Thom" to avoid matching Thom Yorke
    
    # Test for "Thomas"
    opinions_thomas = extract_professors_opinions_for_teacher(teacher_name, eml_texts, context_window_lines=0, teacher_aliases=None)
    assert len(opinions_thomas) == 1
    assert "Thomas is a good teacher. Thom Yorke is a musician. Mr. Thomas said so." in opinions_thomas # The whole line gets matched
    # Correcting: The function adds unique snippets. If Thomas appears twice in one line, that line is one snippet.
    # Re-evaluating based on current implementation: it iterates lines, then terms. If term found, adds snippet, breaks from terms, goes to next line.
    # So if a line has "Thomas ... Thomas", it is added once for the first "Thomas".
    # Let's make lines distinct to test this better.
    eml_texts_distinct = ["Thomas is a good teacher.", "Thom Yorke is a musician.", "Mr. Thomas said so."]
    opinions_thomas_distinct = extract_professors_opinions_for_teacher(teacher_name, eml_texts_distinct, context_window_lines=0, teacher_aliases=None)
    assert len(opinions_thomas_distinct) == 2
    assert "Thomas is a good teacher." in opinions_thomas_distinct
    assert "Mr. Thomas said so." in opinions_thomas_distinct
    assert "Thom Yorke is a musician." not in opinions_thomas_distinct

    # Test for alias "Tom"
    eml_texts_alias = ["Tom is excellent.", "Tommy is his son.", "Bottom line is clear."]
    opinions_tom = extract_professors_opinions_for_teacher(teacher_name, eml_texts_alias, context_window_lines=0, teacher_aliases=["Tom"])
    assert len(opinions_tom) == 1
    assert "Tom is excellent." in opinions_tom
    assert "Tommy is his son." not in opinions_tom # \bTom\b will not match Tommy
    assert "Bottom line is clear." not in opinions_tom # \bTom\b will not match Bottom

@patch(ALIAS_GENERATOR_PATH) # Mock the alias generator call
@patch("class_teacher_awards.data_extraction.eml_parser.parse_eml_content")
def test_get_all_professors_opinions_success(mock_parse_eml, mock_generate_aliases, mock_file_open):
    teachers = ["Professor Alpha", "Professor Beta"]
    # Mock parse_eml_content to return some text
    mock_parse_eml.side_effect = [
        "Content mentioning Professor Alpha and an alias AlphaAlias.", 
        "More text with Professor Beta herself, not just Prof. Beta."
    ]
    
    # Mock generate_teacher_aliases behavior
    def mock_alias_func(teacher_name, all_teachers_list):
        if teacher_name == "Professor Alpha":
            return ["AlphaAlias"]
        return [] # No aliases for Beta
    mock_generate_aliases.side_effect = mock_alias_func
    
    # Configure EML_FILE_PATHS used by the function (via patching config or directly)
    with patch("class_teacher_awards.data_extraction.eml_parser.EML_FILE_PATHS", ["file1.eml", "file2.eml"]):
        result = get_all_professors_opinions(teachers)

    # Assert generate_teacher_aliases was called for each teacher
    assert mock_generate_aliases.call_count == len(teachers)
    mock_generate_aliases.assert_any_call("Professor Alpha", teachers)
    mock_generate_aliases.assert_any_call("Professor Beta", teachers)

    # Assert opinions are found
    assert "Professor Alpha" in result
    assert len(result["Professor Alpha"]) > 0
    assert "Content mentioning Professor Alpha and an alias AlphaAlias." in result["Professor Alpha"][0]
    
    assert "Professor Beta" in result
    assert len(result["Professor Beta"]) > 0
    assert "More text with Professor Beta herself, not just Prof. Beta." in result["Professor Beta"][0]

@patch(ALIAS_GENERATOR_PATH, return_value=[]) # Default mock for no aliases
@patch("class_teacher_awards.data_extraction.eml_parser.parse_eml_content", return_value="")
def test_get_all_professors_opinions_no_eml_content(mock_parse_eml, mock_generate_aliases_empty, mock_file_open):
    teachers = ["Professor Gamma"]
    with patch("class_teacher_awards.data_extraction.eml_parser.EML_FILE_PATHS", ["empty.eml"]):
        result = get_all_professors_opinions(teachers)
    
    assert result["Professor Gamma"] == []
    mock_generate_aliases_empty.assert_not_called() # Still called

@patch(ALIAS_GENERATOR_PATH, return_value=[])
@patch("class_teacher_awards.data_extraction.eml_parser.parse_eml_content")
def test_get_all_professors_opinions_no_eml_files(mock_parse_eml, mock_generate_aliases_no_files, mock_file_open):
    teachers = ["Professor Delta"]
    with patch("class_teacher_awards.data_extraction.eml_parser.EML_FILE_PATHS", []): # No EML files configured
        result = get_all_professors_opinions(teachers)
    
    assert result["Professor Delta"] == []
    mock_generate_aliases_no_files.assert_not_called() # Should not be called if no EML paths
    mock_parse_eml.assert_not_called()

# (Add more tests for edge cases, context window variations if necessary) 