from auto.tasks import download_weekly_report


def run(*args):
    if args:
        week_number = f"2022W{args[0]}5"
    else:
        week_number = None
    print(download_weekly_report.delay())
