'''Flexible script for creating grid search command lines and checking errors.

INPUT
grid_search_cc.py [Parameter and commandline file] 

The command line file should be in the following format:
    
    desc#Description of the test
    x1 x2 x3 ... xn
    y1 y2 ... ym
     :  :  :   :
    k1 k2 ... kp
    command#[Command line with %s in each location that needs a parameter]
    end#

Each row should is a space delimited list of all values you want for one 
parameter. You can have an arbitray number of possible values, and an arbitrary
number of parameters. The rows should be in the order that they will be plugged
into the command line.

The command line row should always start with "command#"

OUTPUT
A .run_CC file that contains all the files to run, and the .failed.run_cc file
that conatins all the jobs that failed. When you first run the script, both 
files should be identical.
'''

import sys
import os
import itertools
import re

def row2list(row):
    '''Converts space-delimited lines to lists.
    
    Used to pull out parameters that you are grid searching.
    '''
    l = []
    for i in row.strip().split(' '):
        l.append(i)
    return l

def create_cost_matricies(low, high, by, name):
    '''Creates 2x2 cost matricies through combinations from low to high.
    
    Only changes weights in top-right and bottom-left. Also includes 1, 1.
    '''
    weight_values = range(int(low), int(high)+1, int(by))
    weight_perm = list(itertools.permutations(weight_values, 2))
    weight_perm.append((1, 1))
    n = 0
    cost_mat_list = []
    for comb in weight_perm:
        n += 1
        out_name = name + "%sTO%s.cost" % comb
        if not os.path.isfile(out_name):
            output = open(out_name, 'w')
            output.write('% Rows\tColumns\n2\t2\n% Matrix elements\n')
            output.write('0.0\t%s\n%s\t0.0' % comb)
            output.close()
        elif os.path.isfile(out_name):
            print 'Found', out_name
        cost_mat_list.append(out_name)
    return cost_mat_list

def parse_commands(par_file):
    '''Parses the command file that you import
    
    Returns the command line to be used, and the list of tuples of all 
    possible parameter combinations.
    '''    
    row_list = []
    command  = None
    tamo = arff = 'absent'
    for row in par_file:
        if row.startswith('end'):
            break
        if row.startswith("command"):
            command = row.strip().split('#')[1]
        elif row.startswith("tamo"):
            tamo = row.strip().split('#')[1]
        elif row.startswith("arff"):
            arff = row.strip().split('#')[1]
        elif row.startswith("cost"):
            low, high, by, name = row.strip().split('#')[1].split(',')
            row_list.append(create_cost_matricies(low, high, by, name))
        else:
            row_list.append(row2list(row))
    par_list = list(itertools.product(*row_list))
    if command == None:
        raise NameError("Make sure that you parameter file has a proper \
command line. (Should look like command#java weka.classi...)") 
    # Insert the tamo if it was specified in a seperate line.
    if not tamo == "absent":
        command = command.replace('[TAMO]', tamo)
    if not arff == "absent":    
        command = command.replace('[ARFF]', arff)
    return command, par_list

def parse_command_file(par):
    '''Parses a command file.
    
    cc_dict = {description: (command, par_list)}
    '''
    
    par_file = open(par, 'r')
    cc_dict = {}
    for line in par_file:
        if line.startswith("desc#"):
            description = line.strip().split('#')[1]
            cc_dict[description] = parse_commands(par_file)
    par_file.close()
    return cc_dict
        
def removeSpacesReturnLst(line):
    line = line.strip()
    while "  " in line:
        line = line.replace("  "," ")
    lineLst = line.split(" ")
    return lineLst

def summarize_weka_out(weka_out, output, par_tuple):
    '''Summarize a weka output file
    
    Originally writen by Johnny Lloyd and converted to a function by Alex Seddon
    '''
    inp = open(weka_out, 'r')
    inCV = 0
    afterDetailed = 0
    detailedCnt = 0
    afterConfusion = 0
    confusionCnt = 0
    for line in inp:
        if line.startswith("=== Stratified cross-validation ==="):
            inCV = 1
        if inCV == 1:
            if line.startswith("Correctly Classified Instances"):
                lineLst = removeSpacesReturnLst(line)
                accuracy = lineLst[-2]
            if line.startswith("Kappa statistic"):
                lineLst = removeSpacesReturnLst(line)
                kappa = lineLst[-1]
            
            if afterDetailed == 1:
                if detailedCnt == 2:
                    lineLst = removeSpacesReturnLst(line)
                    tpRate = lineLst[0]
                    fpRate = lineLst[1]
                    precision = lineLst[2]
                    recall = lineLst[3]
                    fMeasure = lineLst[4]
                    aucRoc = lineLst[5]
                detailedCnt +=1
            if line.startswith("=== Detailed Accuracy By Class ==="):
                afterDetailed = 1
            
            if afterConfusion == 1:
                if confusionCnt == 2:
                    lineLst = removeSpacesReturnLst(line)
                    tp = lineLst[0]
                    fn = lineLst[1]
                if confusionCnt == 3:
                    lineLst = removeSpacesReturnLst(line)
                    fp = lineLst[0]
                    tn = lineLst[1]
                confusionCnt += 1
            if line.startswith("=== Confusion Matrix ==="):
                afterConfusion = 1
    t = (precision,recall,fMeasure,aucRoc,tpRate,fpRate,tp,fn,fp,tn,kappa,\
         accuracy)
    outline = '\t'.join(par_tuple) + '\t%s\t%s\t%s\t%s\t%s\t%s\t[%s %s; %s %s]\t%s\t%s\n' % t
    
    output.write(outline)
    inp.close()

def main():
    
    try:
        par = sys.argv[1]
    except IndexError:
        print __doc__
        sys.exit()
    try:
        out_dir = os.path.abspath(sys.argv[2])
    except IndexError:
        out_dir = os.path.abspath(os.curdir)
    # Parse the command line file
    cc_dict = parse_command_file(par)
    print 'Creating the following Weka runs: %s' % ', '.join(cc_dict.keys())
    # Create a command lines for each command line set
    output = open('%s.runcc' % par, 'w')
    # Look through each individual command line set
    for description, command_par in cc_dict.iteritems():
        # Extract the command and parameter list, and write output.
        command, par_list = command_par
        for par_tuple in par_list:
            outline = command % par_tuple + \
            ' > %s/%s.%s\n' % (out_dir, description, '-'.join(par_tuple))
            output.write(outline)
    output.close()

class check_file(object):
    
    def __init__(self, weka_out):
        self.weka_out = weka_out
        self.function_list = [self.file_exists, self.non_empty, 
                          self.contains_predictions]
        # If all functions are true, the file is good.
        self.file_good = all(function() for function in self.function_list)

    
    def file_exists(self):
        '''Checks that a file exits.
        '''
        return os.path.isfile(self.weka_out)
    
    def non_empty(self):
        '''Checks that a file is non-empty.
        '''
        # Empty files will have a size of 0 (== False).
        return os.path.getsize(self.weka_out)

    def contains_predictions(self):
        '''Checks that the file contains predictions.
        ''' 
        reg = r'\s*(\d*)\s*\d*:([\-\+\d]*)\s*\d*:([\-\+\d]*)[\s\+]*([\d\.]*)\s*'
        prediction_reg = re.compile(reg)
        weka_file = open(self.weka_out)
        # This for loop short circuits after seeing the first prediction
        for line in weka_file:
            # When a file matches the prediction regural expression, then 
            # we can assume that the file has the predictions.
            if not prediction_reg.match(line) == None:
                weka_file.close()
                return True
        weka_file.close()
        return False

def check_output():
    '''Checks for failed jobs, '''
    
    par = os.path.abspath(sys.argv[1])
    out_dir = os.path.split(par)[0]
    cc_dict = parse_command_file(par)
    failed_output = open('%s.failed.runcc' % par, 'w')
    # Look through all the weka runs set up in the paramater file.
    for description, command_par in cc_dict.iteritems():
        command, par_list = command_par
        for par_tuple in par_list:
            weka_out = '%s/%s.%s' % (out_dir, description, '-'.join(par_tuple))
            # Check that file is present and non-empty
            if not check_file(weka_out).file_good:
                failed_output.write(command % par_tuple+' > %s\n' % (weka_out))
    failed_output.close()

if __name__ == "__main__":
    main()
    check_output()

