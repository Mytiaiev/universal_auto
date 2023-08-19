#!/bin/bash
sudo nginx -g 'daemon on;'
gunicorn auto.wsgi:application --bind "0.0.0.0:8000" --log-level debug --timeout 600

