# Sparktractor: Spectractor with Apache Spark <a name="Sparktractor--Spectractor-with-Apache-Spark"></a>

<!-- toc -->

## Contents:

1. [Sparktractor: Spectractor with Apache Spark](#Sparktractor--Spectractor-with-Apache-Spark)
   1. [The original package](#The-original-package)
   1. [Why would you use Apache Spark here?](#Why-would-you-use-Apache-Spark-here?)
   1. [What needs to be modified to use Apache Spark?](#What-needs-to-be-modified-to-use-Apache-Spark?)
      1. [Level 0: minimal intrusion](#Level-0--minimal-intrusion)
      1. [Level 1: code infection](#Level-1--code-infection)
   1. [How to use it?](#How-to-use-it?)
      1. [Apache Spark cluster (with HDFS)](#Apache-Spark-cluster--with-HDFS-)
      1. [Cori@NERSC](#Cori@NERSC)
   1. [Benchmarks](#Benchmarks)
      1. [Apache Spark vs MPI @ NERSC](#Apache-Spark-vs-MPI-@-NERSC)

<!-- endtoc -->

## The original package <a name="The-original-package"></a>

[Spectractor](https://github.com/LSSTDESC/Spectractor) is primarily developed by Jérémy Neveu.

The goal of Spectractor is to extract spectra from CTIO images in order to test the performance of dispersers dedicated to the LSST Auxiliary Telescope, and characterize the atmospheric transmission.

## Why would you use Apache Spark here? <a name="Why-would-you-use-Apache-Spark-here?"></a>

Although [Apache Spark](http://spark.apache.org/) is not primarily meant to bring further speed-up on the computation, it is very efficient to deal with and manage a large volume of data. It often provides better performances than other tools for this kind of embarrassingly parallel job by optimizing data distribution (load balancing) and minimizing I/O latency.
One should also mention that one of the strength of Spark is its simplicity to deal with pipeline and job management. Those are done automatically and often more efficiently than what we could do manually by scheduling tasks with MPI for example.

In this example, we focus on spectra extraction from CTIO images. The way Spectractor works suits very well to Apache Spark: each of the 3300 images to process is independent from the others, and the volume of data collected is rather big (106 GB) and will be bigger and bigger over the time.

## What needs to be modified to use Apache Spark? <a name="What-needs-to-be-modified-to-use-Apache-Spark?"></a>

We acknowledge the fact that cluster computing in general and Apache Spark in particular can be derouting at first sight for newcomers, and one often does not want to rewrite entirely a package.
We define 2 levels of _sparkfication_, with the first one being a minimal change of the original code for Spark to work, and the second one being a more aggressive restructuration to fully benefit from the Spark framework.

### Level 0: minimal intrusion <a name="Level-0--minimal-intrusion"></a>

At the level 0, we mostly focus on rewriting I/O to be compliant with Spark philosophy: input, output, and call to external data such as external DB queries or internal log/parameter files.
One should keep in mind that Spark is a distributed framework, so concepts such as absolute paths, or local data are not valid here.

In the end, out of ∼ 9000 lines of python codes in the original Spectractor code, ∼20 lines were modified or added!

### Level 1: code infection <a name="Level-1--code-infection"></a>

We could go beyond just wrapping up the code and use the full potential of Spark: functional programming, native data source connectors ([spark-fits](https://github.com/astrolabsoftware/spark-fits)), ... This has not been yet done here.

## How to use it? <a name="How-to-use-it?"></a>

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

In order for the -- exector distributed... zip branch spark ...

### Apache Spark cluster (with HDFS) <a name="Apache-Spark-cluster--with-HDFS-"></a>

We provide a launcher ([run_benchmarks_python_cluster.sh](https://github.com/astrolabsoftware/spark-lsst/blob/master/Spectractor/run_benchmarks_python_cluster.sh)) to use on a Spark cluster with HDFS for the file system. For simplicity we loop over days of observation, but one could as well process the entire data set at once.

### Cori@NERSC <a name="Cori@NERSC"></a>

We provide a launcher ([run_benchmarks_python_cori.sh](https://github.com/astrolabsoftware/spark-lsst/blob/master/Spectractor/run_benchmarks_python_cori.sh)) to use on Cori at NERSC, on a Lustre file system (default). Note that you would have to zip yourself the latest version of Spectractor prior to launch the job (see comment in the launcher).

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
