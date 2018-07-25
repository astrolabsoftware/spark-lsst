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
from pyspark.sql import SparkSession
from pyspark import SparkContext
from astroquery.exceptions import RemoteServiceError

import os
import glob
from typing import List
try:
    os.mkdir("astropy")
except FileExistsError:
    pass

os.environ["XDG_CONFIG_HOME"] = "."
os.environ["XDG_CACHE_HOME"] = "."

import numpy as np
import pylab as pl

from spectractor import parameters
from spectractor.extractor.extractor import Spectractor
from spectractor.logbook import LogBook
from spectractor.extractor.spectroscopy import Spectrum

import argparse

def addargs(parser):
    """ Parse command line arguments for Sparktractor """

    ## Arguments
    parser.add_argument(
        '-datapath', dest='datapath',
        required=True,
        help='Path to a FITS file or a directory containing FITS files')

    parser.add_argument(
        '-outpath', dest='outpath',
        required=True,
        help='Folder to write the output spectra')

    parser.add_argument(
        '-logfile', dest='logfile',
        default="ctiofulllogbook_jun2017_v5.csv",
        help='CSV log file to filter out bad observations')

    parser.add_argument(
        '-filesystem', dest='filesystem',
        default="hdfs",
        help='hdfs or lustre - it has an impact on the way we look for files.')

    parser.add_argument(
        '-log_level', dest='log_level',
        default="ERROR",
        help='Level of log for Spark. Default is ERROR.')

    parser.add_argument(
        '--debug', dest='debug',
        default=False,
        action='store_true',
        help='Level of log for Spectractor. Default is False.')

def hglob(sc: SparkContext,
          datapath: str="hdfs://134.158.75.222:8020/user/julien.peloton") -> List[str]:
    """
    Perform a glob (= list files) on a HDFS folder.

    Parameters
    ----------
    sc : SparkContext
        The SparkContext for the session.
    datapath : String
        hdfs://IP:PORT/path/to/data/folder in the hadoop cluster.

    Returns
    ----------
    fns : List of String
        List with filenames (full path)
    """
    uri = sc._gateway.jvm.java.net.URI
    path = sc._gateway.jvm.org.apache.hadoop.fs.Path
    filesystem = sc._gateway.jvm.org.apache.hadoop.fs.FileSystem
    configuration = sc._gateway.jvm.org.apache.hadoop.conf.Configuration

    fs = filesystem.get(uri(datapath), configuration())
    status = fs.globStatus(path(datapath))

    fns = []
    for filestatus in status:
        fns.append(str(filestatus.getPath()))
    return fns

def search_for_image(logbook: LogBook, tag: str) -> (str, int, int):
    """
    Search for image according to a `tag`, and return
    info (target name, xposition, yposition).
    If one of the infos is None, return None.

    Parameters
    ----------
    tag : String
        The tag of the image (filename) as written in the logbook.

    Return
    ----------
    (target, xpos, ypos): (String, Int, Int) or None
        Return the info (name, xposition, yposition) or None if
        at least one of the infos is None.
    """
    target, xpos, ypos = logbook.search_for_image(tag)
    if target is None or xpos is None or ypos is None:
        return None
    else:
        return target, xpos, ypos


def run_spectractor(file_name: str, output_directory: str,
                    position: (int, int), target: str, data: bytes) -> str:
    """
    Run the main Spectrator methods. This includes: load of the data,
    power-spectrum computation, and the fit. The spectrum is dumped on
    the disk (won't work in a pure distributed environment).

    Parameters
    ----------
    file_name : String
        Name of the file to load (full path)
    output_directory : String
        Name of the output_directory when power-spectra will be written
    position : List of two Int
        Position of the target (xpos, ypos) as given by the logbook search.
    target : String
        Name of the target

    Returns
    ----------
    file_name: String
        The name of the processed file.
    """
    try:
        Spectractor(
            file_name, output_directory,
            position, target, databinary=data)
    except ValueError:
        file_name = file_name + "_ValueError_BAD"
    except RemoteServiceError:
        file_name = file_name + "_RemoteServiceError_BAD"
    except IndexError:
        file_name = file_name + "_IndexError_BAD"
    return file_name

def quiet_logs(sc: SparkContext, log_level: str = "ERROR") -> None:
    """
    Set the level of log in Spark.

    Parameters
    ----------
    sc : SparkContext
        The SparkContext for the session
    log_level : String [optional]
        Level of log wanted: INFO, WARN, ERROR, OFF, etc.

    """
    ## Get the logger
    logger = sc._jvm.org.apache.log4j

    ## Set the level
    level = getattr(logger.Level, log_level, "INFO")

    logger.LogManager.getLogger("org"). setLevel(level)
    logger.LogManager.getLogger("akka").setLevel(level)


if __name__ == "__main__":
    """
    Extract spectra from CTIO images in order to test
    the performance of dispersers dedicated to the LSST Auxiliary Telescope,
    and characterize the atmospheric transmission.
    """
    parser = argparse.ArgumentParser(
        description="""
        Extract spectra from CTIO images in order to test
        the performance of dispersers dedicated to the LSST Auxiliary Telescope
        and characterize the atmospheric transmission.
        """)
    addargs(parser)
    args = parser.parse_args(None)

    spark = SparkSession\
        .builder\
        .getOrCreate()

    ## Set logs to be quiet
    quiet_logs(spark.sparkContext, log_level=args.log_level)

    ## Verbosity
    if args.debug:
        parameters.VERBOSE = True
        parameters.DEBUG = True
    else:
        parameters.VERBOSE = False
        parameters.DEBUG = False

    ## Load CTIO image name list
    datapath = args.datapath
    if args.filesystem == 'hdfs':
        file_names = hglob(spark.sparkContext, datapath)
    elif args.filesystem == 'lustre':
        file_names = glob.glob(os.path.join(datapath, "*/*.fits"))

    print("found {} files on {}".format(len(file_names), args.filesystem))

    ## Name of the logbook containing info about images.
    csvfile = args.logfile
    logbook = LogBook(logbook=csvfile)

    paramdic = {
        fn: search_for_image(logbook, fn.split('/')[-1]) for fn in file_names}

    spark.sparkContext.broadcast(paramdic)

    if args.filesystem == 'lustre':
        datapath = os.path.join(datapath, "*/*.fits")
        rdd = spark.sparkContext.binaryFiles(datapath, len(paramdic))\
            .map(lambda x: [x[0].split(":")[1], paramdic[x[0].split(":")[1]], x[1]])\
            .filter(lambda x: x[1] is not None)\
            .map(lambda x: run_spectractor(x[0], "output", [x[1][1], x[1][2]], x[1][0], x[2]))\
            .collect()
    elif args.filesystem == 'hdfs':
        rdd = spark.sparkContext.binaryFiles(datapath, len(paramdic))\
            .map(lambda x: [x[0], paramdic[x[0]], x[1]])\
            .filter(lambda x: paramdic[x[0]] is not None)\
            .map(lambda x: run_spectractor(x[0], "output", [x[1][1], x[1][2]], x[1][0], x[2]))\
            .collect()

    ## Collect statistics
    good_files = [i for i in rdd if "_BAD" not in i]
    indexed_err = [i for i in rdd if "_Index" in i]
    value_err = [i for i in rdd if "_Value" in i]
    remote_err = [i for i in rdd if "_Remote" in i]
    print("{}/{} files processed".format(len(rdd), len(file_names)))
    print("{}/{} files processed".format(len(good_files), len(rdd)))
    print("{} index err".format(len(indexed_err)))
    print("{} value err".format(len(value_err)))
    print("{} remote err".format(len(remote_err)))

    # ## Load spectra from disk
    # spectra_list = glob.glob(os.path.join(root, "spark_test/output/*.fits"))
    #
    # ## Instantiate a spectrum
    # spectrum = Spectrum(spectra_list[0])
    #
    # ## Plot it
    # spectrum.plot_spectrum(xlim=None, fit=True)
    # pl.show()
