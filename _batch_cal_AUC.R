
library("ROCR", lib.loc='/mnt/home/seddonal/R/library/')
cArgs = commandArgs(trailingOnly=TRUE)

get_perf_AUC <- function(t) 

    {
   ncol = dim(t)[2]
   pred <- prediction( t[,seq(2,ncol,2)],t[,seq(1,ncol,2)])
   perf <- performance(pred, "auc")
   }

calculate_auc <- function(prefile){
    file=read.table(prefile, sep = '\t', header = FALSE)
    folds=dim(file)[2]/2       
    perf <- get_perf_AUC(file)

    # Get the AUC-ROC for each fold
    c <- c()
    for(i in seq(1,folds,1)) {
        c <- c(c, as.numeric(perf@y.values[i]))
    }

    auc_mean <- mean(c)
    auc_standard_error <- sd(c)/sqrt(folds)

    write.table(paste(auc_mean, auc_standard_error, sep = '\t')
                , file=paste(prefile, 'AUC', sep=".")
                , col.names = FALSE, row.names = FALSE
                , quote = FALSE
                )
}

for(prefile in cArgs){
    calculate_auc(prefile)
    }
