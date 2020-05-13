#!/usr/bin/env python
#
# file: $(NEDC_NFC)/util/python/nedc_eval_eeg/nedc_eval_eeg.py
#
# revision history:
#  20170730 (JP): moved parameter file constants out of this driver
#  20170728 (JP): added error checking for duration
#  20170716 (JP): upgraded to using the new annotation tools.
#  20170527 (JP): added epoch-based scoring
#  20150520 (SZ): modularized the code
#  20170510 (VS): encapsulated the three scoring metrics 
#  20161230 (SL): revision for standards
#  20150619 (SZ): initial version
# 
# usage:
#   nedc_eval_eeg -odir output -parameters parameters ref.list hyp.list
#
# options:
#  -parameters: a parameter file 
#  -odir: the output directory [$PWD/output]
#  -help: display this help message
#
# arguments:
#  ref.list: a list of reference annotations
#  hyp.list: a list of hypothesis 
#
# This script implements several standard scoring algorithms:
#  (1) DP Align: a dynamic programming-based alignment
#  (2) Epoch-based: measures the time-aligned similarity of two annotations;
#  (3) Overlap: implements a measure popular in bioengineering
#  (4) NEDC Time-Aligned Event Scoring: compares time-aligned events.
#------------------------------------------------------------------------------

# import system modules
#
import os
import sys
import time
from collections import OrderedDict

# import NEDC support modules
#
import sys_tools.nedc_cmdl_parser as ncp
import sys_tools.nedc_file_tools as nft
import sys_tools.nedc_ann_tools as nat

# import NEDC scoring modules
#
import eval_tools.nedc_eval_dpalign as ndpalign
import eval_tools.nedc_eval_epoch as nepoch
import eval_tools.nedc_eval_ovlp as novlp
import eval_tools.nedc_eval_taes as ntaes

#------------------------------------------------------------------------------
#
# global variables are listed here
#
#------------------------------------------------------------------------------

# define script location
#
SCRIPT_LOC = os.path.dirname(os.path.realpath(__file__))

# define the help file and usage message
#
HELP_FILE = SCRIPT_LOC + "/help/nedc_eval_eeg.help"
USAGE_FILE = SCRIPT_LOC + "/help/nedc_eval_eeg.usage"

# define default values for arguments
#
DEF_ODIR = os.environ["PWD"] + "/output"

# define the required number of arguments
#
NUM_ARGS = 2

# define the names of the output files
#
NEDC_SUMMARY_FILE = "summary.txt"
NEDC_DPALIGN_FILE = "summary_dpalign.txt"
NEDC_EPOCH_FILE = "summary_epoch.txt"
NEDC_OVLP_FILE = "summary_ovlp.txt"
NEDC_TAES_FILE = "summary_taes.txt"

# define formatting constants
#
NEDC_EVAL_SEP = "=" * 78
NEDC_NEW_LINE = "\n"
NEDC_VERSION = "NEDC Eval EEG (v3.3.1)"

# define class definitions
#
SEIZ = "SEIZ"
BCKG = "BCKG"
CLASSES = [SEIZ, BCKG]

#------------------------------------------------------------------------------
#
# the main program starts here
#
#------------------------------------------------------------------------------
# method: main
#
# arguments: none
#
# return: none
#
# This function is the main program.
#
def main(argv):

    # declare local variables
    #
    status = True

    # declare default values for command line arguments
    #
    odir = DEF_ODIR

    # create a command line parser
    #
    parser = ncp.CommandLineParser(USAGE_FILE, HELP_FILE)

    # define the command line arguments
    #
    parser.add_argument("args",  type = str, nargs='*')
    parser.add_argument("-odir", type = str)
    parser.add_argument("-help", action="help")
    
    # parse the command line
    #
    args = parser.parse_args()

    # check if the proper number of lists has been provided
    #
    if len(args.args) != NUM_ARGS:
        parser.print_usage()
        exit(-1)

    # set option and argument values
    #
    # set the output directory
    #
    if args.odir is not None:
        odir = args.odir

    # set the input lists
    #
    fname_ref = args.args[0]
    fname_hyp = args.args[1]

    # parse the ref and hyp file lists
    #
    reflist, dur_dict = nat.parse_file(fname_ref)
    hyplist = nat.parse_file(fname_hyp, dur_dict)

    # check for mismatched file lists:
    #  note that we do this here so it is done only once, rather than
    #  in each scoring method
    #
    if (reflist == None) or (hyplist == None):
        print("%s (%s: %s): error loading filelists (ref: %s) and (hyp: %s)" \
            % (sys.argv[0], __name__, "main", fname_ref, fname_hyp))
        exit (-1)
    elif len(reflist) != len(hyplist):
        print("%s (%s: %s): (ref: %d) and (hyp: %d) have different lengths" \
            % (sys.argv[0], __name__, "main", len(reflist), len(hyplist)))
        exit (-1)

    # load the scoring map
    #
    tmpmap = OrderedDict()
    for class_a in CLASSES:
        tmpmap[class_a] = class_a

    # convert the map
    #
    scmap = nft.generate_map(tmpmap)
    if (scmap == None):
        print("%s (%s: %s): error converting the map" % \
            (sys.argv[0], __name__, "main"))
        print(tmpmap)
        exit (-1)

    # create the output directory and the output summary file
    #               
    print(" ... creating the output directory ...")
    if nft.make_dir(odir) == False:
        print("%s (%s: %s): error creating output directory (%s)" \
            % (sys.argv[0], __name__, "main", odir))
        exit (-1)

    fname = nft.make_fname(odir, NEDC_SUMMARY_FILE)
    fp = nft.make_fp(fname)

    # print the header of the summary file showing the relevant information
    #
    fp.write("%s\n%s\n\n" % (NEDC_EVAL_SEP, NEDC_VERSION))
    fp.write(" File: %s\n" % fname) 
    fp.write(" Date: %s\n\n" % time.strftime("%c"))
    fp.write(" Data:\n")
    fp.write("  Ref: %s\n" % fname_ref)
    fp.write("  Hyp: %s\n\n" % fname_hyp)

    # execute dp alignment scoring
    #
    print(" ... executing NEDC DP Alignment scoring ...")
    fp.write("%s\n%s\n\n" % \
             (NEDC_EVAL_SEP, \
              ("NEDC DP Alignment Scoring Summary (v2.0.0):").upper()))
    fname = nft.make_fname(odir, NEDC_DPALIGN_FILE)
    status = ndpalign.run(reflist, hyplist, scmap, odir, fname, fp)
    if status == False:
        print("%s (%s: %s): error in DP Alignment scoring" % \
            (sys.argv[0], __name__, "main"))
        exit (-1)
    
    # execute NEDC epoch-based scoring
    #
    print(" ... executing NEDC Epoch scoring ...")
    fp.write("%s\n%s\n\n" % (NEDC_EVAL_SEP, \
                             "NEDC Epoch Scoring Summary (v2.0.0):"))
    fname = nft.make_fname(odir, NEDC_EPOCH_FILE)
    status = nepoch.run(reflist, hyplist, scmap, odir, fname, fp)
    if status == False:
        print("%s (%s: %s): error in EPOCH scoring" % \
            (sys.argv[0], __name__, "main"))
        exit (-1)
    
    # execute overlap scoring
    #
    print(" ... executing NEDC Overlap scoring ...")
    fp.write("%s\n%s\n\n" % (NEDC_EVAL_SEP, \
                             "NEDC Overlap Scoring Summary (v2.0.0):"))
    fname = nft.make_fname(odir, NEDC_OVLP_FILE)
    status = novlp.run(reflist, hyplist, scmap, odir, fname, fp)
    if status == False:
        print("%s (%s: %s): error in OVERLAP scoring" % \
            (sys.argv[0], __name__, "main"))
        exit (-1)
        
    # execute time-aligned event scoring
    #
    print(" ... executing NEDC Time-Aligned Event scoring ...")
    fp.write("%s\n%s\n\n" % (NEDC_EVAL_SEP, \
                             "NEDC TAES Scoring Summary (v2.0.0):"))
    fname = nft.make_fname(odir, NEDC_TAES_FILE)
    status = ntaes.run(reflist, hyplist, scmap, odir, fname, fp)
    if status == False:
        print("%s (%s: %s): error in TIME-ALIGNED Event scoring" % \
            (sys.argv[0], __name__, "main"))
        exit (-1)

    # print the final message to the summary file, close it and exit
    #
    print(" ... done ...")
    fp.write("%s\nNEDC EEG Eval Successfully Completed on %s\n%s\n" \
             % (NEDC_EVAL_SEP, time.strftime("%c"), NEDC_EVAL_SEP))
    
    # close the output file
    #
    fp.close()

    # end of main
    #
    exit(1)
    
#
# end of main

#
# end of method

# begin gracefully
#
if __name__ == "__main__":
    main(sys.argv[0:])

#                                                                              
# end of file
