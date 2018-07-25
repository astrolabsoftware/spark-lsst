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
from spectractor import parameters
from spectractor.extractor.extractor import Spectractor
from spectractor.logbook import LogBook

from astroquery.exceptions import RemoteServiceError

from mpi4py import MPI

import os
import glob

if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("-i", "--input", dest="input", default=["tests/data/reduc_20170605_028.fits"],
                        help="Input fits file name. It can be a list separated by spaces, or it can use * as wildcard.")
    parser.add_argument("-d", "--debug", dest="debug", action="store_true",
                        help="Enter debug mode (more verbose and plots).", default=False)
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true",
                        help="Enter verbose (print more stuff).", default=False)
    parser.add_argument("-o", "--output_directory", dest="output_directory", default="outputs/",
                        help="Write results in given output directory (default: ./outputs/).")
    parser.add_argument("-c", "--csv", dest="csv", default="ctiofulllogbook_jun2017_v5.csv",
                        help="CSV logbook file. (default: ctiofulllogbook_jun2017_v5.csv).")
    args = parser.parse_args()

    parameters.VERBOSE = args.verbose
    if args.debug:
        parameters.DEBUG = True
        parameters.VERBOSE = True

    file_names = glob.glob(os.path.join(args.input, "*/*.fits"))

    logbook = LogBook(logbook=args.csv)

    rank = MPI.COMM_WORLD.rank
    size = MPI.COMM_WORLD.size

    if rank == 0:
        print("{} files to process".format(len(file_names)))
        print("{} processors used".format(size))

    for position in range(rank, len(file_names), size):
        file_name = file_names[position]
        opt = logbook.search_for_image(file_name.split('/')[-1])
        target = opt[0]
        xpos = opt[1]
        ypos = opt[2]
        if target is None or xpos is None or ypos is None:
            continue
        try:
            Spectractor(file_name, args.output_directory, [xpos, ypos], target)
        except ValueError:
            file_name = file_name + "_ValueError_BAD"
            print("[{}] {} failed".format(rank, file_name))
        except RemoteServiceError:
            file_name = file_name + "_RemoteServiceError_BAD"
            print("[{}] {} failed".format(rank, file_name))
        except IndexError:
            file_name = file_name + "_IndexError_BAD"
            print("[{}] {} failed".format(rank, file_name))
