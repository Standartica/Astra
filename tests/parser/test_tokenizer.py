from toolchain.parser.tokenizer import tokenize


def test_tokenizer_emits_string_and_import_tokens():
    source = """import shared
api Users {
  get \"/users/{id}\" -> GetUser
}
"""
    tokens = list(tokenize(source))
    kinds = [token.kind for token in tokens]
    assert "IMPORT" in kinds
    assert "API" in kinds
    assert "GET" in kinds
    assert "STRING" in kinds
