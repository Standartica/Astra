from toolchain.compiler.binder import ExternalModuleSymbols, bind_module
from toolchain.parser.parser import parse_source


def test_binder_reports_unknown_type():
    module = parse_source(
        """
module users
schema User {
  id: MissingType
}
"""
    )
    result = bind_module(module, source="module users\nschema User {\n  id: MissingType\n}\n")
    assert any(item.code == "ASTRA2001" for item in result.diagnostics.items)


def test_binder_resolves_imported_symbols():
    module = parse_source(
        """
module users
import common as core
schema User {
  id: core.UserId
}
"""
    )
    result = bind_module(module, source="", external_modules=[ExternalModuleSymbols(module_name="common", alias="core", symbols={"UserId": "type"})])
    assert not any(item.code == "ASTRA2001" for item in result.diagnostics.items)
