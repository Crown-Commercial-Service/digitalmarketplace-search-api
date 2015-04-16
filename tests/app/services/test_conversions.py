from nose.tools import assert_equal
from app.main.services.conversions import strip_and_lowercase


def test_should_strip_whitespace_and_symbols():
    cases = [
        ("this", "this"),
        ("THIS", "this"),
        ("THIS ", "this"),
        (" THiS ", "this"),
        (" THi''S ", "this"),
        (" 123THi''S ", "123this"),
        (" 1\\!23THi''S ", "123this"),
    ]

    for example, expected in cases:
        yield \
            assert_equal, \
            strip_and_lowercase(example), \
            expected, \
            example
