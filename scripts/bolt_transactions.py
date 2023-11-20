from app.models import BoltTransactions

def run():
    file_name = input('Please enter file name: ')
    BoltTransactions.save_transactions_to_db(file_name)
    print("Transactions added to DB")
