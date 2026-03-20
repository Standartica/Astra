from toolchain.compiler.binder import bind_module
from toolchain.parser.parser import parse_source


def test_binder_reports_unknown_types_and_missing_symbols():
    source = """
module broken

command RegisterUser {
  email: MissingType
}

handle RegisterUser -> MissingEvent with effects [emit] {
}
"""
    module = parse_source(source)
    result = bind_module(module)
    codes = {item.code for item in result.diagnostics.items}
    assert "ASTRA2001" in codes
    assert "ASTRA2004" in codes
