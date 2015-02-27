These scripts offer a wrapper for running a grid search using weka
classifiers. It is fairly flexible, but it relies on the use of 10 fold
cross validation to parse the results.

Requires the ROCR package and an existing Weka instalation.

Please visit http://shiulab.plantbiology.msu.edu/wiki/index.php/Weka_Grid_Search
For a more fleshed out protocol.

#Basic pipeline
1. Create a parameter file that will be used to create commands for 
   sub runs. It looks like this.

desc#output_file_description
arff#/full/path/to/arff.file
0.29 0.57 1 1.75 3.5 5.25 7
0.03125 0.125 0.5 2 8 32 128 512 2048 8192 32768
0.00048828125 0.001953125 0.0078125 0.03125 0.125 0.5 2 8
command#java weka.classifiers.functions.SMO -t [ARFF] -c last -p 0 -C %s -B -K 2 -G %s
end#

put the information in a file called output_file_description

Notice that [ARFF] will be replaced with the arff path you specify and that 
%s will be replaced by the parameters you specify.

2. Create a file of command lines.
python grid_search_cc.py output_file_description

It will output a file ending with .runcc, which you can use with qsub_hpc.py
(not in this repository) to run the command lines using the PBS scheduler.
A .failed.runcc file will also be created. This cript serves the dual
purposes of creating commands and checking for failed jobs.

After the first batch of jobs run, check them for errors and then run
any jobs in the .failed.runcc file. Do this untill .failed.runcc comes back
empty.

3. Parse the outputs
python weka_output_parser.py output_file_description

Check the .summary file for your best performing model.

You can use script_plot_AUC_ROC.R to make PR and ROC curves.
