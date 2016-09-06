#!/bin/sh

set -eu

echo -n 'never' > /sys/kernel/mm/transparent_hugepage/enabled
echo -n 'never' > /sys/kernel/mm/transparent_hugepage/defrag
