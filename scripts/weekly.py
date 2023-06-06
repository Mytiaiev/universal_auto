from auto.tasks import download_reports


def run(*args):
    if args:
        week_number = f"2022W{args[0]}5"
    else:
        week_number = None
    print(download_reports())






