#!/bin/bash

j2 /hosts.j2 /config.json > /var/Baaz/hosts.cfg

if [ "$SERVICE_NAME" == "applicationservice" ]
then
j2 /logback.j2 /config.json > /usr/lib/baaz_compiler/logback.xml
export COMPILER_PORT=12121
export HIVE_HOME=/usr/local/hive
/usr/local/bin/xplaincompileserver & sudo COMPILER_PORT=$COMPILER_PORT python /usr/local/bin/ApplicationService.py

elif [ "$SERVICE_NAME" == "compileservice" ]
then
j2 /logback.j2 /config.json > /usr/lib/baaz_compiler/logback.xml
export COMPILER_PORT=13131
export HIVE_HOME=/usr/local/hive
/usr/local/bin/xplaincompileserver & sudo COMPILER_PORT=$COMPILER_PORT python /usr/local/bin/BaazCompileService.py

elif [ "$SERVICE_NAME" == "advanalytics" ]
then
j2 /logback.j2 /config.json > /usr/lib/baaz_compiler/logback.xml
export COMPILER_PORT=14141
export HIVE_HOME=/usr/local/hive
/usr/local/bin/xplaincompileserver & sudo COMPILER_PORT=$COMPILER_PORT python /usr/local/bin/XplainAdvAnalyticsService.py

elif [ "$SERVICE_NAME" == "mathservice" ]
then
sudo python /usr/local/bin/BaazMathService.py

elif [ "$SERVICE_NAME" == "ruleengineservice" ]
then
sudo python /usr/local/bin/RuleEngineService.py

elif [ "$SERVICE_NAME" == "elasticpub" ]
then
sudo python /usr/local/bin/ElasticPubService.py

elif [ "$SERVICE_NAME" == "dataacquisitionservice" ]
then
sudo python /usr/local/bin/FPProcessingService.py

else
echo "No service was found for the inputted service"
fi