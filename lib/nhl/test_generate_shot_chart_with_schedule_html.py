import unittest
from unittest.mock import patch, Mock
from fastapi.responses import HTMLResponse
from nhl_shot_chart import generate_shot_chart_with_schedule_html  # Adjust the import based on where your method is located.

class TestGenerateShotChartWithScheduleHtml(unittest.TestCase):

    @patch('nhl_shot_chart.generate_shot_chart_for_game')  # Adjust the module path accordingly
    @patch('nhl_shot_chart.generate_base64_image')
    @patch('nhl_shot_chart.generate_qr_code_for_text')
    def test_happy_path(self, mock_qr_code, mock_base64, mock_shot_chart):
        # Setup mock values
        mock_shot_chart.return_value = "mocked_shot_chart_image"
        mock_base64.return_value = "mocked_base64_image"
        mock_qr_code.return_value = "mocked_qr_code"

        response = generate_shot_chart_with_schedule_html("12345", "teamId", "seasonId", "America/New_York")
        
        self.assertIsInstance(response, HTMLResponse)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Shot Chart for Game ID", response.body.decode())
        
    @patch('nhl_shot_chart.generate_shot_chart_for_game', side_effect=Exception("Test Exception"))
    def test_error_path(self, _):
        response = generate_shot_chart_with_schedule_html("12345", "teamId", "seasonId", "America/New_York")
        
        self.assertIsInstance(response, HTMLResponse)
        self.assertEqual(response.status_code, 500)
        self.assertIn("Error Generating Shot Chart", response.body.decode())