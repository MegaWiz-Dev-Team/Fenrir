"""Tests for fenrir.browser.tasks — Task Router."""

from fenrir.browser.tasks import route_task


class TestTaskRouter:
    """Task routing tests."""

    def test_fhir_patient_search(self):
        """Patient search should route to FHIR."""
        result = route_task("search patient named John Smith")
        assert result.method == "fhir"
        assert result.tool_name == "fhir_search_patient"

    def test_fhir_patient_register(self):
        """Patient registration should route to FHIR."""
        result = route_task("register patient นายสมชาย อายุ 45 ปี")
        assert result.method == "fhir"
        assert result.tool_name == "fhir_create_patient"

    def test_fhir_thai_search(self):
        """Thai keyword should also route to FHIR."""
        result = route_task("ค้นหาคนไข้ชื่อ สมชาย")
        assert result.method == "fhir"
        assert result.tool_name == "fhir_search_patient"

    def test_browser_form_fill(self):
        """Form filling should route to browser."""
        result = route_task("กรอกแบบฟอร์มส่งตัวผู้ป่วย")
        assert result.method == "browser"

    def test_browser_report(self):
        """Report printing should route to browser."""
        result = route_task("print report for patient visit")
        assert result.method == "browser"

    def test_fallback_to_browser(self):
        """Unknown tasks should fallback to browser."""
        result = route_task("do something completely unknown")
        assert result.method == "browser"
        assert "falling back" in result.reason.lower()

    def test_route_result_has_fields(self):
        """TaskRouteResult should have all required fields."""
        result = route_task("test task")
        assert result.method in ("fhir", "browser")
        assert result.tool_name
        assert result.reason
        assert isinstance(result.params, dict)
