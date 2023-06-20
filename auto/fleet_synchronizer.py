import csv
import json
import logging
import os
import pickle
import time
import datetime
from decimal import Decimal

import redis
import requests
from django.db import IntegrityError
from django.utils import timezone
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import TimeoutException, WebDriverException, InvalidSessionIdException
from translators.server import tss
from app.models import Driver, Fleets_drivers_vehicles_rate, Fleet, Vehicle, UseOfCars, RentInformation, StatusChange, \
    ParkSettings, UberService, UaGpsService, NewUklonService, BoltService, NewUklonFleet, BoltPaymentsOrder, \
    NewUklonPaymentsOrder, UberPaymentsOrder, UberTrips
from auto import settings
from auto.drivers import Bolt, NewUklon, Uber, UaGps, clickandclear, SeleniumTools

















