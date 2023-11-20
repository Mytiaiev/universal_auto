import pytest
from app.models import WeeklyReportFile

wrf = WeeklyReportFile()


@pytest.mark.django_db
def test_weekly_report_file_create():
    weekly_report_file = WeeklyReportFile.objects.create(
        organization_name="uber",
        report_file_name="20220829-20220904-payments_driver-___.csv",
        report_from="2022-08-29",
        report_to="2022-09-04",
        file="Data reports")
    assert weekly_report_file.organization_name == "uber"
    assert weekly_report_file.report_file_name == "20220829-20220904-payments_driver-___.csv"
    assert weekly_report_file.report_from == "2022-08-29"
    assert weekly_report_file.report_to == "2022-09-04"
    assert weekly_report_file.file == "Data reports"
    assert WeeklyReportFile.objects.count() == 1


# Checks the function on files in the main folder
@pytest.mark.django_db
def test_save_data_to_db():
    wrf.save_weekly_reports_to_db()
    assert True


# Checks 7 days in report
@pytest.mark.parametrize("start, end, filename", [("2022-08-29", "2022-09-05", "file_name"),
                                                  ("2022-10-08", "2022-10-15", "file_name"),
                                                  ("2023-10-08", "2023-10-15", "file_name")])
def test_check_full_data_all(start, end, filename):
    assert wrf.check_full_data(start, end, filename) == True


# Checks more or less days in report
@pytest.mark.parametrize("start, end, filename", [("2022-08-29", "2022-09-04", "file_name"),
                                                  ("2022-10-08", "2022-10-18", "file_name"),
                                                  ("2023-10-08", "2024-10-15", "file_name"),
                                                  ("2022-10-08", "2022-09-08", "file_name")])
def test_check_full_data_not_all(start, end, filename):
    assert wrf.check_full_data(start, end, filename) == False


@pytest.mark.parametrize("start, end, filename, expected_exception",
                         [(20220829, 20220904, "file_name", TypeError),
                          ("4904394595", "2022-10-18", "file_name", ValueError),
                          ("last_name", "first_name", "file_name", ValueError)])
def test_check_full_data_errors(start, end, filename, expected_exception):
    with pytest.raises(expected_exception):
        wrf.check_full_data(start, end, filename)