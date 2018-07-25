#!/bin/bash
# Copyright 2018 Julien Peloton
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Parameters (put your file)
outpath="output"
logfile="/home/julien.peloton/Spectractor/ctiofulllogbook_jun2017_v5.csv"

cd ../
rm spectractor.zip
zip -r spectractor.zip spectractor
cd spark_test

# Run it day-by-day!
for directory in $(hdfs dfs -ls -C CTIODataJune2017_reduced_RG715_v2); do
    echo $directory
    datapath="hdfs://134.158.75.222:8020/user/julien.peloton/${directory}/*.fits"
    spark-submit \
        --master spark://134.158.75.222:7077 \
        --driver-memory 15g --executor-memory 29g --executor-cores 17 --total-executor-cores 153 \
        --py-files /home/julien.peloton/Spectractor/spectractor.zip \
        sparktractor.py \
        -datapath $datapath -outpath $outpath -filesystem hdfs -logfile $logfile -log_level ERROR
done
