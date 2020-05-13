#!/usr/bin/env python

# file: $NEDC_NFC/class/python/nedc_eval_tools/nedc_eval_dpalign.py
#
# revision history:
#  20170815 (JP): added another metric: prevalence
#  20170812 (JP): changed the divide by zero checks
#  20170716 (JP): upgraded to using the new annotation tools
#  20170702 (JP): added summary scoring; revamped the derived metrics
#  20170617 (JP): initial version
#
# usage:
#  import nedc_eval_dpalign as nepoch
#
# This file implements NEDC's dynamic programming alignment scoring algorithm.
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
NEDC_DPALIGN = "NEDC_DPALIGN"

# define error types
#
DPALIGN_ETYPES_NULL = int(-1)
DPALIGN_ETYPES_DEL = int(0)
DPALIGN_ETYPES_INS = int(1)
DPALIGN_ETYPES_SUB = int(2)

# define dynamic programming penalties and designate a symbol to be
# treated as null (background)
#
PENALTY_DEL = float(1.0)
PENALTY_INS = float(1.0)
PENALTY_SUB = float(1.0)

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
# This method runs the NEDC dp alignment scoring algorithm by:
#  (1) loading the annotations
#  (2) scoring them
#  (3) displaying the results
#
def run(reflist_a, hyplist_a, map_a, odir_a, rfile_a, fp_a):

    # define local variables
    #
    status = True
    ndpalign = NedcDPAlignment()

    # check the reference and hyp file lists
    #
    num_files_ref = len(reflist_a)
    num_files_hyp = len(hyplist_a)

    if num_files_ref < 1 or num_files_hyp < 1 or \
       num_files_ref != num_files_hyp:
        print("%s (%s: %s): file list error (%s %s)" % \
            (sys.argv[0], __name__, "run", reflist_a, hyplist_a))
        return False

    # run dp alignment scoring
    #
    status = ndpalign.init_score(map_a)
    status = ndpalign.score(reflist_a, hyplist_a, map_a, rfile_a)
    if status == False:
        print("%s (%s: %s): error during scoring" % \
            (sys.argv[0], __name__, "run"))
        return False

    # compute performance
    #
    cnf = ndpalign.compute_performance()
    if status == None:
        print("%s (%s: %s): error computing performance" % \
            (sys.argv[0], __name__, "run"))
        return False

    # collect information for scoring and display
    #
    header, tbl = ndt.create_table(cnf)
    status = ndpalign.display_results("NEDC DP Alignment Confusion Matrix",
                                      header, tbl, fp_a)
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

# class: NedcDPAlignment
#
# This class contains methods that execute a dynamic programming based
# approach to scoring that was popularized in speech recognition.
#
class NedcDPAlignment():
    
    # method: constructor
    # 
    # arguments: none
    #
    # return: none
    #
    def __init__(self):

        # decode the parameters passed from the global vars
        #
        self.penalty_del_d = PENALTY_DEL
        self.penalty_ins_d = PENALTY_INS
        self.penalty_sub_d = PENALTY_SUB

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
        self.sub_d = {}
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
        self.refo_d = []
        self.hypo_d = []
        
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
        self.sub_d = OrderedDict()
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
            self.sub_d[key] = OrderedDict()
            for key2 in map_a:
                self.sub_d[key][key2] = int(0)

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

            # update the total duration
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
            refo, hypo = self.compute(ann_ref, ann_hyp)
            if refo == None:
                print("%s (%s: %s): error computing confusion matrix (%s %s)" \
                    % (sys.argv[0], __name__, "score", \
                       files_ref_a[i], files_hyp_a[i]))
                return False

            # output the files to the per file results file
            #
            ref_fm, hyp_fm, hits, subs, inss, dels = \
		ndt.format_hyp(refo, hypo)

            # output the files to the per file results file
            #
            self.rfile_d.write("%5d: %s.tse\n" % (i, fname))
            self.rfile_d.write("%5s  %s.hyp\n" % ("", fname))
            self.rfile_d.write("  Ref: %s\n" % ' '.join(refo))
            self.rfile_d.write("  Hyp: %s\n" % ' '.join(hypo))

            self.rfile_d.write("%7s (Hits: %d  Sub: %d  Ins: %d  Del: %d  Total: %d)\n" \
                               % ("", hits, subs, inss, dels, \
                                  subs + inss + dels))
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
    #
    # this method measures similarity by performing a dynamic programming
    # based string alignment.
    #
    def compute(self, ref_a, hyp_a):

        # extract the labels from the input file record and extend the 
        #  inputs with a dummy symbol at the beginning and end:
        #  this makes the code a little simpler and more uniform
        #
        ref = [ntt.NULL_CLASS]
        for value in ref_a:
            ref.append(value[2])
        ref.append(ntt.NULL_CLASS)

        hyp = [ntt.NULL_CLASS]
        for value in hyp_a:
            hyp.append(value[2])
        hyp.append(ntt.NULL_CLASS)

        # compute the lengths and clear temp variables
        #
        m = len(ref)
        n = len(hyp)
        d = []
        etypes = []

        # zero out the cost matrix and initialize the edges with the
        # correct error types (backpointers)
        #
        for i in range(m):
            d.append([])
            etypes.append([])
            for j in range(n):
                d[i].append(float(0))
                etypes[i].append(DPALIGN_ETYPES_NULL)

        for i in range(1,n):
            d[0][i] = d[0][i-1] + self.penalty_ins_d
            etypes[0][i] = DPALIGN_ETYPES_INS

        for i in range(1,m):
            d[i][0] = d[i-1][0] + self.penalty_del_d
            etypes[i][0] = DPALIGN_ETYPES_DEL
        etypes[0][0] = DPALIGN_ETYPES_SUB

        # iterate over the interior nodes:
        #  cols (j) correspond to the reference. rows (i) correspond
        #  to the hypothesis. iterate over a column first (j), matching
        #  ref to a specific event in a hypothesis, and then over rows (i)
        #  next (iterating over events in the reference).
        #
        for j in range(1,n):
            for i in range(1,m):

                # compute the node penalties
                #
                d_del = d[i-1][j] + self.penalty_del_d
                d_ins = d[i][j-1] + self.penalty_ins_d
                d_sub = d[i-1][j-1]
                if ref[i] != hyp[j]:
                    d_sub += self.penalty_sub_d

                # update the best path and save the error type
                #
                min_dist = d_sub
                etypes[i][j] = DPALIGN_ETYPES_SUB
                if (d_ins < min_dist):
                    min_dist = d_ins
                    etypes[i][j] = DPALIGN_ETYPES_INS
                if (d_del < min_dist):
                    min_dist = d_del
                    etypes[i][j] = DPALIGN_ETYPES_DEL
                d[i][j] = min_dist

        # the last node (m-1, n-1) is where the best path terminates. backtrack
        # to get the best path. start at (m-1, n-1) and end at (0,0).
        #
        i = int(m - 1)
        j = int(n - 1)
        reft = []
        hypt = []

        while (True):
            if etypes[i][j] == DPALIGN_ETYPES_DEL:
                reft.append(ref[i])
                hypt.append(ntt.NULL_CLASS)
                i -= 1
            elif etypes[i][j] == DPALIGN_ETYPES_INS:
                reft.append(ntt.NULL_CLASS)
                hypt.append(hyp[j])
                j -= 1
            elif etypes[i][j] == DPALIGN_ETYPES_SUB:
                reft.append(ref[i])
                hypt.append(hyp[j])
                i -= 1
                j -= 1
            else:
                print("%s (%s: %s): error doing dynamic programming (%s %s)" \
                    % (sys.argv[0], __name__, "compute", reft, hypt))
                return False

            # the best path must terminate on (0,0)
            #
            if (i < 0) and (j < 0):
                break

        # flip the arrays so the output is in the right order
        #
        refo = reft[::-1]
        hypo = hypt[::-1]

        # count errors - igtnore the first and last items since they are
        # due to the dummy nodes
        #
        for i in range(1, len(refo) - 1):
        
            # track no. of targets, del, ins and subs
            #
            if refo[i] == ntt.NULL_CLASS:
                self.ins_d[hypo[i]] += int(1)
            elif hypo[i] == ntt.NULL_CLASS:
                self.tgt_d[refo[i]] += 1            
                self.del_d[refo[i]] += int(1)
            else:
                self.tgt_d[refo[i]] += 1            
                self.sub_d[refo[i]][hypo[i]] += 1
                
            # track no. of hits, misses and false alarms
            #
            if refo[i] == ntt.NULL_CLASS:
                self.fal_d[hypo[i]] += int(1)
            elif hypo[i] == ntt.NULL_CLASS:
                self.mis_d[refo[i]] += int(1)
            elif refo[i] == hypo[i]:
                self.hit_d[refo[i]] += int(1)
            else:
                self.mis_d[refo[i]] += int(1)

        # exit gracefully
        #
        return [refo, hypo]

    # method: compute_performance
    #
    # arguments: none
    #
    # return:
    #  cnf: a confusion matrix
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
        #     missses and false alarms. These are directly computed
        #     from the output of the dp alignment.


        #----------------------------------------------------------------------
        # (2) The second block of computations are the derived measures
        #     such as sensitivity. These are computed using a two-step
        #     approach:
        #      (2.2) compute true positives, etc. (tp, tn, fp, fn)
        #      (2.3) compute the derived measures (e.g., sensitivity)
        #
        # loop over all labels
        #
        for key1 in self.sub_d:

            #------------------------------------------------------------------
            # (2.2) The dp algorithm outputs hits, misses and false alarms
            #       directly. These must be converted to (tp, tn, fp, fn).
            #
            # compute true positives (tp)
            #
            self.tp_d[key1] = self.hit_d[key1]

            # compute true negatives (tn)
            #  sum the submatrix formed when you exclude the row and column
            #  associated with key1
            #
            tn_sum = int(0)
            for key2 in self.sub_d:
                for key3 in self.sub_d:
                    if (key1 != key2) and (key1 != key3):
                        tn_sum += self.sub_d[key2][key3]
            self.tn_d[key1] = tn_sum

            # compute false positives (fp)
            #
            self.fp_d[key1] = self.ins_d[key1]

            # compute false negatives (fn)
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
            if (round(tdur, ntt.MAX_PRECISION) != 0):
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
            self.sum_flr_d = float(0)
        else:
            self.sum_flr_d = float(self.sum_fp_d) / self.total_dur_d * \
                             (60 * 60 * 24)

        # exit gracefully
        #
        return self.sub_d
    #
    # end of method

    # method: display_results
    #
    # arguments:
    #  title: the title of the confusion table
    #  headers: the headers associated with the columns of the matrix
    #  tbl: the table to be printed
    #  fp: output file pointer
    #
    # return: a logical value indicating status
    #
    # This method displays all the results in output report.
    #
    def display_results(self, title_a, headers_a, tbl_a, fp_a):

        # print complete table in output file
        #
        ndt.print_table(title_a, headers_a, tbl_a,
                        "%10s", "%12.2f", "%6.2f", fp_a)
        fp_a.write("\n")

        # write per label header
        #
        fp_a.write(("Per Label Results:\n").upper())
        fp_a.write("\n")

        # per label results: loop over all classes
        #
        for key in self.sub_d:
            fp_a.write((" Label: %s\n" % key).upper())
            fp_a.write("\n")

            fp_a.write("   %30s: %12.0f\n" % \
                       ("Targets", float(self.tgt_d[key])))
            fp_a.write("   %30s: %12.0f\n" % \
                       ("Hits", float(self.hit_d[key])))
            fp_a.write("   %30s: %12.0f\n" % \
                       ("Misses", float(self.mis_d[key])))
            fp_a.write("   %30s: %12.0f\n" % \
                       ("False Alarms", float(self.fal_d[key])))
            fp_a.write("   %30s: %12.0f   <**\n" % \
                       ("Insertions", float(self.ins_d[key])))
            fp_a.write("   %30s: %12.0f   <**\n" % \
                       ("Deletions", float(self.del_d[key])))
            fp_a.write("\n")

            fp_a.write("   %30s: %12.0f\n" % \
                       ("True Positives (TP)", float(self.tp_d[key])))
            fp_a.write("   %30s: %12.0f\n" % \
                       ("True Negatives (TN)", float(self.tn_d[key])))
            fp_a.write("   %30s: %12.0f\n" % \
                       ("False Positives (FP)", float(self.fp_d[key])))
            fp_a.write("   %30s: %12.0f\n" % \
                       ("False Negatives (FN)", float(self.fn_d[key])))
            fp_a.write("\n")

            fp_a.write("   %30s: %12.4f%%\n" % \
                       ("Sensitivity (TPR, Recall)", self.tpr_d[key] * 100.0))
            fp_a.write("   %30s: %12.4f%%\n" % \
                       ("Specificity (TNR)", self.tnr_d[key] * 100.0))
            fp_a.write("   %30s: %12.4f%%\n" % \
                       ("Precision (PPV)", self.ppv_d[key] * 100.0))
            fp_a.write("   %30s: %12.4f%%\n" % \
                       ("Negative Pred. Value (NPV)", self.npv_d[key] * 100.0))
            fp_a.write("   %30s: %12.4f%%\n" % \
                       ("Miss Rate (FNR)", self.fnr_d[key] * 100.0))
            fp_a.write("   %30s: %12.4f%%\n" % \
                       ("False Positive Rate (FPR)", self.fpr_d[key] * 100.0))
            fp_a.write("   %30s: %12.4f%%\n" % \
                       ("False Discovery Rate (FDR)", self.fdr_d[key] * 100.0))
            fp_a.write("   %30s: %12.4f%%\n" % \
                       ("False Omission Rate (FOR)", self.for_d[key] * 100.0))
            fp_a.write("   %30s: %12.4f%%\n" % \
                       ("Accuracy", self.acc_d[key] * 100.0))
            fp_a.write("   %30s: %12.4f%%\n" % \
                       ("Misclassification Rate", self.msr_d[key] * 100.0))
            fp_a.write("   %30s: %12.4f%%\n" % \
                       ("Prevalence", self.prv_d[key] * 100.0))
            fp_a.write("   %30s: %12.4f\n" % \
                       ("F1 Score (F Ratio)", self.f1s_d[key]))
            fp_a.write("   %30s: %12.4f per 24 hours\n" % \
                       ("False Alarm Rate", self.flr_d[key]))
            fp_a.write("\n")

        # display a summary of the results
        #
        fp_a.write(("Summary:\n").upper())
        fp_a.write("\n")

        # display the standard derived values
        #
        fp_a.write("   %30s: %12.0f\n" % \
                   ("Total", float(self.sum_tgt_d)))
        fp_a.write("   %30s: %12.0f\n" % \
                   ("Hits", float(self.sum_hit_d)))
        fp_a.write("   %30s: %12.0f\n" % \
                   ("Misses", float(self.sum_mis_d)))
        fp_a.write("   %30s: %12.0f\n" % \
                   ("False Alarms", float(self.sum_fal_d)))
        fp_a.write("   %30s: %12.0f   <**\n" % \
                   ("Insertions", float(self.sum_ins_d)))
        fp_a.write("   %30s: %12.0f   <**\n" % \
                   ("Deletions", float(self.sum_del_d)))
        fp_a.write("\n")

        fp_a.write("   %30s: %12.0f\n" % \
                   ("True Positives(TP)", float(self.sum_tp_d)))
        fp_a.write("   %30s: %12.0f\n" % \
                   ("False Positives (FP)", float(self.sum_fp_d)))
        fp_a.write("\n")

        fp_a.write("   %30s: %12.4f%%\n" % \
                   ("Sensitivity (TPR, Recall)", self.sum_tpr_d * 100.0))
        fp_a.write("   %30s: %12.4f%%\n" % \
                   ("Miss Rate (FNR)", self.sum_fnr_d * 100.0))
        fp_a.write("   %30s: %12.4f%%\n" % \
                   ("Accuracy", self.sum_acc_d * 100.0))
        fp_a.write("   %30s: %12.4f%%\n" % \
                   ("Misclassification Rate", self.sum_msr_d * 100.0))
        fp_a.write("   %30s: %12.4f%%\n" % \
                   ("Prevalence", self.sum_prv_d * 100.0))
        fp_a.write("   %30s: %12.4f\n" % \
                   ("F1 Score", self.sum_f1s_d))
        fp_a.write("\n")

        # display the overall false alarm rate
        #
        fp_a.write("   %30s: %12.4f secs\n" % \
                   ("Total Duration", self.total_dur_d))
        fp_a.write("   %30s: %12.4f events\n" % \
                   ("Total False Alarms", self.sum_fp_d))
        fp_a.write("   %30s: %12.4f per 24 hours\n" % \
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
            refo, hypo = self.compute(ann_ref, ann_hyp)
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
