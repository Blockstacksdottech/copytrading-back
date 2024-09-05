from celery import shared_task
from .handler.Fetcher import Fetcher
from .models import Strategy


@shared_task
def test():
    print("This is a test task")


@shared_task
def fetch_data():
    print("fetching the data")
    strategies = Strategy.objects.filter(enabled=True)
    for strat in strategies:
        f = Fetcher()
        print("executing")
        f.execute(strat.sheetUrl,float(strat.accountSize),strat)
    print("done")
    
