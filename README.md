# Introduction
These scripts offer a wrapper for running a grid search using Weka
classifiers.

While we could have used Java to do grid searches with Weka, our lab is
primarily a Python lab. This pipeline also use the more powerful plotting
functions available through the `R` package `ROCR`.

Requires the `ROCR` for `R` package and an existing `Weka` instalation.

* For more information about the purpose behind grid searching, please visit
   this [article](http://en.wikipedia.org/wiki/Hyperparameter_optimization#Grid_search) 
   on Wikipedia.
* Please visit the fleshed out [protocol](http://shiulab.plantbiology.msu.edu/wiki/index.php/Weka_Grid_Search)
on our lab website for more details on this pipeline.

# Grid Search Pipeline
The pipeline involves.


1. Using `grid_search_cc.py` to create a file containing command lines for
   all possible parameter combinations specified for the grid search.
1. Using `qsub_hpc.py` - not included here - to run the command lines as jobs.
1. Using `grid_search_cc.py` to check for failed jobs, and rerunning as
   specific in 1. and 2. untill all jobs complete.
1. Using `weka_output_parser.py` to check the performance of all the parameter
   combinations.

## Create a parameter file that will be used to create commands for 
   sub runs.

The parameter file should contain the following:


1. A basic file name that will be used for all the output files. I like to 
    use the same name as the parameter file to keep things consistent. This
    is formated as `desc#basic_file_name` in the parameter file.
2. The full path to the Weka formater ARFF file. This is formated as
    `arff#/full/path/to/file.arff` in the parameter file. Note that this
    is optional, and you can include the ARFF file in the command line as
    described bellow.
    * This is for you convinience when you want to perform the same grid 
    search on several ARFF files.
3. The Weka command line which you want to perform the grid search with. Please
    see the example bellow.
    * You need to include:
        * Place holders for the grid search parameters using Python's `%s` string
        formating.
        * If you used the `arff#` option, then you will need to include [ARFF]
        in place of the ARFF file path in the command line.
4. One line for each grid search parameter, with all possible values of this
    parameter listed out in space delimited format.
5. A line to denote that all parameters are specified. This is coded as 
    `end#` in the parameter file.


Here is a full example. It sets up an SVM grid search that adjusts parameters
for the C constant and gamma of the RBF kernel.
    
```
desc#basic_file_name
arff#/full/path/to/file.arff
command#java weka.classifiers.functions.SMO -t [ARFF] -c last -p 0 -C %s -B -K 2 -G %s
0.1 1 10 100
0.1 0.2 0.5 1.0
end#
```

Note that the possible values for `-C` are in the first line after `command#` 
and the possible values for `-G` are in the second line.
I will call this file `parameter_file` for the remainder of the protocol.

## Create a file of command lines.
Use the following command:
`python grid_search_cc.py parameter_file`

It will output a file ending with .runcc, which you can use with qsub_hpc.py
- not in this repository -  to run the command lines using the PBS scheduler.
A .failed.runcc file will also be created. This script serves the dual
purposes of creating commands and checking for failed jobs.

## Check for failed jobs and rerun

After the first batch of jobs run, check them for errors using the same 
command as the previous step.
`python grid_search_cc.py basic_file_name`

Then, run any jobs in the .failed.runcc file using qsub_hpc.py. Do this untill 
.failed.runcc comes back empty.

## Parse the outputs
Use the following command:
`python weka_output_parser.py parameter_file`

By default, the script calculates AUC-ROC.

Check the .summary.AUC file for your best performing model. I do this
By sorting the the file by the second column using the Unix commands:
`sort -gk 2 paramter_file.summary.AUC | tail -n` 

## Plot curves for the best model.
You can use script_plot_AUC_ROC.R to make PR and ROC curves.
