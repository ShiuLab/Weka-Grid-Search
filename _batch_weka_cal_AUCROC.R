library("ROCR", lib.loc='/mnt/home/seddonal/R/library/')
cArgs = commandArgs(trailingOnly = TRUE)
#prefile = cArgs[5]

calculate_performance <- function(prefile){
    file=read.table(prefile, sep = '\t', header = FALSE)
    pre = file$V3
    obs = file$V2

    pred <- prediction(pre,obs)
    # Calculate AUC-ROC
    perf <- performance(pred,"auc")
    write.table(slot(perf,"y.values"),
                file=paste(prefile,"ROC",sep="."),
                quote=F,row.names=FALSE,col.names=FALSE)
    # Calculate f-measure
    perf <- performance(pred,"f")
    x=slot(perf,"y.values")
    y=max(unlist(x),na.rm=TRUE)
    write.table(y,
                file=paste(prefile,"F1",sep="."),
                quote=F,row.names=FALSE,col.names=FALSE)
    # Calculate accuracy
    perf <- performance(pred,"acc")
    x=slot(perf,"y.values")
    y=max(unlist(x),na.rm=TRUE)
    write.table(y,
                file=paste(prefile,"ACC",sep="."),
                quote=F,row.names=FALSE,col.names=FALSE)
}

for(prefile in cArgs){
    calculate_performance(prefile)
}

