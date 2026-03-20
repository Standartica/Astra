from toolchain.parser.parser import parse_source


def test_parser_supports_alias_import_and_export():
    source = """
module users

import common as c
export RegisterUser

command RegisterUser {
}
"""
    module = parse_source(source)
    assert module.imports[0].module_name == "common"
    assert module.imports[0].alias == "c"
    assert module.exports[0].name == "RegisterUser"
