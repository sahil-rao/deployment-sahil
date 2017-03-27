#!/bin/bash

set -euv

# Hardcode the boto versions to make sure it works for Cloudwatch Logs
pip install boto3==1.4.4
pip install --upgrade botocore==1.5.26
