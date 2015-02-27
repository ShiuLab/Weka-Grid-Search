'''Parses the weka output predictions for easy use with ROCR.

INPUT
weka_output_parser.py [parameter file OR single prediction file] [OPTIONS]

OPTIONS
    single - Use this options if you are looking at a single prediciton file
    invert - Use this option if you want your negative class to be the positive
        class, and vice-versa
    maxF - Use this option if you would like a summary of the max F-measure 
        instead of the AUC-ROC
    failed - Run the check_output function to compile the command lines of 
        failed jobs.
    Include as many of the options as you wish to the end of the command

Assumes that you used 10-fold crosss validation. Removes instances that have
fewer then 10 cross validations. You can modify the output parser in this 
script and the R script for caluclateing AUC or F measures.

OUTPUT
Parsed prediction (.parsed) and AUC (.AUC) files for each prediction file.
Additionally, you get a .summary file that summarizes all the runs.
'''

import sys
import os
import re
import subprocess

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
        
        # NOTE: Switching this to a function that uses basic
        # string methods may speed up performance.
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
    
    def __init__(self, parameter_file, overwrite, invert, measure='AUC'):
        self.parameter_file = os.path.abspath(parameter_file)
        self.out_dir = os.path.split(self.parameter_file)[0]
        # Set up the overwrite function based on user input.
        if not overwrite:
            # returns false if the file already exists (i.e. don't overwrite)
            self.file_extension = '.parsed.%s' % measure
            self.overwrite = lambda x: not os.path.exists(x+self.file_extension)
        elif overwrite:
            # Returns true to everything (i.e. overwrite any file)
            self.overwrite = lambda x: True
        # Variable that determines if the prediction and observations
        # should be inverted. Usefull if you want to calculate an AUC-ROC
        # on the negative class.
        self.measure = measure
        self.invert = invert
        # This funtion performs the summary on the outputs.
        self.batch_summary()      
    
    def batch_summary(self):
        '''Summarizes a batch of outputs.
        
        The "meat and potatoes" of this parsing script.
        '''
        cc_dict = parse_command_file(self.parameter_file)
        # Look through all the weka runs set up in the paramater file
        # And parse all possible outputs.
        weka_output_files = []
        
        print 'parsing weka output files'
        # converts output to an R digestible format.
        # par_tuple is the tuple of parameters from the grid search that are
        # used in the name of the file.
        for index, weka_out, par_tuple in self.iter_weka_output(cc_dict):
            weka_out = os.path.join(self.out_dir, weka_out)
            # Check if the file is in the correct format.
            if check_file(weka_out).file_good:
                if not self.overwrite(weka_out):
                    pass
                else:
                    # Parse the output from Weka's format to a matrix.
                    weka_output_files.append(weka_out)
                    parse_weka_output(weka_out, self.invert)
            if index % 50==0:
                print '... %s files so far ...' % index
        
        # Convert the performance measure on all the parsed outputs.
        print 'calculating %ss' % self.measure
        self.batch_auc_calculation(weka_output_files)
        print 'finished calculating %ss' % self.measure
        self.write_summary_file(cc_dict)

    def iter_weka_output(self, cc_dict):
        '''Iterator that yeilds weka_output names from a parsed parameter file.
        '''
        for description, command_par in cc_dict.iteritems():
            command, par_list = command_par
            for index, par_tuple in enumerate(par_list):
                yield index,'%s.%s'%(description, '-'.join(par_tuple)),par_tuple

    def batch_auc_calculation(self, weka_output_files):
        '''Runs an R script to calculate the AUCROC on all the parsed outputs.
        '''
        # Assumses that the R measure script is tin the same directory.
        script_dir = os.path.dirname(os.path.realpath(__file__))
        measure_script = '%s/_batch_cal_%s.R' % (script_dir, self.measure)
        Rcmd = 'R --vanilla --slave --args %s < %s > out.R 2> error.R' 
        parsed_output = ['%s.parsed' % f for f in weka_output_files]
        # Submit the R command with the parsed files.        
        Rcmd = Rcmd % (' '.join(parsed_output), measure_script)
        output = open('%s.Rcmd.sh' % self.parameter_file, 'w')
        output.write(Rcmd)
        output.close()
        
        os.system('sh %s' % '%s.Rcmd.sh' % self.parameter_file)
        
        #print Rcmd

        # This call to os.system has inexplicable stopped working. Thus, I 
        # have created an inelegant work around involving the creation of a 
        # shell script file and running that script with os.system
        # I think that the was a cap of some sort on how long of a command you
        # can use with os.system, and that is causing a problem.
        #exit_stat = os.system(Rcmd)
        #exit_stat = subprocess.check_call(Rcmd.split(' '))
        #print exit_stat
        
    def write_summary_file(self, cc_dict):
        '''Summarizes the outputs from all the AUCROC files.
        '''
        output = open(self.parameter_file + '.summary.%s' % self.measure, 'w')
        for index, weka_out, par_tuple in self.iter_weka_output(cc_dict):
            weka_out = os.path.join(self.out_dir, weka_out)
            if check_file(weka_out).file_good:
                try:
                    measure_line = self.extract_measure(weka_out)
                except IOError:
                    print weka_out + self.file_extension, 'not found'
                else:
                    output.write('%s\t%s\n' % (measure_line,
                                               '\t'.join(par_tuple)))
        output.close()
        
    def extract_measure(self, weka_out):
        '''Extracts the mean auc and its standard error for an output file
        '''
        measure_file = open(weka_out + self.file_extension, 'r')
        measure = measure_file.readline().strip()
        measure_file.close()
        
        return '\t'.join((weka_out, measure))

def main():
    '''Parses and summarizes all available weka outputs from a grid search'''
    
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
    measure = 'AUC'
    cc_dict = parse_command_file(par)
    # Get additional parameters
    try:
        sys.argv[2]
    except IndexError:
        pass
    else:
        # Parse the optional parameters if they are specified
        for i, value in enumerate(sys.argv[2:]):
            if value == "single":
                single = value
            elif value == "overwrite":
                overwrite = value
            elif value == "invert":
                invert = 1
            elif value == "maxF":
                measure = "maxF"
            elif value == "AUC":
                measure = "AUC"
            elif value == "failed":
                check_output()
    # Summarize all available 
    if not single:
        batch_summary(par, overwrite, invert, measure)
    elif single == 'single':
        summarize_weka_output(par)
    else:
        print "Include 'single' at the end of the command if you want to look"
        print "at a single output."
        print "Otherwise, leave this space blank to do a batch summary."

    
if __name__ == "__main__":
    
    main()
    
        
