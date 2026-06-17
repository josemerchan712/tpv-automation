from unittest.mock import patch, MagicMock

from app.config import settings


def test_weekly_report_success(client, admin_headers):
    """El endpoint devuelve 200 con campo 'informe' cuando Gemini responde OK."""
    mock_response = MagicMock()
    mock_response.text = "Resumen semanal: ventas estables."

    with patch("app.services.ai_service.genai") as mock_genai, \
         patch.object(settings, "GEMINI_API_KEY", "test-key"):
        mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_response
        response = client.post("/ai/weekly-report", headers=admin_headers)

    assert response.status_code == 200
    data = response.json()
    assert "informe" in data
    assert data["informe"] == "Resumen semanal: ventas estables."


def test_weekly_report_no_api_key(client, admin_headers):
    """Sin GEMINI_API_KEY el endpoint devuelve 503 con mensaje claro."""
    with patch.object(settings, "GEMINI_API_KEY", None):
        response = client.post("/ai/weekly-report", headers=admin_headers)

    assert response.status_code == 503
    assert "GEMINI_API_KEY" in response.json()["detail"]


def test_weekly_report_gemini_error(client, admin_headers):
    """Si Gemini falla, el endpoint devuelve 502 con mensaje amigable."""
    with patch("app.services.ai_service.genai") as mock_genai, \
         patch.object(settings, "GEMINI_API_KEY", "test-key"):
        mock_genai.GenerativeModel.return_value.generate_content.side_effect = Exception(
            "API rate limit exceeded"
        )
        response = client.post("/ai/weekly-report", headers=admin_headers)

    assert response.status_code == 502
    assert "Error al contactar" in response.json()["detail"]


def test_stock_analysis_success(client, admin_headers):
    """El endpoint de análisis de stock devuelve 200 con campo 'analisis'."""
    mock_response = MagicMock()
    mock_response.text = "Análisis de stock: producto X tiene alta rotación."

    with patch("app.services.ai_service.genai") as mock_genai, \
         patch.object(settings, "GEMINI_API_KEY", "test-key"):
        mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_response
        response = client.post("/ai/stock-analysis", headers=admin_headers)

    assert response.status_code == 200
    data = response.json()
    assert "analisis" in data
    assert data["analisis"] == "Análisis de stock: producto X tiene alta rotación."


def test_stock_analysis_no_api_key(client, admin_headers):
    """Sin GEMINI_API_KEY el endpoint de stock devuelve 503."""
    with patch.object(settings, "GEMINI_API_KEY", None):
        response = client.post("/ai/stock-analysis", headers=admin_headers)

    assert response.status_code == 503
    assert "GEMINI_API_KEY" in response.json()["detail"]
