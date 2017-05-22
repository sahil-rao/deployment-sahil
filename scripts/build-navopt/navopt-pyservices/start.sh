#!/bin/bash
set -m

# if any suprocess exits trap and exit

function chld_exit() {
  kill -9 $xplain_pid $python_pid
  exit 0
}

export COMPILER_PORT=12121
export HIVE_HOME=/usr/local/hive

case "$SERVICE_NAME" in
  "applicationservice" )
    python_service=/usr/local/bin/ApplicationService.py
    java_svc='yes'
  ;;
  "compileservice" )
    python_service=/usr/local/bin/BaazCompileService.py
    java_svc='yes'
  ;;
  "advanalytics" )
    python_service=/usr/local/bin/XplainAdvAnalyticsService.py
    java_svc='yes'
  ;;
  "apiservice" )
    python_service=/usr/local/bin/ApiService.py
    java_svc='yes'
  ;;
  "mathservice" )
    python_service=/usr/local/bin/BaazMathService.py
  ;;
  "ruleengineservice" )
    python_service=/usr/local/bin/RuleEngineService.py
  ;;
  "elasticpub" )
    python_service=/usr/local/bin/ElasticPubService.py
  ;;
  "dataacquisitionservice" )
    python_service=/usr/local/bin/FPProcessingService.py
  ;;
  * )
    echo "No service was found for the given argument"
    exit 1
  ;;
esac

j2 /hosts.j2 /config.json > /var/Baaz/hosts.cfg
j2 /logback.j2 /config.json > /usr/lib/baaz_compiler/logback.xml

trap chld_exit CHLD

if [ ! -z "$java_svc" ]
then
  (/usr/local/bin/xplaincompileserver) &
  xplain_pid=$!
fi

(/usr/bin/python $python_service) &
python_pid=$!

wait
