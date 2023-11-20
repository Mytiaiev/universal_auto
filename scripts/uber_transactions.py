import sys

print(sys.path)
sys.path.append('app/')
from app.models import UberTransactions


def run():
    file_name = input('Please enter file name: ')
    UberTransactions.save_transactions_to_db(file_name)
    print("Transactions added to DB")
