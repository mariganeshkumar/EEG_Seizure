#!/usr/bin/env python
#
# file: $NEDC_NFC/class/python/nedc_ann_tools/nedc_ann_tools.py
#                                                                              
# revision history: 
#  20200327 (TE): initial version
#                                                                              
# usage:                                                                       
#  import nedc_ann_tools as nat
#                                                                              
# This class contains a collection of methods that provide 
# the infrastructure for processing annotation-related data.
#------------------------------------------------------------------------------

# import reqired system modules
#
import os
import sys
from collections import OrderedDict

# import required NEDC modules
#
import sys_tools.nedc_file_tools as nft

#------------------------------------------------------------------------------
#                                                                              
# global variables are listed here                                             
#                                                                              
#------------------------------------------------------------------------------

# define ref/hyp event constants
#
DEF_CLASS = "seiz"
BCKG_CLASS = "bckg"
FIRST_EVENT_INDEX = 0
LAST_EVENT_INDEX = -1
START_TIME_INDEX = 0
STOP_TIME_INDEX = 1

#------------------------------------------------------------------------------
#
# functions are listed here:
#
#------------------------------------------------------------------------------

# function: sort_dict
#
# arguments:
#  odict: dictionary mapping of files and events
#
# return: updated dictionary
#
# This function sorts the events in all files by the event start time
#
def sort_dict(odict):

    # for each file
    #
    for key in odict:

        # sort by the start time of the event
        #
        odict[key] = sorted(odict[key], key=lambda event:event[START_TIME_INDEX])

    # exit gracefully
    #
    return odict
#
# end of function


# function: parse_ref
#
# arguments:
#  f_cont: the file content tokenized by newline
#
# return: event dictionary and duration dictionary
#
# This function parses through the ref file and creates
# a dictionary mapping between files and their events
# i.e {'00000258_s002_t000': [[0.0, 10.0, 'bckg', 1.00]..] ... }
# it also returns a duration dictionary with a key/value pair of
# file/duration
#
def parse_ref(f_cont):

    # instatiate the event dictionary
    #
    odict = {}

    # for each line in the file
    #
    for line in f_cont:

        # split the line by whitespace
        #
        tokenized = line.split()

        # ensure we have all 5 entries
        #
        if len(tokenized) != 5:
            continue

        # file name, used as key
        #
        fname = tokenized[0]

        # get the start, stop time as well as
        # event label and confidence
        #
        start = float(tokenized[1])
        stop = float(tokenized[2])
        lbl = tokenized[3]
        conf = float(tokenized[4])

        # if this is a new file
        #
        if fname not in odict:

            # the value is a new nested list of events
            #
            odict[fname] = [[start, stop, OrderedDict({lbl:conf})]]

        # if this file is already in the dictionary
        #
        else:

            # add the event to the list
            #
            odict[fname].append([start, stop, OrderedDict({lbl:conf})])

    # sort the dictionary
    #
    odict = sort_dict(odict)

    # create a mapping of fname:duration; duration is simply
    # the stop time of the last event
    #
    dur_dict = {fname: odict[fname][LAST_EVENT_INDEX][STOP_TIME_INDEX] for fname in odict}

    # exit gracefully
    #
    return odict, dur_dict
#
# end of function


# function: fill_gap
#
# arguments:
#  odict: dictionary mapping of files and events
#  duration_dict: dictionary mapping of files and duration
#
# return: updated dictionary
#
# This function ensures that all events for the duration of
# the hyp files are accounted for
#
def fill_gap(odict, duration_dict):

    # for each hyp file
    #
    for fname in odict:

        # get the start and stop time of the file
        #
        f_start = 0.0
        f_stop = duration_dict[fname]

        # get the start time of the first event and the
        # stop time of the last event
        #
        first_event_start = odict[fname][FIRST_EVENT_INDEX][START_TIME_INDEX]
        last_event_stop = odict[fname][LAST_EVENT_INDEX][STOP_TIME_INDEX]

        # sanity check
        #
        if(first_event_start < f_start):
            raise ValueError("[%s]: '%s' event cannot start before time 0.0" \
                             % (sys.argv[0], fname))
        if(last_event_stop > f_stop):
            raise ValueError("[%s]: '%s' event cannot stop after time %f" \
                             % (sys.argv[0], fname, last_event_stop))
        
        # all events not accounted for will be background
        #
        bckg_event = OrderedDict({BCKG_CLASS:1.0})

        # if the first event didn't start at time 0.0
        #
        if first_event_start != f_start:

            # insert a bckg event from time 0 to the start of
            # the first event
            #
            odict[fname].insert(0, [f_start, first_event_start, bckg_event])

        # if the last event didn't stop at the end of the file
        #
        if last_event_stop != f_stop:

            # insert a bckg event from the stop time of the
            # last event to the end of the file
            #
            odict[fname].append([last_event_stop, f_stop, bckg_event])

        # keep track of the previous event stop time
        # initially, this is the stop time of the first event
        #
        prev_event_stop = odict[fname][FIRST_EVENT_INDEX][STOP_TIME_INDEX]

        # skip the first event
        #
        index = 1

        # while there are events to process
        #
        while index < len(odict[fname]):

            # get the current event
            #
            event = odict[fname][index]

            # get the start/stop time of the current event
            #
            curr_event_start = event[START_TIME_INDEX]
            curr_event_stop = event[STOP_TIME_INDEX]

            # if the stop time of the previous event is not
            # equal to the start time of the current event
            #
            if prev_event_stop != curr_event_start:

                # insert a bckg event in between the two events
                #
                odict[fname].insert(index, [prev_event_stop, curr_event_start, bckg_event])

                # skip the next event
                #
                index += 1

            # update the stop time of the previous event
            #
            prev_event_stop = curr_event_stop

            # increment the index
            #
            index += 1

    # for each fname in the duration dictionary
    #
    for key in duration_dict:

        # if there is a file in the duration dictionary
        # that was not mentioned in the hyp file
        #
        if key not in odict:

            # add the file and set the entire duration as bckg
            #
            odict[key] = [[0.0, duration_dict[key], OrderedDict({BCKG_CLASS:1.0})]]

    # exit gracefully
    #
    return odict
#
# end of function


# function: parse_hyp
#
# arguments:
#  f_cont: the file content of the hyp file
#  duration_dict: dictionary mapping of files and duration
#
# return: updated dictionary
#
# This function sorts through the hyp file and creates 
# a dictionary mapping of file name and events
#
def parse_hyp(f_cont, duration_dict):

    # instantiate the event dictionary
    #
    odict = {}

    # for each line in the file
    #
    for line in f_cont:

        # tokenize the line by whitespace
        #
        tokenized = line.split()

        # if there are not four entries...
        #
        if len(tokenized) != 4:
            continue

        # grab the file name
        #
        fname = tokenized[0]

        # grab the start, stop, and confidence of event
        #
        start = float(tokenized[1])
        stop = float(tokenized[2])
        conf = float(tokenized[3])

        # if this file was not in the dictionary
        #
        if fname not in odict:

            # the value is a nested list of events
            #
            odict[fname] = [[start, stop, OrderedDict({DEF_CLASS:conf})]]

        # if the file was already in the dictionary
        #
        else:

            # add the event to the list
            #
            odict[fname].append([start, stop, OrderedDict({DEF_CLASS:conf})])

    # sort the dictionary
    #
    odict = sort_dict(odict)

    # exit gracefully
    #
    return fill_gap(odict, duration_dict)
#
# end of function


# function: parse_file
#
# arguments:
#  fname: the name of the annoation file
#  duration_dict: dictionary mapping of files and duration
#
# return: event dictionary 
#
# This function returns an event dictionary and duration 
# dictionary for ref files or event dictionaries for hyp files
#
def parse_file(fname, duration_dict = None):

    # read the file
    #
    with open(fname, 'r') as fp:
        f_cont = fp.read().splitlines()

    # if no duration dict was provided, treat as ref
    #
    if duration_dict is None:

        # return event dictionary and duration dictionary
        #
        return parse_ref(f_cont)

    # return event dictionary
    #
    return parse_hyp(f_cont, duration_dict)
#
# end of function

#                                                                              
# end of file 
