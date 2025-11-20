#!/usr/bin/env python3
from pyspark.sql import SparkSession

if __name__ == "__main__":
    spark = SparkSession.builder.appName("WordCount").getOrCreate()
    
    text = spark.sparkContext.parallelize([
        "Hello Spark", 
        "Hello World", 
        "Spark is awesome"
    ])
    
    counts = text.flatMap(lambda line: line.split(" ")) \
                 .map(lambda word: (word, 1)) \
                 .reduceByKey(lambda a, b: a + b)
    
    for word, count in counts.collect():
        print(f"{word}: {count}")
    
    spark.stop()