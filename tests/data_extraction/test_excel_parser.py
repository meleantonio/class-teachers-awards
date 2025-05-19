# Test file for excel_parser.py
# TODO: Add actual test cases using pytest
# - Mock pd.read_excel
# - Test get_teacher_names_from_excel with various inputs (empty file, file not found, different column names)
# - Test extract_positive_feedback_for_teacher (teacher found, not found, no comments, different column names)
# - Test get_all_teacher_feedback
# - Test get_all_teacher_names_from_sources

# Example (conceptual - needs pytest fixtures and mocks):
# def test_example_excel_parser():
#     assert True 

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from class_teacher_awards.data_extraction.excel_parser import (
    get_teacher_names_from_excel,
    extract_positive_feedback_for_teacher,
    get_all_teacher_feedback,
    get_all_teacher_names_from_sources
)
# Assuming config values are used for file paths, we might need to mock them or the functions using them.
# For now, let's focus on the logic within the functions, mocking the direct external calls.

@patch('pandas.read_excel')
def test_get_teacher_names_from_excel_success(mock_read_excel):
    mock_df = pd.DataFrame({'Instructor': ['Alice', 'Bob', 'Alice ', None, '  Charlie  ']})
    mock_read_excel.return_value = mock_df
    
    result = get_teacher_names_from_excel('dummy_path.xlsx', 'Sheet1')
    assert sorted(result) == sorted(['Alice', 'Bob', 'Charlie'])
    mock_read_excel.assert_called_once_with('dummy_path.xlsx', sheet_name='Sheet1')

@patch('pandas.read_excel')
def test_get_teacher_names_from_excel_file_not_found(mock_read_excel):
    mock_read_excel.side_effect = FileNotFoundError("File not found")
    result = get_teacher_names_from_excel('non_existent.xlsx', 'Sheet1')
    assert result == []

@patch('pandas.read_excel')
def test_get_teacher_names_from_excel_instructor_col_missing_fallback(mock_read_excel, capsys):
    mock_df = pd.DataFrame({
        'Some Other Name': ['David', None],
        'Instructor Name': ['Eve', 'Frank']
    })
    mock_read_excel.return_value = mock_df
    
    result = get_teacher_names_from_excel('dummy_path.xlsx', 'Sheet1', instructor_column_name='Instructor')
    assert sorted(result) == sorted(['Eve', 'Frank'])
    captured = capsys.readouterr()
    assert "Warning: Column 'Instructor' not found" in captured.out
    assert "Using 'Instructor Name' instead" in captured.out

@patch('pandas.read_excel')
def test_get_teacher_names_from_excel_instructor_col_missing_no_fallback(mock_read_excel, capsys):
    # Test the scenario where the specified instructor column is missing AND
    # NO suitable fallback column (containing 'instructor', 'name', or 'teacher') exists.
    mock_df = pd.DataFrame({'ColumnX': ['David'], 'ColumnY':['X']})
    mock_read_excel.return_value = mock_df
    
    result = get_teacher_names_from_excel('dummy_path.xlsx', 'Sheet1', instructor_column_name='Instructor')
    assert result == [] 
    captured = capsys.readouterr()
    assert "Error: Column 'Instructor' not found" in captured.out
    assert "and no alternative found." in captured.out

@patch('pandas.read_excel')
def test_extract_positive_feedback_for_teacher_success(mock_read_excel):
    mock_df = pd.DataFrame({
        'Instructor': ['Alice', 'Bob', 'Alice'],
        'Positive comments': ['Great!', 'Good job.', 'Excellent teaching.']
    })
    mock_read_excel.return_value = mock_df
    
    result = extract_positive_feedback_for_teacher('dummy.xlsx', 'Sheet1', 'Alice')
    assert sorted(result) == sorted(['Great!', 'Excellent teaching.'])

@patch('pandas.read_excel')
def test_extract_positive_feedback_for_teacher_name_not_found(mock_read_excel):
    mock_df = pd.DataFrame({
        'Instructor': ['Alice', 'Bob'],
        'Positive comments': ['Great!', 'Good job.']
    })
    mock_read_excel.return_value = mock_df
    result = extract_positive_feedback_for_teacher('dummy.xlsx', 'Sheet1', 'Charlie')
    assert result == []

@patch('pandas.read_excel')
def test_extract_positive_feedback_for_teacher_file_not_found(mock_read_excel):
    mock_read_excel.side_effect = FileNotFoundError
    result = extract_positive_feedback_for_teacher('non_existent.xlsx', 'Sheet1', 'Alice')
    assert result == []

@patch('pandas.read_excel')
def test_extract_positive_feedback_for_teacher_cols_missing_fallback(mock_read_excel, capsys):
    mock_df = pd.DataFrame({
        'Instructor Name': ['Alice', 'Bob'], 
        'Any good comment': ['Super!', 'Well done.']
    })
    mock_read_excel.return_value = mock_df
    
    result = extract_positive_feedback_for_teacher('dummy.xlsx', 'Sheet1', 'Alice', 
                                                   instructor_column_name='Instructor', 
                                                   comment_column_name='Positive comments')
    assert result == ['Super!']
    captured = capsys.readouterr()
    assert "Warning: Column 'Instructor' not found" in captured.out
    assert "Warning: Column 'Positive comments' not found" in captured.out
    assert "Using 'Any good comment' instead." in captured.out

@patch('class_teacher_awards.data_extraction.excel_parser.extract_positive_feedback_for_teacher')
def test_get_all_teacher_feedback(mock_extract_feedback):
    at24_file_mock = "dummy_AT 24 Results_file.xlsx"
    wt25_file_mock = "dummy_WT25 Course Survey_file.xlsx"
    
    with patch('class_teacher_awards.data_extraction.excel_parser.ECONOMICS_AT24_RESULTS_FILE', at24_file_mock), \
         patch('class_teacher_awards.data_extraction.excel_parser.ECONOMICS_WT25_SURVEY_FILE', wt25_file_mock), \
         patch('class_teacher_awards.data_extraction.excel_parser.POSITIVE_FEEDBACK_SHEET_NAME', 'FeedbackSheet'):

        def feedback_side_effect(file_path, sheet_name, teacher_name, instructor_column_name, comment_column_name):
            if teacher_name == 'Alice':
                if file_path == at24_file_mock:
                    assert instructor_column_name == "Instructor Name"
                    assert comment_column_name == "If you would like to add any positive comments about this instructor, please do so here:"
                    return ['Alice AT24 comment']
                elif file_path == wt25_file_mock:
                    assert instructor_column_name == "Instructor"
                    assert comment_column_name == "If you would like to add any positive comments about this class teacher, please do so here:"
                    return ['Alice WT25 comment']
            elif teacher_name == 'Bob':
                if file_path == at24_file_mock:
                    return ['Bob AT24 comment']
            return []
        
        mock_extract_feedback.side_effect = feedback_side_effect
        
        teachers = ['Alice', 'Bob']
        result = get_all_teacher_feedback(teachers)
        
        assert 'Alice' in result
        assert 'Bob' in result
        assert sorted(result['Alice']) == sorted(['Alice AT24 comment', 'Alice WT25 comment'])
        assert result['Bob'] == ['Bob AT24 comment']
        
        assert mock_extract_feedback.call_count == 4 
        mock_extract_feedback.assert_any_call(at24_file_mock, 'FeedbackSheet', 'Alice', instructor_column_name="Instructor Name", comment_column_name="If you would like to add any positive comments about this instructor, please do so here:")
        mock_extract_feedback.assert_any_call(wt25_file_mock, 'FeedbackSheet', 'Alice', instructor_column_name="Instructor", comment_column_name="If you would like to add any positive comments about this class teacher, please do so here:")
        mock_extract_feedback.assert_any_call(at24_file_mock, 'FeedbackSheet', 'Bob', instructor_column_name="Instructor Name", comment_column_name="If you would like to add any positive comments about this instructor, please do so here:")
        mock_extract_feedback.assert_any_call(wt25_file_mock, 'FeedbackSheet', 'Bob', instructor_column_name="Instructor", comment_column_name="If you would like to add any positive comments about this class teacher, please do so here:")

@patch('class_teacher_awards.data_extraction.excel_parser.get_teacher_names_from_excel')
def test_get_all_teacher_names_from_sources(mock_get_names):
    at24_file_mock = "dummy_AT 24 Results_file.xlsx"
    wt25_file_mock = "dummy_WT25 Course Survey_file.xlsx"

    with patch('class_teacher_awards.data_extraction.excel_parser.ECONOMICS_AT24_RESULTS_FILE', at24_file_mock), \
         patch('class_teacher_awards.data_extraction.excel_parser.ECONOMICS_WT25_SURVEY_FILE', wt25_file_mock), \
         patch('class_teacher_awards.data_extraction.excel_parser.POSITIVE_FEEDBACK_SHEET_NAME', 'FeedbackSheet'):

        def names_side_effect(file_path, sheet_name, instructor_column_name):
            if file_path == at24_file_mock:
                assert instructor_column_name == "Instructor Name"
                return ['Alice', 'Bob']
            elif file_path == wt25_file_mock:
                assert instructor_column_name == "Instructor"
                return ['Bob', 'Charlie', '']
            return []

        mock_get_names.side_effect = names_side_effect
        result = get_all_teacher_names_from_sources()
        assert sorted(result) == sorted(['Alice', 'Bob', 'Charlie'])
        
        mock_get_names.assert_any_call(at24_file_mock, 'FeedbackSheet', instructor_column_name='Instructor Name')
        mock_get_names.assert_any_call(wt25_file_mock, 'FeedbackSheet', instructor_column_name='Instructor')


