#!/usr/bin/env python
import sys
import os
sys.path.append(os.environ['DEEPMITOROOT'])
import argparse
import numpy
from Bio import SeqIO

import deepmitolib.deepmitoconfig as cfg
from deepmitolib.cnn import MultiCNNWrapper
from deepmitolib.utils import encode, annotToText
from deepmitolib.workenv import TemporaryEnv
from deepmitolib.blast import runPsiBlast

def main():
  DESC = "DeepMito: Predictor of protein submitochondrial localization"
  parser = argparse.ArgumentParser(description=DESC)
  parser.add_argument("-f", "--fasta",
                      help = "The input FASTA file name",
                      dest = "fasta", required = True)
  parser.add_argument("-d", "--dbfile",
                      help = "The PSIBLAST DB file",
                      dest = "dbfile", required= True)

  parser.add_argument("-o", "--outf",
                      help = "The output tabular file",
                      dest = "outf", required = True)
  ns = parser.parse_args()

  workEnv = TemporaryEnv()

  multiModel = MultiCNNWrapper(cfg.MODELS)
  annotation = {}

  for sequence in SeqIO.parse(ns.fasta, 'fasta'):
    sequence.id = sequence.id.replace("|","_")
    fastaSeq  = workEnv.createFile(sequence.id+".", ".fasta")
    SeqIO.write([sequence], fastaSeq, 'fasta')
    pssmFile, _ = runPsiBlast(sequence.id, ns.dbfile, fastaSeq, workEnv)
    acc, X = encode(fastaSeq, cfg.AAIDX10, pssmFile)
    pred   = multiModel.predict(X)
    cc = cfg.GOMAP[numpy.argmax(pred)]
    score = round(numpy.max(pred),2)
    annotation[sequence.id] = {'sequence': {'len': len(str(sequence.seq)), 'sequence': str(sequence.seq)}, 
                               'goa': [cc], 'features': [], 'score': score, 'second': '-', 'alt_score': 0.0}
  
  annotToText(annotation, ns.outf)
  workEnv.destroy()

if __name__ == "__main__":
  main()  
