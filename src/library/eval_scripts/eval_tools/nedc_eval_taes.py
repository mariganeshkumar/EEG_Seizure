#!/usr/bin/env python

# file: $NEDC_NFC/class/python/nedc_eval_tools/nedc_eval_taes.py
#
# revision history:
#  20180218 (VS): bug fixes, updated the metric according definition
#  20170815 (JP): added another metric: prevalence
#  20170812 (JP): changed the divide by zero checks
#  20170716 (JP): upgraded to using the new annotation tools
#  20170710 (JP): refactored code
#  20170702 (JP): added summary scoring; revamped the derived metrics
#  20170627 (VS): second optimized version
#  20170625 (VS): initial version

#
# usage:
#  import nedc_eval_taes as ntaes
#
# This file implements NEDC's Time-Aligned Event scoring algorithm.
#------------------------------------------------------------------------------

# import required system modules
#
import os
import sys
from collections import OrderedDict

# import required NEDC modules
#
import sys_tools.nedc_file_tools as nft
import sys_tools.nedc_ann_tools as nat
import sys_tools.nedc_text_tools as ntt
import sys_tools.nedc_display_tools as ndt

#------------------------------------------------------------------------------
#
# define important constants
#
#------------------------------------------------------------------------------

# define paramter file constants
#
NEDC_TAES = "NEDC_TAES"

#------------------------------------------------------------------------------
#                                                                              
# the main interface method
#                                                                              
#------------------------------------------------------------------------------

# method: run
#
# arguments:
#  reflist: the reference file list
#  hyplist: the hypothesis file list
#  map: a mapping used to collapse classes during scoring
#  odir: the output directory
#  rfile: the results file (written in odir)
#  fp: a pointer to the output summary file
#
# return: a logical value indicating status
#
# This method runs the NEDC time-aligned scoring algorithm by:
#  (1) loading the annotations
#  (2) scoring them
#  (3) displaying the results
#
def run(reflist_a, hyplist_a, map_a, odir_a, rfile_a, fp_a):

    # define local variables
    #
    status = True
    ntaes = NedcTAES()

    # load the reference and hyp file lists into memory
    #
    num_files_ref = len(reflist_a)
    num_files_hyp = len(hyplist_a)
    
    if num_files_ref < 1 or num_files_hyp < 1 or \
       num_files_ref != num_files_hyp:
        print("%s (%s: %s): file list error (%s %s)" % \
            (sys.argv[0], __name__, "run", reflist_a, hyplist_a))
        return False

    # run time-aligned scoring
    #
    status = ntaes.init_score(map_a)
    status = ntaes.score(reflist_a, hyplist_a, map_a, rfile_a)
    if status == False:
        print("%s (%s: %s): error during scoring" % \
            (sys.argv[0], __name__, "run"))
        return False

    # compute performance
    #
    cnf = ntaes.compute_performance()
    if status == None:
        print("%s (%s: %s): error computing performance" % \
            (sys.argv[0], __name__, "run"))
        return False

    # collect information for scoring and display
    #
    status = ntaes.display_results(fp_a)
    if status == False:
        print("%s (%s: %s): error displaying results" % \
            (sys.argv[0], __name__, "run"))
        return False

    # exit gracefully
    #
    return status
#
# end of function

#------------------------------------------------------------------------------
#
# classes are listed here
#
#------------------------------------------------------------------------------

# class: NedcTAES
#
# This class contains methods that execute the time-aligned event-based 
# scoring algorithm. This approach computes fractional counts of matches,
# providing more resolution than the overlap method.
#
class NedcTAES():
    
    # method: constructor
    # 
    # arguments: none
    #
    # return: none
    #
    def __init__(self):

        # declare a variable to hold a permuted map
        #
        self.pmap_d = {}

        # declare a duration parameter used to calculate the false alarm rate:
        #  we need to know the total duration of the data in secs
        #
        self.total_dur_d = float(0)

        # declare parameters to track errors:
        #  all algorithms should track the following per label:
        #   substitutions, deletions, insertions, hits, misses
        #   and false alarms.
        #
        self.tp_d = {}
        self.tn_d = {}
        self.fp_d = {}
        self.fn_d = {}

        self.tgt_d = {}
        self.hit_d = {}
        self.mis_d = {}
        self.fal_d = {}
        self.ins_d = {}
        self.del_d = {}

        # additional derived data:
        #  we use class data to store a number of statistical measures
        #
        self.tpr_d = {}
        self.tnr_d = {}
        self.ppv_d = {}
        self.npv_d = {}
        self.fnr_d = {}
        self.fpr_d = {}
        self.fdr_d = {}
        self.for_d = {}
        self.acc_d = {}
        self.msr_d = {}
        self.prv_d = {}
        self.f1s_d = {}
        self.flr_d = {}

        # declare parameters to compute summaries
        #
        self.sum_tp_d = int(0)
        self.sum_tn_d = int(0)
        self.sum_fp_d = int(0)
        self.sum_fn_d = int(0)

        self.sum_tgt_d = int(0)
        self.sum_hit_d = int(0)
        self.sum_mis_d = int(0)
        self.sum_fal_d = int(0)
        self.sum_ins_d = int(0)
        self.sum_del_d = int(0)

        # additional derived data:
        #  we use class data to store a number of statistical measures
        #
        self.sum_tpr_d = float(0)
        self.sum_tnr_d = float(0)
        self.sum_ppv_d = float(0)
        self.sum_npv_d = float(0)
        self.sum_fnr_d = float(0)
        self.sum_fpr_d = float(0)
        self.sum_fdr_d = float(0)
        self.sum_for_d = float(0)
        self.sum_acc_d = float(0)
        self.sum_msr_d = float(0)
        self.sum_prv_d = float(0)
        self.sum_f1s_d = float(0)
        self.sum_flr_d = float(0)

        # declare parameters to hold per file output
        #
        self.rfile_d = None

        # exit gracefully
        #
        
    # method: init_score
    #
    # arguments:
    #  map: a scoring map
    #
    # return: a logical value indicating status
    #
    # This method initializes parameters used to track errors.
    # We use ordered dictionaries that are initialized in the order
    # labels appear in the scoring map.
    #
    def init_score(self, map_a):
        
        # initialize global counters
        #
        self.total_dur_d = float(0)

        # initialiaze parameters to track errors:
        #  these are declared as ordered dictionaries organized
        #  in the order of the scoring map
        #
        self.tp_d = OrderedDict()
        self.tn_d = OrderedDict()
        self.fp_d = OrderedDict()
        self.fn_d = OrderedDict()

        self.tgt_d = OrderedDict()
        self.hit_d = OrderedDict()
        self.mis_d = OrderedDict()
        self.fal_d = OrderedDict()
        self.ins_d = OrderedDict()
        self.del_d = OrderedDict()

        self.tpr_d = OrderedDict()
        self.tnr_d = OrderedDict()
        self.ppv_d = OrderedDict()
        self.npv_d = OrderedDict()
        self.fnr_d = OrderedDict()
        self.fpr_d = OrderedDict()
        self.fdr_d = OrderedDict()
        self.for_d = OrderedDict()
        self.acc_d = OrderedDict()
        self.msr_d = OrderedDict()
        self.prv_d = OrderedDict()
        self.f1s_d = OrderedDict()
        self.flr_d = OrderedDict()

        # declare parameters to compute summaries
        #
        self.sum_tp_d = int(0)
        self.sum_tn_d = int(0)
        self.sum_fp_d = int(0)
        self.sum_fn_d = int(0)

        self.sum_tgt_d = int(0)
        self.sum_hit_d = int(0)
        self.sum_mis_d = int(0)
        self.sum_fal_d = int(0)
        self.sum_ins_d = int(0)
        self.sum_del_d = int(0)

        self.sum_tpr_d = float(0)
        self.sum_tnr_d = float(0)
        self.sum_ppv_d = float(0)
        self.sum_npv_d = float(0)
        self.sum_fnr_d = float(0)
        self.sum_fpr_d = float(0)
        self.sum_fdr_d = float(0)
        self.sum_for_d = float(0)
        self.sum_msr_d = float(0)
        self.sum_f1s_d = float(0)
        self.sum_flr_d = float(0)

        # establish the order of these dictionaries in terms of
        # the scoring map.
        #
        for key in map_a:
            self.tp_d[key] = int(0)
            self.tn_d[key] = int(0)
            self.fp_d[key] = int(0)
            self.fn_d[key] = int(0)

            self.tgt_d[key] = int(0)
            self.hit_d[key] = int(0)
            self.mis_d[key] = int(0)
            self.fal_d[key] = int(0)
            self.ins_d[key] = int(0)
            self.del_d[key] = int(0)

            self.tpr_d[key] = float(0)
            self.tnr_d[key] = float(0)
            self.ppv_d[key] = float(0)
            self.npv_d[key] = float(0)
            self.fnr_d[key] = float(0)
            self.fpr_d[key] = float(0)
            self.fdr_d[key] = float(0)
            self.for_d[key] = float(0)
            self.acc_d[key] = float(0)
            self.msr_d[key] = float(0)
            self.prv_d[key] = float(0)
            self.f1s_d[key] = float(0)
            self.flr_d[key] = float(0)

        # permute the map: we need this in various places
        #
        self.pmap_d = nft.permute_map(map_a)

        # exit gracefully
        # 
        return True
    #
    # end of method

    # method: score
    #
    # arguments:
    #  files_ref: a reference file list
    #  files_hyp: a hypothesis file list
    #  map: a scoring map
    #  rfile: a file that contains per file scoring results
    #
    # return: a logical value indicating status
    #
    # This method computes a confusion matrix.
    #
    def score(self, files_ref_a, files_hyp_a, map_a, rfile_a):
        
        # declare local variables
        #
        status = True

        # create the results file
        #
        self.rfile_d = nft.make_fp(rfile_a)

        # for each fname
        #
        for i, fname in enumerate(files_ref_a):

            # get the ref events
            #
            events_ref = files_ref_a.get(fname, None)
            if events_ref == None:
                print("%s (%s: %s): error getting annotations (%s)" % \
                    (sys.argv[0], __name__, "score", files_ref_a[i]))
                return False

            # get the hyp events
            #
            events_hyp = files_hyp_a.get(fname, None)
            if events_hyp == None:
                print("%s (%s: %s): error getting annotations (%s)" % \
                    (sys.argv[0], __name__, "score", files_hyp_a[i]))
                return False

            # pudate the total duration
            #
            self.total_dur_d += events_ref[-1][1]

            # map the annotations before scoring:
            #  only extract the first label and convert to a pure list
            #
            ann_ref = []
            for event in events_ref:
                key = next(iter(event[2]))
                ann_ref.append([event[0], event[1], \
                                self.pmap_d[key], event[2][key]])
                
            ann_hyp = []
            for event in events_hyp:
                key = next(iter(event[2]))
                ann_hyp.append([event[0], event[1], \
                                self.pmap_d[key], event[2][key]])

            # add this to the confusion matrix
            #
            refo, hypo, hit, mis, fal = self.compute(ann_ref, ann_hyp)
            if refo == None:
                print("%s (%s: %s): error computing confusion matrix (%s %s)" % \
                    (sys.argv[0], __name__, "score", \
                     files_ref_a[i], files_hyp_a[i]))
                return False

            # output the files to the per file results file
            #
            self.rfile_d.write("%5d: %s.tse\n" % (i, fname))
            self.rfile_d.write("%5s  %s.hyp\n" % ("", fname))
            self.rfile_d.write("  Ref: %s\n" % ' '.join(refo))
            self.rfile_d.write("  Hyp: %s\n" % ' '.join(hypo))
            self.rfile_d.write("%6s (Hits: %.4f  Miss: %.4f  False Alarms: %.4f  Total: %.4f)\n" \
                               % ("", hit, mis, fal, \
                                  mis + fal))
            self.rfile_d.write("\n")

        # close the file
        #
        self.rfile_d.close()

        # exit gracefully
        # 
        return True
    #
    # end of method

    # method: compute
    #
    # arguments:
    #  ref: reference annotation
    #  hyp: hypothesis annotation
    #  
    # return:
    #  refo: the output aligned ref string
    #  hypo: the output aligned hyp string
    #  hit: the number of hits
    #  mis: the number of misses
    #  fal: the number of false alarms
    #
    # this method loops through reference and hypothesis annotations to 
    # collect partial and absolute hit, miss and false alarms.
    #
    def compute(self, ref_a, hyp_a):

        # check to make sure the annotations match:
        #  since these are floating point values for times, we
        #  do a simple sanity check to make sure the end times
        #  are close (within 1 microsecond)
        #
        if round(ref_a[-1][1], 3) != round(hyp_a[-1][1], 3):
            return False

        # prime the output strings with null characters
        #
        refo = []
        hypo = []

        # initialize hmf variables to collect absolute and partial values
        #
        hit = float(0)
        mis = float(0)
        fal = float(0)

        # generate flags for hypothesis and reference values to indicate
        # whether an event is used once or not (for detection)
        #
        hflags = []
        rflags = []

        for i in range(len(hyp_a)):
            hflags.append(True)
        for i in range(len(ref_a)):
            rflags.append(True)

        # loop through ref events
        #
        for i in range(len(ref_a)):
            self.tgt_d[ref_a[i][2]] += 1
            tgt_event = ref_a[i][2]
            refo.append(ref_a[i][2])
            
            # collect hyp events which are in some overlap with ref event
            #
            labels, starts, stops \
                = self.get_events(ref_a[i][0], ref_a[i][1], hyp_a, hflags)

            # one event at a time, don't bother if ref/hyp labels don't overlap
            #
            if ref_a[i][2] in labels and rflags[i]:

                # loop through all hyp events and calculate partial HMF
                #
                for j in range(len(hyp_a)):

                    # compare hyp and ref event labels and hyp flags status;
                    #
                    if hyp_a[j][2] == ref_a[i][2] and hflags[j]:
                    
                        p_hit, p_miss, p_fa \
                            = self.compute_partial(ref_a, hyp_a, i, j, \
                                                   rflags, hflags, tgt_event)

                        # updat the HMF confusion matrix
                        #
                        hit += p_hit
                        mis += p_miss
                        fal += p_fa

                        self.hit_d[ref_a[i][2]] += p_hit
                        self.mis_d[ref_a[i][2]] += p_miss
                        self.fal_d[ref_a[i][2]] += p_fa

                    # update the hyp event index
                    #
                    j += 1
            
            # updated the ref event index
            #
            i += 1

        # update the absolute misses and false alarms from flags
        #
        if True in (rflags + hflags):
            mis += rflags.count(True)
            fal += hflags.count(True)
            self.update_abs_mf(ref_a, hyp_a, rflags, hflags)
        
        # exit gracefully
        #
        return (refo, hypo, hit, mis, fal)

    # method: update_abs_mf
    #
    # arguments:
    #  ref_a: reference label information as a list
    #  hyp_a: hypothesis label information as a list
    #  rflags_a: reference flags indicating the processed labels
    #  hflags_a: hypothesis flags indicating the processed labels
    #
    # return:
    #  None
    #
    # This method updates the miss and fa class-variables by 
    # collecting the ignored events which are not in partial
    # overlap with same labels. (i.e. Absolute misses)
    #
    def update_abs_mf(self, ref_a, hyp_a, rflags_a, hflags_a):
            
        # loop through ref and hyp lists to update class variables
        # 
        for i in range(len(ref_a)):
            if rflags_a[i]:
                self.mis_d[ref_a[i][2]] += 1

        for i in range(len(hyp_a)):
            if hflags_a[i]:
                self.fal_d[hyp_a[i][2]] += 1

        # exit gracefully
        #
    #
    # end of method

    # method: ovlp_ref_seqs
    #
    # arguments:
    #  ref_a: reference label information as a list
    #  hyp_a: hypothesis label information as a list
    #  rind_a: ref index where ovlp is detected
    #  hind_a: hyp index where ovlp is detected
    #  refflag_a: reference flags indicating the processed labels
    #  hypflag_a: hypothesis flags indicating the processed labels
    #  tgt_a: label name for which ovlp is detected
    #
    # return:
    #  p_hit: detected partial hits
    #  p_miss: detected partial miss
    #  p_fa: detected partial FAs
    #
    # This method calculates the HMF for overlapped events where
    # hypothesis event stop time exceeds the reference event
    # stop time.
    #
    def ovlp_ref_seqs(self, ref_a, hyp_a, rind_a, hind_a,
                          refflag_a, hypflag_a, tgt_a):
        
        # define variables
        #
        p_miss = float(0)

        # calculate the parameters for the current event
        #
        p_hit, p_fa = self.calc_hf(ref_a[rind_a], hyp_a[hind_a])
        p_miss += float(1) - p_hit
        
        # update flags for already detected events
        #
        hypflag_a[hind_a] = False
        refflag_a[rind_a] = False

        # update the index since there could be multiple ref events
        # overlapped with hyp event
        #
        #  <-->    <-->  <-->
        # <--------------------->
        #
        rind_a += 1
        
        # look for more ref events overlapping with hyp event
        #
        for i in range(rind_a, len(ref_a)):
            
            # update misses according to the TAES score definition
            #
            if ref_a[i][2] == hyp_a[hind_a][2] and \
               self.anyovlp(ref_a[i], hyp_a[hind_a]):

                # update the flags for processed events
                #
                refflag_a[i] = False
                p_miss += 1

            # move to next event index
            #
            i += 1

        # exit gracefully
        #
        return p_hit, p_miss, p_fa
    #
    # end of method
    
    # method: ovlp_hyp_seqs
    #
    # arguments:
    #  ref_a: reference label information as a list
    #  hyp_a: hypothesis label information as a list
    #  rind_a: ref index where ovlp is detected
    #  hind_a: hyp index where ovlp is detected
    #  refflag_a: reference flags indicating the processed labels
    #  hypflag_a: hypothesis flags indicating the processed labels
    #  tgt_a: label name for which ovlp is detected
    #
    # return:
    #  p_hit: detected partial hits
    #  p_miss: detected partial miss
    #  p_fa: detected partial FAs
    #
    # This method calculates the HMF for overlapped events where
    # reference event stop time exceeds the hypothesis event
    # stop time.
    #
    def ovlp_hyp_seqs(self, ref_a, hyp_a, rind_a, hind_a,
                          refflag_a, hypflag_a, tgt_a):
        
        # define variables
        #
        p_miss = float(0)

        # calculate the parameters for the current event
        #
        p_hit, p_fa = self.calc_hf(ref_a[rind_a], hyp_a[hind_a])
        p_miss += float(1) - p_hit        

        # update flags for already detected events
        #
        refflag_a[rind_a] = False
        hypflag_a[hind_a] = False

        # update the index since there could be multiple hyp events
        # overlapped with hyp event
        #
        #  <----------------------->
        #   <---->  <-->   <-->
        #
        hind_a += 1
        
        # look for hyp events overlapping with hyp event
        #
        for i in range(hind_a, len(hyp_a)):
            
            # update HMF according to the TAES score definition
            #
            if hyp_a[i][2] == ref_a[rind_a][2] and \
               self.anyovlp(ref_a[rind_a], hyp_a[i]):

                # update the flags for processed events
                #
                hypflag_a[i] = False

                ovlp_hit, ovlp_fa \
                    = self.calc_hf(ref_a[rind_a], hyp_a[i])

                p_hit += ovlp_hit
                p_miss -= ovlp_hit
                p_fa += ovlp_fa

            # move to the next event index
            #
            i += 1

        # return gracefully
        #
        return p_hit, p_miss, p_fa
    # 
    # end of method


    # method: compute_partial
    #
    # arguments:
    #  start_r: start time of ref event
    #  stop_r: stop time of ref event
    #  start_h: start time of hyp event
    #  stop_h: stop time of hyp event
    #  flag: flag that suggests that event has previously used
    #  tstop_prev: previous stop time of a recent class
    #
    # return:
    #  hit: calculated fractional number of hits
    #  miss: calculated fractional number of misses
    #  fa: calculated fractional number of false alarms
    #
    # This method calculates hits, misses and false alarms
    #  for detected hyp events by comparing it with duration
    #  of reference/hypothesis events and computing the amount
    #  of overlap between the two.
    #
    def compute_partial(self, ref_a, hyp_a, rind_a, hind_a, \
                        rflags_a, hflags_a, tgt_event_a):

        # check whether current reference event has any overlap
        # with the hyp event
        if not self.anyovlp(ref_a[rind_a], hyp_a[hind_a]):
            return (float(0), float(0), float(0))

        # check whether detected event stop time exceed the 
        # reference stop time.
        #
        elif float(hyp_a[hind_a][1]) >= float(ref_a[rind_a][1]):

            #   <---->
            #     <---->
            #
            #   <---->
            # <-------->
            #            
            # check whether multiple reference events are 
            # overlapped with hypothesis event
            #
            #  <-->    <-->  <-->
            # <--------------------->
            #
            p_hit, p_mis, p_fal \
                = self.ovlp_ref_seqs(ref_a, hyp_a, rind_a, hind_a, 
                                      rflags_a, hflags_a, tgt_event_a)

        # check whether reference event stop time exceed the 
        # detected stop time.
        #
        elif float(ref_a[rind_a][1]) > float(hyp_a[hind_a][1]):

            #   <------>
            # <----->
            #
            #   <------>
            #     <-->
            #
            # check whether multiple hypothesis events are 
            # overlapped with reference event
            #
            #  <----------------------->
            #   <---->  <-->   <-->
            #
            p_hit, p_mis, p_fal \
                = self.ovlp_hyp_seqs(ref_a, hyp_a, rind_a, hind_a,
                                     rflags_a, hflags_a, tgt_event_a)

        # return gracefully
        #
        return (p_hit, p_mis, p_fal)
    #
    # end of method
            
    # method: anyovlp
    #
    # arguments:
    #  ref_a: reference event
    #  hyp_a: hypothesis event
    #
    # return:
    #  boolean: True/False
    #
    # This method looks for any sort of overlap between 
    # two events passed as an argument and return a boolean
    # value indicating the status.
    #
    def anyovlp(self, ref_a, hyp_a):
        
        # create set for the ref/hyp events
        #
        refset = set(range(int(ref_a[0]), int(ref_a[1]) + 1))
        hypset = set(range(int(hyp_a[0]), int(hyp_a[1]) + 1))
            
        if len(refset.intersection(hypset)) != 0:
            return True

        # return gracefully
        #
        return False
    #
    # end of method

    
    # method: calc_hf
    #
    # arguments:
    #  ref_a: reference event
    #  hyp_a: hypothesis event
    #
    # return:
    #  hit: detected hits
    #  fa: detected False Positives 
    #
    # This method calculates hits and false alarms between the 
    # events passed as an argument.
    #
    def calc_hf(self, ref_a, hyp_a):


        ## collect start and stop times from input arg events
        #
        start_r_a = ref_a[0]
        stop_r_a = ref_a[1]
        start_h_a = hyp_a[0]
        stop_h_a = hyp_a[1]

        # initialize local variables
        #
        ref_dur = stop_r_a - start_r_a
        hyp_dur = stop_h_a - start_h_a
        hit = float(0)
        fa = float(0)

        #----------------------------------------------------------------------
        # deal explicitly with the four types of overlaps that can occur
        #----------------------------------------------------------------------

        # (1) for pre-prediction event
        #     ref:         <--------------------->
        #     hyp:   <---------------->
        #
        if start_h_a <= start_r_a and stop_h_a <= stop_r_a:
            hit = (stop_h_a - start_r_a) / ref_dur
            if ((start_r_a - start_h_a) / ref_dur) < 1.0:
                fa = ((start_r_a - start_h_a) / ref_dur)
            else:
                fa = float(1)

        # (2) for post-prediction event
        #     ref:         <--------------------->
        #     hyp:                  <-------------------->
        #
        elif start_h_a >= start_r_a and stop_h_a >= stop_r_a:

            hit = (stop_r_a - start_h_a) / ref_dur                       
            if ((stop_h_a - stop_r_a) / ref_dur) < 1.0:
                fa = ((stop_h_a - stop_r_a) / ref_dur)
            else:
                fa = float(1)


        # (3) for over-prediction event
        #     ref:              <------->
        #     hyp:        <------------------->
        #
        elif start_h_a < start_r_a and stop_h_a > stop_r_a:
            
            hit = 1.0
            fa = ((stop_h_a - stop_r_a) + (start_r_a - start_h_a)) /\
                 ref_dur
            if fa > 1.0:
                fa = float(1)

        # (4) for under-prediction event
        #     ref:        <--------------------->
        #     hyp:            <------>
        #
        else:
            hit = (stop_h_a - start_h_a) / ref_dur

        # exit gracefully
        #
        return (hit, fa)
    #
    # end of method
        
    # method: get_events
    # 
    # arguments:
    #  start: start time
    #  stop: stop_time
    #  events: a list of events
    #  flags: event flags
    #
    # return:
    #  labels: the labels that overlap with the start and stop time
    #  starts: a list of start times
    #  stops: a list of stop times
    #
    # this method returns a list of events that fall within a specified
    # range of time of main event list (i.e. here events_a)
    #
    def get_events(self, start_a, stop_a, events_a, flags_a):

        # declare output variables
        #
        labels = []
        starts = []
        stops = []
        flags = []
        ind = []

        # loop over all events
        #
        for i in range(len(events_a)):

            # if the event overlaps partially with the interval,
            # it is a match. this means:
            #              start               stop
            #   |------------|<---------------->|-------------|
            #          |---------- event -----|
            #
            if (events_a[i][1] > start_a) and (events_a[i][0] < stop_a):
                starts.append(events_a[i][0])
                stops.append(events_a[i][1])
                labels.append(events_a[i][2])
                ind.append(i)
                flags.append(flags_a[i])

        # exit gracefully
        #
        return [labels, starts, stops]
    #
    # end of method

    # method: compute_performance
    #
    # arguments: none
    #
    # return: a logical value indicating status
    #
    # This method computes a number of standard measures of performance. The
    # terminology follows these references closely:
    #
    #  https://en.wikipedia.org/wiki/Confusion_matrix
    #  https://en.wikipedia.org/wiki/Precision_and_recall
    #  http://www.dataschool.io/simple-guide-to-confusion-matrix-terminology/
    #
    # The approach taken here for a multi-class problem is to convert the
    # NxN matrix to a 2x2 for each label, and then do the necessary
    # computations.
    #
    def compute_performance(self):

        # check for a zero count
        #
        num_total_ref_events = sum(self.tgt_d.values())
        if num_total_ref_events == 0:
            print("%s (%s: %s): number of events is zero (%d %d)" % \
                    (sys.argv[0], __name__, "compute_performance", \
                     num_total_ref_events))
            return None

        #----------------------------------------------------------------------
        # (1) The first block of parameters count events such as hits,
        #     missses and false alarms. The overlap algorithm provides
        #     these directly.
        #
        for key1 in self.hit_d:
            self.ins_d[key1] = self.fal_d[key1]
            self.del_d[key1] = self.mis_d[key1]

        #----------------------------------------------------------------------
        # (2) The second block of computations are the derived measures
        #     such as sensitivity. These are computed using a two-step
        #     approach:
        #      (2.2) compute true positives, etc. (tp, tn, fp, fn)
        #      (2.3) compute the derived measures (e.g., sensitivity)
        #
        # loop over all labels
        #
        for key1 in self.hit_d:

            #------------------------------------------------------------------
            # (2.2) The overlap algorithm outputs hits, misses and false alarms
            #       directly. These must be converted to (tp, tn, fp, fn).
            #
            # compute true positives (tp)
            #
            self.tp_d[key1] = self.hit_d[key1]

            # compute true negatives (tn):
            #  sum the hits that are not the current label
            #
            tn_sum = int(0)
            for key2 in self.hit_d:
                if key1 != key2:
                    tn_sum += self.hit_d[key2]
            self.tn_d[key1] = tn_sum

            # compute false positives (fp): copy false alarms
            #
            self.fp_d[key1] = self.fal_d[key1]

            # compute false negatives (fn): copy misses
            #
            self.fn_d[key1] = self.mis_d[key1]

            # check the health of the confusion matrix
            #
            tp = self.tp_d[key1]
            fp = self.fp_d[key1]
            tn = self.tn_d[key1]
            fn = self.fn_d[key1]
            tdur = self.total_dur_d

            if ((tp + fn) == 0) or ((fp + tn) == 0) or \
               ((tp + fp) == 0) or ((fn + tn) == 0):
                print("%s (%s: %s): " % \
                    (sys.argv[0], __name__, "compute_performance"), \
                    "divide by zero (warning) (%d %d %d %d)" % \
                    (tp, fp, tn, fn))
            elif (round(tdur, ntt.MAX_PRECISION) == 0):
                print("%s (%s: %s): duration is zero (warning) (%f)" % \
                    (sys.argv[0], __name__, "compute_performance", tdur))

            # (2.3) compute derived measures
            #
            if (tp + fn) != 0:
                self.tpr_d[key1] = float(self.tp_d[key1]) / float(tp + fn)
            else:
                self.tpr_d[key1] = float(0)

            if (tn + fp) != 0:
                self.tnr_d[key1] = float(self.tn_d[key1]) / float(tn + fp)
            else:
                self.tnr_d[key1] = float(0)

            if (tp + fp) != 0:
                self.ppv_d[key1] = float(self.tp_d[key1]) / float(tp + fp)
            else:
                self.ppv_d[key1] = float(0)

            if (tn + fn) != 0:
                self.npv_d[key1] = float(self.tn_d[key1]) / float(tn + fn)
            else:
                self.npv_d[key1] = float(0)

            self.fnr_d[key1] = 1 - float(self.tpr_d[key1])
            self.fpr_d[key1] = 1 - float(self.tnr_d[key1])
            self.fdr_d[key1] = 1 - float(self.ppv_d[key1])
            self.for_d[key1] = 1 - float(self.npv_d[key1])

            if (tp + tn + fp + fn) != 0:
                self.acc_d[key1] = float(self.tp_d[key1] + self.tn_d[key1]) / \
                                   (tp + tn + fp + fn)
                self.prv_d[key1] = float(self.tp_d[key1] + self.fn_d[key1]) / \
                                   (tp + tn + fp + fn)
            else:
                self.acc_d[key1] = float(0)
                self.prv_d[key1] = float(0)

            self.msr_d[key1] = 1 - self.acc_d[key1]

            # compute the f1 score:
            #  this has to be done after sensitivity and prec are computed
            #
            f1s_denom = float(self.ppv_d[key1] + self.tpr_d[key1])
            if round(f1s_denom, ntt.MAX_PRECISION) == 0:
                print("%s (%s: %s): f ratio divide by zero (warning) (%s)" % \
                    (sys.argv[0], __name__, "compute_performance", key1))
                self.f1s_d[key1] = float(0)
            else:
                self.f1s_d[key1] = 2.0 * self.ppv_d[key1] * \
                                    self.tpr_d[key1] / f1s_denom

            # compute the false alarm rate
            #
            if (round(tdur, ntt.MAX_PRECISION) == 0):
                print("%s (%s: %s): zero duration (warning) (%s)" % \
                    (sys.argv[0], __name__, "compute_performance", key1))
                self.flr_d[key1] = float(0)
            else:
                self.flr_d[key1] = float(fp) / tdur * (60 * 60 * 24)
        
        #----------------------------------------------------------------------
        # (3) the third block of parameters are the summary values
        #
        self.sum_tgt_d = sum(self.tgt_d.values())
        self.sum_hit_d = sum(self.hit_d.values())
        self.sum_mis_d = sum(self.mis_d.values())
        self.sum_fal_d = sum(self.fal_d.values())
        self.sum_ins_d = sum(self.ins_d.values())
        self.sum_del_d = sum(self.del_d.values())

        self.sum_tp_d = sum(self.tp_d.values())
        self.sum_tn_d = sum(self.tn_d.values())
        self.sum_fp_d = sum(self.fp_d.values())
        self.sum_fn_d = sum(self.fn_d.values())

        if (self.sum_tp_d + self.sum_fn_d) != 0:
            self.sum_tpr_d = float(self.sum_tp_d) / \
                             float(self.sum_tp_d + self.sum_fn_d)
        else:
            self.sum_tpr_d = float(0)

        if (self.sum_tn_d + self.sum_fp_d) != 0:
            self.sum_tnr_d = float(self.sum_tn_d) / \
                             float(self.sum_tn_d + self.sum_fp_d)
        else:
            self.sum_tnr_d = float(0)

        if (self.sum_tp_d + self.sum_fp_d) != 0:
            self.sum_ppv_d = float(self.sum_tp_d) / \
                             float(self.sum_tp_d + self.sum_fp_d)
        else:
            self.sum_ppv_d = float(0)

        if (self.sum_tn_d + self.sum_fn_d) != 0:
            self.sum_npv_d = float(self.sum_tn_d) / \
                             float(self.sum_tn_d + self.sum_fn_d)
        else:
            self.sum_npv_d = float(0)

        self.sum_fnr_d = 1 - float(self.sum_tpr_d)
        self.sum_fpr_d = 1 - float(self.sum_tnr_d)
        self.sum_fdr_d = 1 - float(self.sum_ppv_d)
        self.sum_for_d = 1 - float(self.sum_npv_d)

        if (self.sum_tp_d + self.sum_tn_d + \
            self.sum_fp_d + self.sum_fn_d) != 0:
            self.sum_acc_d = float(self.sum_tp_d + self.sum_tn_d) / \
                             (float(self.sum_tp_d + self.sum_tn_d + \
                                    self.sum_fp_d + self.sum_fn_d))
            self.sum_prv_d = float(self.sum_tp_d + self.sum_fn_d) / \
                             (float(self.sum_tp_d + self.sum_tn_d + \
                                    self.sum_fp_d + self.sum_fn_d))
        else:
            self.sum_acc_d = float(0)
            self.sum_prv_d = float(0)

        self.sum_msr_d = 1 - self.sum_acc_d

        if round(f1s_denom, ntt.MAX_PRECISION) == 0:
            print("%s (%s: %s): f ratio divide by zero (warning) (%s)" % \
                (sys.argv[0], __name__, "compute_performance", "summary"))
            self.sum_f1s_d = float(0)
        else:
            self.sum_f1s_d = 2.0 * self.sum_ppv_d * self.sum_tpr_d / f1s_denom

        # compute the false alarm rate
        #
        if round(self.total_dur_d, ntt.MAX_PRECISION) == 0:
            print("%s (%s: %s): zero duration (warning) (%s)" % \
                (sys.argv[0], __name__, "compute_performance", "summary"))
            self.sum_flr_d = float(0)
        else:
            self.sum_flr_d = float(self.sum_fp_d) / self.total_dur_d * \
                             (60 * 60 * 24)

        # exit gracefully
        #
        return True
    #
    # end of method

    # method: display_results
    #
    # arguments:
    #  fp: output file pointer
    #
    # return: a logical value indicating status
    #
    # This method displays all the results in output report.
    #
    def display_results(self, fp_a):

        # write per label header
        #
        fp_a.write(("Per Label Results:\n").upper())
        fp_a.write("\n")

        # per label results: loop over all classes
        #
        for key in self.hit_d:
            fp_a.write((" Label: %s\n" % key).upper())
            fp_a.write("\n")

            fp_a.write("   %30s: %12.2f   <**\n" % \
                       ("Targets", float(self.tgt_d[key])))
            fp_a.write("   %30s: %12.2f   <**\n" % \
                       ("Hits", float(self.hit_d[key])))
            fp_a.write("   %30s: %12.2f   <**\n" % \
                       ("Misses", float(self.mis_d[key])))
            fp_a.write("   %30s: %12.2f   <**\n" % \
                       ("False Alarms", float(self.fal_d[key])))
            fp_a.write("   %30s: %12.2f\n" % \
                       ("Insertions", float(self.ins_d[key])))
            fp_a.write("   %30s: %12.2f\n" % \
                       ("Deletions", float(self.del_d[key])))
            fp_a.write("\n")

            fp_a.write("   %30s: %12.2f\n" % \
                       ("True Positives (TP)", float(self.tp_d[key])))
            fp_a.write("   %30s: %12.2f\n" % \
                       ("True Negatives (TN)", float(self.tn_d[key])))
            fp_a.write("   %30s: %12.2f\n" % \
                       ("False Positives (FP)", float(self.fp_d[key])))
            fp_a.write("   %30s: %12.2f\n" % \
                       ("False Negatives (FN)", float(self.fn_d[key])))
            fp_a.write("\n")

            fp_a.write("   %30s: %12.2f%%\n" % \
                       ("Sensitivity (TPR, Recall)", self.tpr_d[key] * 100.0))
            fp_a.write("   %30s: %12.2f%%\n" % \
                       ("Specificity (TNR)", self.tnr_d[key] * 100.0))
            fp_a.write("   %30s: %12.2f%%\n" % \
                       ("Precision (PPV)", self.ppv_d[key] * 100.0))
            fp_a.write("   %30s: %12.2f%%\n" % \
                       ("Negative Pred. Value (NPV)", self.npv_d[key] * 100.0))
            fp_a.write("   %30s: %12.2f%%\n" % \
                       ("Miss Rate (FNR)", self.fnr_d[key] * 100.0))
            fp_a.write("   %30s: %12.2f%%\n" % \
                       ("False Positive Rate (FPR)", self.fpr_d[key] * 100.0))
            fp_a.write("   %30s: %12.2f%%\n" % \
                       ("False Discovery Rate (FDR)", self.fdr_d[key] * 100.0))
            fp_a.write("   %30s: %12.2f%%\n" % \
                       ("False Omission Rate (FOR)", self.for_d[key] * 100.0))
            fp_a.write("   %30s: %12.2f%%\n" % \
                       ("Accuracy", self.acc_d[key] * 100.0))
            fp_a.write("   %30s: %12.2f%%\n" % \
                       ("Misclassification Rate", self.msr_d[key] * 100.0))
            fp_a.write("   %30s: %12.2f%%\n" % \
                       ("Prevalence", self.prv_d[key] * 100.0))
            fp_a.write("   %30s: %12.2f\n" % \
                       ("F1 Score (F Ratio)", self.f1s_d[key]))
            fp_a.write("   %30s: %12.2f per 24 hours\n" % \
                       ("False Alarm Rate", self.flr_d[key]))
            fp_a.write("\n")

        # display a summary of the results
        #
        fp_a.write(("Summary:\n").upper())
        fp_a.write("\n")

        # display the standard derived values
        #
        fp_a.write("   %30s: %12.2f   <**\n" % \
                   ("Total", float(self.sum_tgt_d)))
        fp_a.write("   %30s: %12.2f   <**\n" % \
                   ("Hits", float(self.sum_hit_d)))
        fp_a.write("   %30s: %12.2f   <**\n" % \
                   ("Misses", float(self.sum_mis_d)))
        fp_a.write("   %30s: %12.2f   <**\n" % \
                   ("False Alarms", float(self.sum_fal_d)))
        fp_a.write("   %30s: %12.2f\n" % \
                   ("Insertions", float(self.sum_ins_d)))
        fp_a.write("   %30s: %12.2f\n" % \
                   ("Deletions", float(self.sum_del_d)))
        fp_a.write("\n")

        fp_a.write("   %30s: %12.2f\n" % \
                   ("True Positives(TP)", float(self.sum_tp_d)))
        fp_a.write("   %30s: %12.2f\n" % \
                   ("False Positives (FP)", float(self.sum_fp_d)))
        fp_a.write("\n")

        fp_a.write("   %30s: %12.2f%%\n" % \
                   ("Sensitivity (TPR, Recall)", self.sum_tpr_d * 100.0))
        fp_a.write("   %30s: %12.2f%%\n" % \
                   ("Miss Rate (FNR)", self.sum_fnr_d * 100.0))
        fp_a.write("   %30s: %12.2f%%\n" % \
                   ("Accuracy", self.sum_acc_d * 100.0))
        fp_a.write("   %30s: %12.2f%%\n" % \
                   ("Misclassification Rate", self.sum_msr_d * 100.0))
        fp_a.write("   %30s: %12.2f%%\n" % \
                   ("Prevalence", self.sum_prv_d * 100.0))
        fp_a.write("   %30s: %12.2f\n" % \
                   ("F1 Score", self.sum_f1s_d))
        fp_a.write("\n")

        # display the overall false alarm rate
        #
        fp_a.write("   %30s: %12.2f secs\n" % \
                   ("Total Duration", self.total_dur_d))
        fp_a.write("   %30s: %12.2f events\n" % \
                   ("Total False Alarms", self.sum_fp_d))
        fp_a.write("   %30s: %12.2f per 24 hours\n" % \
                   ("Total False Alarm Rate", self.sum_flr_d))
        fp_a.write("\n")

        # exit gracefully
        #
        return True
    #
    # end of method

    # method: score_roc
    #
    # arguments:
    #  events_ref: a reference list
    #  events_hyp: a hypothesis list
    #
    # return: a logical value indicating status
    #
    # This method computes a confusion matrix for an roc/det curve.
    #
    def score_roc(self, events_ref_a, events_hyp_a):
        
        # declare local variables
        #
        status = True
        ann = nat.Annotations()

        # loop over all event lists (corresponding to files)
        #
        for ann_ref, ann_hyp in zip(events_ref_a, events_hyp_a):

            # update the total duration
            #
            self.total_dur_d += ann_ref[-1][1]

            # add this to the confusion matrix
            #
            refo, hypo, hit, mis, fal = self.compute(ann_ref, ann_hyp)
            if refo == None:
                print("%s (%s: %s): error computing confusions" % \
                    (sys.argv[0], __name__, "score_roc"))
                return False

        # exit gracefully
        # 
        return True
    #
    # end of method

    # method: compute_performance_roc
    #
    # arguments:
    #  key: the class to be scored
    #
    # return: a logical value indicating status
    #
    # This is a stripped down version of compute_performance that is
    # focused on the data needed for an ROC or DET curve.
    #
    # Note that because of the way this method is used, error messages
    # are suppressed.
    #
    def compute_performance_roc(self, key_a):

        # check for a zero count
        #
        num_total_ref_events = sum(self.tgt_d.values())
        if num_total_ref_events == 0:
            print("%s (%s: %s): number of events is zero (%d)" % \
                (sys.argv[0], __name__, "compute_performance_roc", \
                 num_total_ref_events))
            return False

        #----------------------------------------------------------------------
        # (1) The first block of parameters count events such as hits,
        #     missses and false alarms. The overlap algorithm provides
        #     these directly.
        #
        for key1 in self.hit_d:
            self.ins_d[key1] = self.fal_d[key1]
            self.del_d[key1] = self.mis_d[key1]

        #----------------------------------------------------------------------
        # (2) The second block of computations are the derived measures
        #     such as sensitivity. These are computed using a two-step
        #     approach:
        #      (2.2) compute true positives, etc. (tp, tn, fp, fn)
        #      (2.3) compute the derived measures (e.g., sensitivity)
        #
        #------------------------------------------------------------------
        # (2.2) The overlap algorithm outputs hits, misses and false alarms
        #       directly. These must be converted to (tp, tn, fp, fn).
        #
        # compute true positives (tp)
        #
        self.tp_d[key_a] = self.hit_d[key_a]

        # compute true negatives (tn):
        #  sum the hits that are not the current label
        #
        tn_sum = int(0)
        for key2 in self.hit_d:
            if key_a != key2:
                tn_sum += self.hit_d[key2]
        self.tn_d[key_a] = tn_sum

        # compute false positives (fp): copy false alarms
        #
        self.fp_d[key_a] = self.fal_d[key_a]

        # compute false negatives (fn): copy misses
        #
        self.fn_d[key_a] = self.mis_d[key_a]

        # check the health of the confusion matrix
        #
        tp = self.tp_d[key_a]
        fp = self.fp_d[key_a]
        tn = self.tn_d[key_a]
        fn = self.fn_d[key_a]
        tdur = self.total_dur_d

        # (2.3) compute derived measures
        #
        if (tp + fn) != 0:
            self.tpr_d[key_a] = float(self.tp_d[key_a]) / float(tp + fn)
        else:
            self.tpr_d[key_a] = float(0)

        if (tn + fp) != 0:
            self.tnr_d[key_a] = float(self.tn_d[key_a]) / float(tn + fp)
        else:
            self.tnr_d[key_a] = float(0)

        self.fnr_d[key_a] = 1 - float(self.tpr_d[key_a])
        self.fpr_d[key_a] = 1 - float(self.tnr_d[key_a])

        # exit gracefully
        #
        return True
    #
    # end of method

    # method: get_roc
    #
    # arguments:
    #  key: the symbol for which the values are needed
    #
    # return: a logical value indicating status
    #
    # This method simply returns the quanities needed for an roc curve:
    # true positive rate (tpr) as a function of the false positive rate (fpr).
    #
    def get_roc(self, key_a):
        return self.fpr_d[key_a], self.tpr_d[key_a]

    # method: get_det
    #
    # arguments:
    #  key: the symbol for which the values are needed
    #
    # return: a logical value indicating status
    #
    # This method simply returns the quanities needed for a det curve:
    # false negative rate (fnr) as a function of the false positive rate (fpr).
    #
    def get_det(self, key_a):
        return self.fpr_d[key_a], self.fnr_d[key_a], 

# end of file
#
