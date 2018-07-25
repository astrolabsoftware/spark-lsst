# Sparktractor: Spectractor with Apache Spark <a name="Sparktractor--Spectractor-with-Apache-Spark"></a>

<!-- toc -->

## Contents:

1. [Sparktractor: Spectractor with Apache Spark](#Sparktractor--Spectractor-with-Apache-Spark)
   1. [The original package](#The-original-package)
   1. [How to use it?](#How-to-use-it?)
      1. [Code source](#Code-source)
      1. [Apache Spark cluster (with HDFS)](#Apache-Spark-cluster--with-HDFS-)
      1. [Cori@NERSC](#Cori@NERSC)
   1. [Benchmarks](#Benchmarks)
      1. [Apache Spark vs MPI @ NERSC](#Apache-Spark-vs-MPI-@-NERSC)

<!-- endtoc -->

## The original package <a name="The-original-package"></a>

[Spectractor](https://github.com/LSSTDESC/Spectractor) is primarily developed by Jérémy Neveu.

The goal of Spectractor is to extract spectra from CTIO images in order to test the performance of dispersers dedicated to the LSST Auxiliary Telescope, and characterize the atmospheric transmission.

In this example, we focus on spectra extraction from CTIO images. The way Spectractor works suits very well to Apache Spark: each of the 3300 images to process is independent from the others, and the volume of data collected is rather big (106 GB) and will be bigger and bigger over the time.

In the end, out of ∼ 9000 lines of python codes in the original Spectractor code, ∼20 lines were modified or added!

## How to use it? <a name="How-to-use-it?"></a>

#### Code source

First fork and clone the [JulienPeloton/Spectractor](https://github.com/JulienPeloton/Spectractor) repository, and pull the branch `spark`. For the moment this branch lives in my fork, but later it will be merged in the original repository (I keep it sync with the original).

Each machine needs to know the code to execute. That means the Spectractor package (which usually lives in your driver) needs to be either installed on all machines (not scalable) or shipped at execution. I advice the latter if the size of the repo is not too big (a priori you do not have GB of python files...!). This is achieved by zipping the code (files or set of files within folders) thanks to the argument `--py-file <.zip of the repo>`:

```bash
spark-submit \
--master $SPARKURL \
--driver-memory 15g --executor-memory 50g --executor-cores 32 --total-executor-cores 1280 \
--py-files /path/to/spectractor.zip \
/path/to/sparktractor.py <args>
```

For reference, we provide such a zip of the code (with modification for the Spark cluster@LAL and Cori@NERSC) produced using:

```bash
# Move to Spectractor root 
cd /path/to/Spectractor
# Zip the folder containing sources
zip -r spectractor.zip spectractor
```

#### Apache Spark main

We provide a python script to launch Spectractor with Spark: [sparktractor.py](https://github.com/astrolabsoftware/spark-lsst/blob/master/Spectractor/sparktractor.py). The main idea behind is:

```python
# Distribute the computation over dataNodes containing images
spectra = spark.sparkContext.binaryFiles(<data path>)\
	# Extract additional informations from user file 
	.map(lambda x: <data + load external information>)\
	# Filter out images considered as bad 
	.filter(lambda x: <condition>)\
	# Run Spectractor on remaining images 
	.map(lambda x: <run Spectractor>)\
	# collect back each core output (spectra here).
	.collect()
```

There are few caveats:

- Spark is a framework to perform distributed computing. Therefore you are expected to work with distant machines so absolute paths are not valid here. Especially variable like `os.getenv("HOME")` does not mean much in this context (each machine will have its own `$HOME`). They have to be replaced in the code with meaningful path (if possible).
- If your code needs to read local data, it has be known by all the machines. There are several ways of doing that:
 1. Duplicate and store the data onto all executors prior to the job.
 2. Broadcast the data from the driver to the executors at the beginning of the job.
 3. Store the data on a distant server, and each executor will query or download the data on-the-fly during the run.

Obviously, solution 1. is by far the one easiest but the one which won't scale for thousand machines... Solution 2. is great if the volume of data is not big (you do not want to broadcast GB of data though...). Solution 3. is Spark-proof but requires an internet connection, a distant storage place, and modification in the code to the download the data.

#### Data from external DB

Spectractor needs external DB such as NED or Simbad (online -- no problem), but also calibration data from [synphot](http://astroconda.readthedocs.io/en/latest/) which need to be downloaded and read from disk. The needed data is about 50 MB on disk. On a Spark cluster we just shamelessly duplicate the data onto all executors (9 machines), but solution 3. is envisaged (FITS can be read from distant URL).

#### User parameter file

Spectractor also needs a parameter file containing flags and extra information on the observation condition. We opted for the solution 2. (broadcast) since the log file is very small (KB).

### Apache Spark cluster (with HDFS) <a name="Apache-Spark-cluster--with-HDFS-"></a>

We provide a launcher ([run_benchmarks_python_cluster.sh](https://github.com/astrolabsoftware/spark-lsst/blob/master/Spectractor/run_benchmarks_python_cluster.sh)) to use on a Spark cluster with HDFS for the file system. For simplicity we loop over days of observation, but one could as well process the entire data set at once.

### Cori@NERSC <a name="Cori@NERSC"></a>

We provide a launcher ([run_benchmarks_python_cori.sh](https://github.com/astrolabsoftware/spark-lsst/blob/master/Spectractor/run_benchmarks_python_cori.sh)) to use on Cori at NERSC, on a Lustre file system (default). Note that you would have to zip yourself the latest version of Spectractor prior to launch the job (see comment in the launcher).

What is good with HPC machines here, is that they are not really distributed hence global variable and path to local data will work.

## Benchmarks <a name="Benchmarks"></a>

### Apache Spark vs MPI @ NERSC <a name="Apache-Spark-vs-MPI-@-NERSC"></a>

In this benchmark, we compare the runtime of Spectractor if we use Apache Spark or MPI to schedule the different tasks.

- Data set: Full CTIO (3363 images, 106 GB on disk)
- Machine: Cori @ NERSC
- Numbers of cores: 1280 (40 nodes of 32 cores each)
- File system: Lustre (no OST optimisation)

|                     |   Apache Spark  |      MPI      |
|:-------------------:|:---------------:|:--------------|
| Raw Core Hours Used | 284 CPUh        | 552 CPUh      |
| User time           | 14 min          | 26 min        |

For Spark, among the 14 min (user time), 8 min were dedicated to raw I/O and computation and the rest was spent in latency or queries to external DB.

For the MPI version of Spectractor, see [here](https://github.com/astrolabsoftware/spark-lsst/tree/master/Spectractor/mpi).
