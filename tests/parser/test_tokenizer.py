from toolchain.parser.tokenizer import tokenize


def test_tokenizer_emits_keywords_and_arrow():
    source = "handle RegisterUser -> UserRegistered with effects [db.write, emit] {}"
    kinds = [token.kind for token in tokenize(source)]
    assert "HANDLE" in kinds
    assert "ARROW" in kinds
    assert "EFFECTS" in kinds
    assert kinds[-1] == "EOF"
