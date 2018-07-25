#!/bin/bash
#SBATCH -p debug
#SBATCH -N 40
#SBATCH -t 00:15:00
#SBATCH -J spectractor
#SBATCH -C haswell
#SBATCH --image=nersc/spark-2.3.0:v1
#SBATCH -A m1727

module load spark
module load sbt

# Parameters (put your file)
outpath="/global/cscratch1/sd/peloton/output_ctio"
logfile="/global/homes/p/peloton/Spectractor/ctiofulllogbook_jun2017_v5.csv"
# For NERSC only (direct glob)
datapath="/global/cscratch1/sd/peloton/ctio/CTIODataJune2017_reduced_RG715_v2"

# Do not forget to produce a ZIP with the latest change
# You can find below the command to execute -->
# cd /global/homes/p/peloton/Spectractor
# rm spectractor.zip
# zip -r spectractor.zip spectractor
# cd /global/homes/p/peloton/Spectractor/spark_test

# Run it!
start-all.sh

# Run it!
shifter spark-submit \
  --master $SPARKURL \
  --driver-memory 15g --executor-memory 50g --executor-cores 32 --total-executor-cores 1280 \
  --py-files /global/homes/p/peloton/Spectractor/spectractor.zip \
  /global/homes/p/peloton/Spectractor/spark_test/sparktractor.py \
  -datapath $datapath -outpath $outpath -filesystem lustre -logfile $logfile -log_level ERROR

stop-all.sh
