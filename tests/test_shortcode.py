import pytest

from app.shortcode import ALPHABET, InvalidAlias, generate_code, validate_alias


def test_generate_code_length_and_alphabet():
    code = generate_code(7)
    assert len(code) == 7
    assert all(c in ALPHABET for c in code)


def test_generate_code_is_random():
    assert len({generate_code(8) for _ in range(50)}) > 1


@pytest.mark.parametrize("alias", ["abc", "my-link", "A_b-9", "x" * 32])
def test_valid_aliases_pass_through(alias):
    assert validate_alias(alias) == alias


@pytest.mark.parametrize("alias", ["ab", "x" * 33, "has space", "dots.here", "slash/y", ""])
def test_bad_aliases_rejected(alias):
    with pytest.raises(InvalidAlias):
        validate_alias(alias)


@pytest.mark.parametrize("alias", ["api", "API", "healthz", "static", "admin"])
def test_reserved_aliases_rejected(alias):
    with pytest.raises(InvalidAlias):
        validate_alias(alias)
