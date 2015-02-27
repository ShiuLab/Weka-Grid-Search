#library("caTools")
#library("grid")
#library("KernSmooth")
#library("gtools")
#library("gdata")
#library("gplots")
library("ROCR", lib.loc='/mnt/home/seddonal/R/library/')
cArgs = commandArgs(trailingOnly=TRUE)

get_perf_maxF <- function(t) 
  
{
  ncol = dim(t)[2]
  pred <- prediction( t[,seq(2,ncol,2)],t[,seq(1,ncol,2)])
  folds <- ncol/2
  perf <- performance(pred, "f")
  c <- c()
  # get the max AUC-ROCs
  for(i in 1:folds){
    Fmeasure <- unlist(perf@y.values[i])
    Fmax <- max(Fmeasure, na.rm=T)
    c <- c(c, Fmax)
  }
  c
  
}

calculate_F <- function(prefile){
    file=read.table(prefile, sep = '\t', header = FALSE)
    # You can choose to invert the predictions and observations.
    # This allows you to calculate an AUC-ROC based on the negative class.
    # An invert value of 1 allows you to do this

    maxF <- get_perf_maxF(file)
    maxF_mean <- mean(maxF)
    maxF_standard_error <- sd(maxF)/length(maxF)

    write.table(paste(maxF_mean, maxF_standard_error, sep = '\t')
                , file=paste(prefile, 'maxF', sep=".")
                , col.names = FALSE, row.names = FALSE
                , quote = FALSE
                )
}

for(prefile in cArgs){
    calculate_F(prefile)
    }
