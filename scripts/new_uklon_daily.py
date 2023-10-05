from selenium_ninja.bolt_sync import BoltRequest


def run(*args):
    BoltRequest(4).get_access_token()
