from datetime import datetime, timedelta

import pendulum
from django.db.models import Sum, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone

from app.models import Driver, Payments, SummaryReport
from auto.tasks import download_daily_report, send_weekly_report, send_efficiency_report
from selenium_ninja.uber_sync import UberSynchronizer


def run(*args):
    # download_daily_report.delay("2023-07-09")
    end = timezone.localtime().date() - timedelta(days=timezone.localtime().weekday() + 1)
    start = end - timedelta(days=6)
    message = ''
    for driver in Driver.objects.all():
        driver_report = SummaryReport.objects.filter(report_from__range=(start, end),
                                                     full_name=driver)
        non_zero_reports = driver_report.exclude(total_amount=0.00)
        kasa = non_zero_reports.aggregate(
            kasa=Coalesce(Sum('total_amount_without_fee'), 0, output_field=DecimalField()))['kasa']
        cash = non_zero_reports.aggregate(
            cash=Coalesce(Sum('total_amount_cash'), 0, output_field=DecimalField()))['cash']
        salary = kasa * driver.rate - cash
        message += f"Загальна каса {driver}:{kasa}\n"
        message += f'Зарплата за тиждень {kasa}*{driver.rate}- Готівка {cash} = {salary}\n'
        message += "*" * 39 + '\n'
    print(message)
    #     if r:
    #         r = r[0]
    #         name = driver.full_name()
    #         reports[name] = reports.get(name, '') + r.report_text(name, float(rate.driver.rate)) + '\n'
    #         totals[name] = totals.get(name, 0) + r.kassa()
    #         salary[name] = salary.get(name, 0) + r.total_drivers_amount(float(rate.driver.rate))
    #
    # totals = {k: v for k, v in totals.items() if v != 0.0}
    # return totals, salary, reports
