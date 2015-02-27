# USAGE
# R [OUTPUT NAME] [PREDICTIONs 1] [PRED. 1 Title] ... < script_plot_AUC_ROC.R
#load the package
library(ROCR) 
cArgs = commandArgs(trailingOnly = TRUE)

# Get the output file name
output_name <- cArgs[1]

#Get all of the summary files
files <- c() # The file object
title <- c() # The title for the object
for(i in seq(2, length(cArgs), 2)){
    files <- c(files, cArgs[i])
    title <- c(title, cArgs[i+1])
}

#This function creates the performance object necessary for makeing an 
#precision-recall curve.
get_perf_PR <- function(t) 
  
{
  ncol = dim(t)[2]
  pred <- prediction( t[,seq(2,ncol,2)],t[,seq(1,ncol,2)])
  perf <- performance(pred, "prec", "rec")
}

#This function sets up the performance object for an ROC curve.
get_perf_ROC <- function(t) 
  
{
  ncol = dim(t)[2]
  pred <- prediction( t[,seq(2,ncol,2)],t[,seq(1,ncol,2)])
  perf <- performance(pred, "tpr", "fpr")
}

# Function that creates plots for all files
plot_curves <- function(files, title, FUNCTION, legend_location){
    # Plot the first file
    print(files[1])
    perf <- FUNCTION(read.table(files[1], header=FALSE))
    plot(perf, avg='vertical', spread.estimate='stderror', 
         ylim=c(0,1), col = colors[1], lwd=3)

    # Add all subsequent files if available.
    if(length(files) > 1){
        for(i in seq(2, length(files), 1)){
            print(files[i])
            perf <- FUNCTION(read.table(files[i],  header=FALSE))
            plot(perf, avg='vertical', spread.estimate='stderror', 
                 ylim=c(0,1), col = colors[i], add=TRUE, lwd=3)
        }
    }
    legend(legend_location, title, lwd=3, col = colors, bty = 'n')
}

# Set up color scheme
colors <- rainbow(length(files))

# This block outputs a PDF of the precision-recall curve, complete with a 
# legend.
pdf(paste(paste(output_name, 'PR', sep='_'), 'pdf', sep = '.')) 
plot_curves(files, title, get_perf_PR, "topright")
dev.off()

# This block outputs a PDF of the ROC curve, complete with a legend
pdf(paste(paste(output_name, 'ROC', sep='_'), 'pdf', sep = '.')) 
plot_curves(files, title, get_perf_ROC, "bottomright")
dev.off() 

# Create a log file to keep a record of the command line.
write.table(x = paste(commandArgs(), sep=' '),
            file = paste(output_name, 'log', sep = '.'))
