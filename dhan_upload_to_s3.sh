#!/bin/bash
aws s3 cp dhan.py s3://tradebot01/dhan/dhan.py
aws s3 cp dhan.txt s3://tradebot01/dhan/dhan.txt
aws s3 cp .env s3://tradebot01/dhan/.env
aws s3 cp telegram.py s3://tradebot01/dhan/telegram.py
aws s3 cp session.session s3://tradebot01/dhan/session.session
aws s3 cp security_mapping.csv s3://tradebot01/dhan/security_mapping.csv