"""External acceptance for structured invalid characters; existing warning strings remain."""
from mcp.shared.tool_name_validation import ToolNameValidationResult,validate_tool_name


def test_structured_invalid_characters_are_unique_and_ordered():
    value=validate_tool_name('a !é!💡é')
    assert value.is_valid is False
    assert value.invalid_characters==[' ','!','é','💡']
    assert value.warnings==[
        'Tool name contains spaces, which may cause parsing issues',
        "Tool name contains invalid characters: ' ', '!', 'é', '💡'",
        'Allowed characters are: A-Z, a-z, 0-9, underscore (_), dash (-), and dot (.)']


def test_valid_and_early_return_shapes_preserved():
    valid=validate_tool_name('abc_1.-X')
    assert valid.is_valid and valid.invalid_characters==[] and valid.warnings==[]
    empty=validate_tool_name('')
    assert empty.invalid_characters==[] and empty.warnings==['Tool name cannot be empty']
    long=validate_tool_name('!'*129)
    assert long.invalid_characters==[]
    assert long.warnings==['Tool name exceeds maximum length of 128 characters (current: 129)']


def test_existing_positional_construction_and_lists_are_independent():
    one=ToolNameValidationResult(False,['old warning'])
    two=ToolNameValidationResult(True)
    assert one.warnings==['old warning'] and one.invalid_characters==[]
    one.invalid_characters.append('!')
    assert two.invalid_characters==[]
