from toolchain.parser.tokenizer import tokenize


def test_tokenizer_recognizes_keywords_and_string():
    tokens = list(tokenize('module users\napi Users { get "/users" -> GetUsers }'))
    kinds = [token.kind for token in tokens]
    assert "MODULE" in kinds
    assert "API" in kinds
    assert "GET" in kinds
    assert "STRING" in kinds
