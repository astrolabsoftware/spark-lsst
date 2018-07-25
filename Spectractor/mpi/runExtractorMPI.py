from spectractor import parameters
from spectractor.extractor.extractor import Spectractor
from spectractor.logbook import LogBook
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

    # opts = [[fn, logbook.search_for_image(fn.split('/')[-1])] for fn in file_names]

    rank = MPI.COMM_WORLD.rank
    size = MPI.COMM_WORLD.size

    if rank == 0:
        print("{} files to process".format(len(file_names)))
        print("{} processors used".format(size))

    for position in range(rank, len(file_names), size):
        file_name = file_names[position]
        opt = logbook.search_for_image(file_name.split('/')[-1])
        #opt = opts[position]
        #file_name = opt[0]
        target = opt[0]
        xpos = opt[1]
        ypos = opt[2]
        if target is None or xpos is None or ypos is None:
            continue
        try:
            Spectractor(file_name, args.output_directory, [xpos, ypos], target)
        except:
            print("Failed")
