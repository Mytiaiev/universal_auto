from selenium_ninja.bolt_sync import BoltRequest


def run(*args):
    BoltRequest(1).get_login_token()

