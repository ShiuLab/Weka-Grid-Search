'''Parses the weka output predictions for easy use with ROCR.

INPUT
weka_output_parser.py [parameter file OR single prediction file] ["single" if
    you are inputing a single prediction file]

Assumes that you used 10-fold crosss validation. Removes instances that have
fewer then 10 cross validations.

OUTPUT
Parsed prediction (.parsed) and AUC (.AUC) files for each prediction file.
Additionally
'''

import sys
import os
import re
from grid_search_cc import *

class parse_weka_output(object):
    '''Calculates the AUC-ROC for a given weka output file
    '''
    def __init__(self, weka_out, invert = 0):
        self.weka_out = weka_out
        self.invert = invert
        self.parse_file()
    
    def parse_file(self):
        '''Converts the weka output to a tab delimited format
        '''
        reg = r'\s*(\d*)\s*\d*:([\-\+\d]*)\s*\d*:([\-\+\d]*)[\s\+]*([\d\.]*)\s*'
        prediction_reg = re.compile(reg)    
        pred_file = open(self.weka_out, 'r')
        output = open(self.weka_out + '.parsed', 'w')
        instances = {}
        # Extract all the predictions in the file
        for line in pred_file:
            try:
                prediction = prediction_reg.match(line).groups()
            # AttributeError is thrown if line is not a preciction.
            except AttributeError:
                pass
            else:
                inst_number = prediction[0]
                if not inst_number in instances:
                    instances[inst_number] = [prediction]
                else:
                    instances[inst_number].append(prediction)
        # consolidate the instances into a single file
        for inst_num in sorted(instances):
            inst_set = instances[inst_num]
            # Skip instance if it has fewer then 10 predictions
            if len(inst_set) == 10:
                outline = self.instance_set2line(inst_set)
                output.write(outline + '\n')
        output.close()
        pred_file.close()
    
    def line_skip(self, line):
        '''checks if this is an irrelevant line.
        
        An irrelevant line is any line that does not contain predictions.
        '''
        # Add skip tests here as needed.
        skip_tests = [lambda x: x.startswith('==='), lambda x: x == '\n', \
                      lambda x: 'inst#' in x]
        return any(test(line) for test in skip_tests)

    def instance_set2line(self, pred_set):
        '''Consolidates all the instance tuples to a single line for the output.
        '''
        try:
            line = ['%s\t%s' % (actual, int(predicted)*float(prediction))\
                     for num, actual, predicted, prediction in pred_set]
        except ValueError:
           print '\nYou need to rerun', self.weka_out
           print 'Make sure your Weka command line is not set to report the'
           print 'distribution (-distribution) of classes'
           sys.exit()
        else:
            return '\t'.join(line)

class summarize_weka_output(parse_weka_output):
    '''Parses and calculates the AUC-ROC for a given weka output file
    '''
    def __init__(self, weka_out, invert = 0):
        self.weka_out = weka_out
        self.invert = invert
        # The AUC calculation script should be in the same directory
        self.auc_script = '%s/_cal_AUCROC.R' % os.path.dirname(
                                                   os.path.realpath(__file__))
        self.summarize_predictions()
        
    def summarize_predictions(self):
        '''Parses output and uses R to calculate the AUC-ROC'''
        
        self.parse_file()
        os.system('R --vanilla --slave --silent --args %s.parsed %s < %s > out.R' %
            (self.weka_out, self.invert, self.auc_script))

class batch_summary(object):
    '''Summarizes the outputs based on a grid search parameter file.
    '''
    
    def __init__(self, parameter_file, overwrite, invert):
        self.parameter_file = parameter_file
        # Set up the overwrite function based on user input.
        if not overwrite:
            # returns false if the file already exists (i.e. don't overwrite)
            self.overwrite = lambda x: not os.path.exists(x + '.parsed.AUC')
        elif overwrite:
            # Returns true to everything (i.e. overwrite any file)
            self.overwrite = lambda x: True
        # Variable that determines if the prediction and observations
        # should be inverted. Usefull if you want to calculate an AUC-ROC
        # on the negative class.
        self.invert = invert
        self.batch_summary()      
    
    def batch_summary(self):
        '''Summarizes a batch of outputs.
        '''
        cc_dict = parse_command_file(self.parameter_file)
        # Look through all the weka runs set up in the paramater file
        # And parse all possible outputs.
        weka_output_files = []
        print 'parsing weka output files'
        for weka_out, par_tuple in self.iter_weka_output(cc_dict):
            if check_file(weka_out).file_good:
                if not self.overwrite(weka_out):
                    pass
                else:
                    weka_output_files.append(weka_out)
                    parse_weka_output(weka_out, self.invert)

        print 'calculating AUC-ROCs'
        self.batch_auc_calculation(weka_output_files)
        self.write_summary_file(cc_dict)

    def iter_weka_output(self, cc_dict):
        '''Iterator that yeilds weka_output names from a parsed parameter file.
        '''
        for description, command_par in cc_dict.iteritems():
            command, par_list = command_par
            for par_tuple in par_list:
                yield '%s.%s' % (description, '-'.join(par_tuple)), par_tuple

    def batch_auc_calculation(self, weka_output_files):
        '''Runs an R script to calculate the AUCROC on all the parsed outputs.
        '''
        auc_script = '%s/_batch_cal_AUCROC.R' % os.path.dirname(
                                           os.path.realpath(__file__))
        Rcmd = 'R --vanilla --slave --silent --args %s < %s > out.R' 
        parsed_output = ['%s.parsed' % f for f in weka_output_files]
        # Submit the R command with the parsed files.
        os.system(Rcmd % (' '.join(parsed_output), auc_script))
    
    def write_summary_file(self, cc_dict):
        '''Summarizes the outputs from all the AUCROC files.
        '''
        output = open(self.parameter_file + '.summary', 'w')
        for weka_out, par_tuple in self.iter_weka_output(cc_dict):
            if check_file(weka_out).file_good:
                AUC_line = self.extract_auc(weka_out)
                output.write('%s\t%s\n' % (AUC_line, '\t'.join(par_tuple)))
        output.close()
        
    def extract_auc(self, weka_out):
        '''Extracts the mean auc and its standard error for an output file
        '''
        auc_file = open(weka_out + '.parsed.AUC', 'r')
        auc = auc_file.readline().strip()
        auc_file.close()
        
        return '\t'.join((weka_out, auc))

def main():
    '''Checks for failed jobs, '''
    
    try:
        par = sys.argv[1]
    # Print the doc string if no input is specified.
    except IndexError:
        print __doc__
        sys.exit()
    auc_script = \
        '/mnt/home/seddonal/scripts/11_phenotype_prediction/_cal_AUCROC.R'
    single = False
    overwrite = False
    invert = 0
    cc_dict = parse_command_file(par)
    try:
        sys.argv[2]
    except IndexError:
        pass
    else:
        # Parse the options if they are specified
        for i, value in enumerate(sys.argv[2:]):
            if value == "single":
                single = value
            elif value == "overwrite":
                overwrite = value
            elif value == "invert":
                invert = 1
    if not single:
        batch_summary(par, overwrite, invert)
    elif single == 'single':
        summarize_weka_output(par)
    else:
        print "Include 'single' at the end of the command if you want to look"
        print "at a single output."
        print "Otherwise, leave this space blank to do a batch summary."

    
if __name__ == "__main__":
    main()
        
