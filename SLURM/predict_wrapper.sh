#!/bin/bash
SITES="OSBS JERC MLBS BLAN UKFS SCBI BART HARV SERC GRSM NIWO RMNP WREF SJER BONA DEJU TREE STEI UNDE DELA LENO CLBJ TEAK SOAP YELL OSBS JERC TALL"
#SITES="UNDE OSBS"
for SITE in $SITES; do
echo "${SITE}"
sbatch SLURM/predict.sh ${SITE}
sleep 1 # pause to be kind to the scheduler
done
