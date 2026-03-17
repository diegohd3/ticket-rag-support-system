from app.application.services.query_analyzer import QueryAnalyzer


def test_analyze_extracts_error_codes_tags_and_keywords() -> None:
    analyzer = QueryAnalyzer()
    result = analyzer.analyze(
        "Tengo error ERR-401 en login #auth #portal cuando intento entrar al sistema"
    )

    assert result.error_codes == ["ERR-401"]
    assert result.tags == ["auth", "portal"]
    assert "login" in result.keywords
    assert "sistema" in result.keywords
    assert "tengo" not in result.keywords
