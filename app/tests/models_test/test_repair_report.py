import pytest
from app.models import RepairReport


@pytest.fixture
def test_repair_report(db) -> RepairReport:
    return RepairReport.objects.create(
        repair='https://api.telegram.org/file/bot5408955298:AAGEdvJmY0LC_g3THv9DvrpzzNtgu5cD9yo/photos/file_4.jpg',
        numberplate="BH1234KO",
        start_of_repair='2022-11-07 20:24:22+00',
        end_of_repair='2022-11-10 20:24:22+00',
        status_of_payment_repair='Unpaid')


def test_db(test_repair_report):
    assert test_repair_report.repair == 'https://api.telegram.org/file/bot5408955298:AAGEdvJmY0LC_g3THv9DvrpzzNtgu5cD9yo/photos/file_4.jpg'
    assert test_repair_report.numberplate == "BH1234KO"
    assert test_repair_report.start_of_repair == '2022-11-07 20:24:22+00'
    assert test_repair_report.end_of_repair == '2022-11-10 20:24:22+00'
    assert test_repair_report.status_of_payment_repair == 'Unpaid'


def test_field_length(test_repair_report):
    assert len(test_repair_report.repair) <= 255
    assert len(test_repair_report.numberplate) <= 12
    assert len(test_repair_report.status_of_payment_repair) <= 6


def test_type(test_repair_report):
    assert isinstance(test_repair_report.repair, str)
    assert isinstance(test_repair_report.numberplate, str)
    assert isinstance(test_repair_report.status_of_payment_repair, str)
