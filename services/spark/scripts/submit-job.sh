#!/bin/bash
/opt/spark/bin/spark-submit \
    --master spark://spark-master:7077 \
    --name "Spark-Job" \
    $@