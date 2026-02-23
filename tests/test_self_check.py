from app import self_check


def test_required_list_has_core_deps():
    assert "streamlit" in self_check.REQUIRED
    assert "pandas" in self_check.REQUIRED
