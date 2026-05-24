from health_tools import format_health_data

def test_format_health_data_basic(sample_health_data):
    formatted = format_health_data(sample_health_data)
    assert "3969" in formatted
    assert "72" in formatted
    assert isinstance(formatted, str)

def test_format_health_data_empty():
    assert isinstance(format_health_data({}), str)
