# spark-lsst

_Collection of examples combining Apache Spark and LSST codes._

## Why would you use Apache Spark in the context of LSST? 

Although [Apache Spark](http://spark.apache.org/) is not primarily meant to bring further speed-up on the computation itself, it is very efficient to deal with and manage a large volume of data. It often provides better performances than other tools for e.g. embarrassingly parallel job by optimizing data distribution (load balancing) and minimizing I/O latency.

One should also mention that one of the strength of Apache Spark resides in its simplicity. It’s impressive really how seamless Spark works for dealing with pipeline and job management. Those are done internally without user actions and are often more efficiently than what we could do manually by scheduling tasks with MPI for example.

## What typically needs to be modified to use Apache Spark?

We acknowledge the fact that cluster computing (HTC) in general and Apache Spark in particular can be derouting at first sight for newcomers from HPC, and one often does not want to rewrite entirely a package.
We define 2 levels of _sparkfication_, with the first one being a minimal change of the original code for Spark to work, and the second one being a more aggressive restructuration to fully benefit from the Spark framework.

### Level 0: minimal intrusion

At the level 0, we mostly focus on rewriting I/O to be compliant with Spark philosophy: input, output, and call to external data such as external DB queries or internal log/parameter files.
One should keep in mind that Spark is a distributed framework, so concepts such as absolute paths, or local data are often not valid here.

### Level 1: code infection

We go beyond just wrapping the code and use the full potential of Spark: functional programming, native data source connectors (e.g. [spark-fits](https://github.com/astrolabsoftware/spark-fits)), ...

## Available LSST package using Spark

- [LSSTDESC/Spectractor](https://github.com/LSSTDESC/Spectractor)