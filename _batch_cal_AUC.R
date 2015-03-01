# Takes an arbitrary list set of parsed files and cacluates AUC-ROCs
library("ROCR", lib.loc='/mnt/home/seddonal/R/library/')
cArgs = commandArgs(trailingOnly=TRUE)

# Gets the AUC-ROC values for a file.
get_perf_AUC <- function(t)

    {
   ncol = dim(t)[2]
   pred <- prediction( t[,seq(2,ncol,2)],t[,seq(1,ncol,2)])
   perf <- performance(pred, "auc")
   }

# Calculates the standard error for AUC-ROCs
calculate_auc <- function(prefile){
    file=read.table(prefile, sep = '\t', header = FALSE)
    # You can choose to invert the predictions and observations.
    # This allows you to calculate an AUC-ROC based on the negative class.
    # An invert value of 1 allows you to do this
       
    perf <- get_perf_AUC(file)

    c <- c()
    for(i in 1:10){c <- c(c, as.numeric(perf@y.values[i]))}

    auc_mean <- mean(c)
    auc_standard_error <- sd(c)/sqrt(10)

    write.table(paste(auc_mean, auc_standard_error, sep = '\t')
                , file=paste(prefile, 'AUC', sep=".")
                , col.names = FALSE, row.names = FALSE
                , quote = FALSE
                )
}

for(prefile in cArgs){
    print(prefile)
    calculate_auc(prefile)
    }
