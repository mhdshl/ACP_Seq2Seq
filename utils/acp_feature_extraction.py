# -*- coding: utf-8 -*-
"""ACP_feature_extraction.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1022ePonaY_0jEiO3ZlF1oPJMQ9b43xL-
"""

## Load useful packages
import sys, os, re, gc
from scipy.io import savemat
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from keras import optimizers
from tensorflow.keras.utils import to_categorical
from collections import Counter
import matplotlib.pyplot as plt
from keras.models import Model
from keras.layers import Input, Dense, BatchNormalization, Dropout
from keras import optimizers
from keras import metrics
from sklearn.metrics import confusion_matrix
from sklearn.metrics import classification_report, accuracy_score, matthews_corrcoef, balanced_accuracy_score, precision_recall_fscore_support
from sklearn.metrics import auc, average_precision_score, precision_recall_curve, roc_curve

from keras import backend as K
from keras.models import load_model
from keras.callbacks import EarlyStopping
from keras.callbacks import ModelCheckpoint
from random import sample
from imblearn.over_sampling import SMOTE

"""#CKSAAP Features

### Use the command like this (use github location with wget)
data_path = '/content/drive/MyDrive/ACP_Seq2Seq/Datasets/acp740.txt'

[DataX, LabelY] = Convert_Seq2CKSAAP(prepare_feature_for_CKSAAP(data_path), gap=8)
"""

def prepare_feature_for_CKSAAP(data_path):
    # path = r"acp740.txt"
    new_list=[]
    seq_list=[]
    label = []
    lis = []
    interaction_pair = {}
    RNA_seq_dict = {}
    protein_seq_dict = {}
    protein_index = 0
    with open(data_path, 'r') as fp:
        for line in fp:
            if line[0] == '>':
                values = line[1:].strip().split('|')
                label_temp = values[1]
                proteinName = values[0]
                proteinName_1=proteinName.split("_")
                new_list.append(proteinName_1[0])
    #             print(new_list)

                if label_temp == '1':
                    label.append(1)
                else:
                    label.append(0)
            else:
                seq = line[:-1]
                seq_list.append(seq)
        for i, item in enumerate(new_list):
            lis.append([item, seq_list[i]])

    return lis

def Convert_Seq2CKSAAP(train_seq, gap=8):
  cksaapfea = []
  seq_label = []
  for sseq in train_seq:
    temp= CKSAAP([sseq], gap)
    cksaapfea.append(temp[1][1:])
    seq_label.append(sseq[0])

  x = np.array(cksaapfea)
  y = np.array(seq_label)
  y[y=='ACP']=0
  y[y=='non-ACP']=1
  y = to_categorical(y)
  print('num pos:', sum(y[:,0]==1), 'num neg:', sum(y[:,0]==0))
  return x,y

def minSequenceLength(fastas):
    minLen = 10000
    for i in fastas:
        if minLen > len(i[1]):
            minLen = len(i[1])
    return minLen

def CKSAAP(fastas, gap=5, **kw):
    if gap < 0:
        print('Error: the gap should be equal or greater than zero' + '\n\n')
        return 0

    if minSequenceLength(fastas) < gap+2:
        print('Error: all the sequence length should be larger than the (gap value) + 2 = ' + str(gap+2) + '\n' + 'Current sequence length ='  + str(minSequenceLength(fastas)) + '\n\n')
        return 0

    AA = 'ACDEFGHIKLMNPQRSTVWY'
    encodings = []
    aaPairs = []
    for aa1 in AA:
        for aa2 in AA:
            aaPairs.append(aa1 + aa2)
    header = ['#']
    for g in range(gap+1):
        for aa in aaPairs:
            header.append(aa + '.gap' + str(g))
    encodings.append(header)
    for i in fastas:
        name, sequence = i[0], i[1]
        code = [name]
        for g in range(gap+1):
            myDict = {}
            for pair in aaPairs:
                myDict[pair] = 0
            sum = 0
            for index1 in range(len(sequence)):
                index2 = index1 + g + 1
                if index1 < len(sequence) and index2 < len(sequence) and sequence[index1] in AA and sequence[index2] in AA:
                    myDict[sequence[index1] + sequence[index2]] = myDict[sequence[index1] + sequence[index2]] + 1
                    sum = sum + 1
            for pair in aaPairs:
                code.append(myDict[pair] / sum)
        encodings.append(code)
    return encodings

"""# Features for MHCNN

## use this to read from github source

path_to_file = tf.keras.utils.get_file('untrained_gen_ACP.txt', 'https://raw.githubusercontent.com/mhdshl/ACP_Seq2Seq/main/Data/untrained_gen_ACP.txt')

## and use these to generate features for MHCNN

X1test = numeric(dBPF) --- BPF features

X2test = numeric(dBIT) --- dBIT features

X3test = numeric(dBLOSUM) --- dBLOSUM features



"""

paddingLength = 25
def check(seq):
    seq  =set(seq)
    proteinElements = set('ACDEFGHIKLMNPQRSTVWY') # Except: BOJUXZ

    if proteinElements >= seq:
        return True
    else:
        return False
    #end-if
#end-def

def readFASTAs(fileName):

    '''
    :param fileName:
    :return: genome sequences
    '''
    with open(fileName, 'r') as file:
        v = []
        genome = ''
        for line in file:
            if line[0] != '>':
                genome += line.strip()
            else:
                v.append(genome.upper())
                genome = ''
        #end-for
        v.append(genome.upper())
        del v[0]
        return v
    #end-with
#end-def

# path_to_file = tf.keras.utils.get_file('untrained_gen_ACP.txt', 'https://raw.githubusercontent.com/mhdshl/ACP_Seq2Seq/main/Data/untrained_gen_ACP.txt')
# Sequences = readFASTAs(path_to_file)

def ensure(path_to_file):
  Sequences = readFASTAs(path_to_file)
    for seq in Sequences:
        if check(seq) == False:
            return False
        #end-if
    #end-for
    return True
#end-def


assert ensure() == True # It won't work, if the bad character found.

# Protein/Peptide One-Zero Encoding

dBPF = {
    'A':[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    'C':[0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    'D':[0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    'E':[0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    'F':[0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    'G':[0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    'H':[0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0],
    'I':[0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0],
    'K':[0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
    'L':[0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0],
    'M':[0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0],
    'N':[0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0],
    'P':[0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0],
    'Q':[0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0],
    'R':[0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0],
    'S':[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0],
    'T':[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0],
    'V':[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0],
    'W':[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0],
    'Y':[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    'p':[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0], #padding
}

dBIT = {
    'A': [0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0],
    'R': [0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 1],
    'N': [0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 1],
    'D': [0, 1, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 1],
    'C': [0, 0, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0],
    'Q': [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1],
    'E': [0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1],
    'G': [0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0],
    'H': [1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0],
    'I': [0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0],
    'L': [0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0],
    'K': [0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 1],
    'M': [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0],
    'F': [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0],
    'P': [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0],
    'S': [0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0],
    'T': [0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0],
    'W': [1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0],
    'Y': [1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0],
    'V': [0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0],
    'p': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
}


dBLOSUM = {
    'A':[ 4,  0, -2, -1, -2,  0, -2, -1, -1, -1, -1, -2, -1, -1, -1,  1,  0,  0, -3, -2],
    'C':[ 0,  9, -3, -4, -2, -3, -3, -1, -3, -1, -1, -3, -3, -3, -3, -1, -1, -1, -2, -2],
    'D':[-2, -3,  6,  2, -3, -1, -1, -3, -1, -4, -3,  1, -1,  0, -2,  0, -1, -3, -4, -3],
    'E':[-1, -4,  2,  5, -3, -2,  0, -3,  1, -3, -2,  0, -1,  2,  0,  0, -1, -2, -3, -2],
    'F':[-2, -2, -3, -3,  6, -3, -1,  0, -3,  0,  0, -3, -4, -3, -3, -2, -2, -1,  1,  3],
    'G':[ 0, -3, -1, -2, -3,  6, -2, -4, -2, -4, -3,  0, -2, -2, -2,  0, -2, -3, -2, -3],
    'H':[-2, -3, -1,  0, -1, -2,  8, -3, -1, -3, -2,  1, -2,  0,  0, -1, -2, -3, -2,  2],
    'I':[-1, -1, -3, -3,  0, -4, -3,  4, -3,  2,  1, -3, -3, -3, -3, -2, -1,  3, -3, -1],
    'K':[-1, -3, -1,  1, -3, -2, -1, -3,  5, -2, -1,  0, -1,  1,  2,  0, -1, -2, -3, -2],
    'L':[-1, -1, -4, -3,  0, -4, -3,  2, -2,  4,  2, -3, -3, -2, -2, -2, -1,  1, -2, -1],
    'M':[-1, -1, -3, -2,  0, -3, -2,  1, -1,  2,  5, -2, -2,  0, -1, -1, -1,  1, -1, -1],
    'N':[-2, -3,  1,  0, -3,  0,  1, -3,  0, -3, -2,  6, -2,  0,  0,  1,  0, -3, -4, -2],
    'P':[-1, -3, -1, -1, -4, -2, -2, -3, -1, -3, -2, -2,  7, -1, -2, -1, -1, -2, -4, -3],
    'Q':[-1, -3,  0,  2, -3, -2,  0, -3,  1, -2,  0,  0, -1,  5,  1,  0, -1, -2, -2, -1],
    'R':[-1, -3, -2,  0, -3, -2,  0, -3,  2, -2, -1,  0, -2,  1,  5, -1, -1, -3, -3, -2],
    'S':[ 1, -1,  0,  0, -2,  0, -1, -2,  0, -2, -1,  1, -1,  0, -1,  4,  1, -2, -3, -2],
    'T':[ 0, -1, -1, -1, -2, -2, -2, -1, -1, -1, -1,  0, -1, -1, -1,  1,  5,  0, -2, -2],
    'V':[ 0, -1, -3, -2, -1, -3, -3,  3, -2,  1,  1, -3, -2, -2, -3, -2,  0,  4, -3, -1],
    'W':[-3, -2, -4, -3,  1, -2, -2, -3, -3, -2, -1, -4, -4, -2, -3, -3, -2, -3, 11,  2],
    'Y':[-2, -2, -3, -2,  3, -3,  2, -1, -2, -1, -1, -2, -3, -1, -2, -2, -2, -1,  2,  7],
    'p':[ 0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
}

def numeric(d):
    X = []

    for sequence in Sequences:
        x = []
        for residue in sequence:
            x.append(d[residue])
        #end-for
        v =  len(sequence) - paddingLength
        if v < 0:
            v = v*(-1)
            for i in range(v):
                x.append(d['p'])
            #end-for
        else:
            x = x[0:paddingLength]

        x = np.array(x)
        # x = x.T
        X.append(x)

    X = np.array(X)
    return X
#end-def

"""# Features for the paper ACP-DL

## use the following for feature extraction

bpf, kmer, label = prepare_feature_ACP-DL(filepath)
"""

def TransDict_from_list(groups):
    transDict = dict()
    tar_list = ['0', '1', '2', '3', '4', '5', '6']
    result = {}
    index = 0
    for group in groups:
        g_members = sorted(group)  # Alphabetically sorted list
        for c in g_members:
            # print('c' + str(c))
            # print('g_members[0]' + str(g_members[0]))
            result[c] = str(tar_list[index])  # K:V map, use group's first letter as represent.
        index = index + 1
    return result

def get_3_protein_trids():
    nucle_com = []
    chars = ['0', '1', '2', '3', '4', '5', '6']
    base = len(chars)
    end = len(chars) ** 3
    for i in range(0, end):
        n = i
        ch0 = chars[n % base]
        n = n / base
        ch1 = chars[int(n % base)]
        n = n / base
        ch2 = chars[int(n % base)]
        nucle_com.append(ch0 + ch1 + ch2)
    return nucle_com

def translate_sequence(seq, TranslationDict):
    '''
    Given (seq) - a string/sequence to translate,
    Translates into a reduced alphabet, using a translation dict provided
    by the TransDict_from_list() method.
    Returns the string/sequence in the new, reduced alphabet.
    Remember - in Python string are immutable..

    '''
    import string
    from_list = []
    to_list = []
    for k, v in TranslationDict.items():
        from_list.append(k)
        to_list.append(v)
    # TRANS_seq = seq.translate(str.maketrans(zip(from_list,to_list)))
    TRANS_seq = seq.translate(str.maketrans(str(from_list), str(to_list)))
    # TRANS_seq = maketrans( TranslationDict, seq)
    return TRANS_seq

def get_4_nucleotide_composition(tris, seq, pythoncount=True):
    seq_len = len(seq)
    tri_feature = [0] * len(tris)
    k = len(tris[0])
    note_feature = [[0 for cols in range(len(seq) - k + 1)] for rows in range(len(tris))]
    if pythoncount:
        for val in tris:
            num = seq.count(val)
            tri_feature.append(float(num) / seq_len)
    else:
        # tmp_fea = [0] * len(tris)
        for x in range(len(seq) + 1 - k):
            kmer = seq[x:x + k]
            if kmer in tris:
                ind = tris.index(kmer)
                # tmp_fea[ind] = tmp_fea[ind] + 1
                note_feature[ind][x] = note_feature[ind][x] + 1
        # tri_feature = [float(val)/seq_len for val in tmp_fea]    #tri_feature type:list len:256
        u, s, v = la.svd(note_feature)
        for i in range(len(s)):
            tri_feature = tri_feature + u[i] * s[i] / seq_len
        # print tri_feature
        # pdb.set_trace()

    return tri_feature

def prepare_feature_ACP_DL(filepath):
    label = []
    interaction_pair = {}
    RNA_seq_dict = {}
    protein_seq_dict = {}
    protein_index = 0
    with open(filepath, 'r') as fp:
        for line in fp:
            if line[0] == '>':
                values = line[1:].strip().split('|')
                label_temp = values[1]
                proteinName = values[0]
                if label_temp == '1':
                    label.append(1)
                else:
                    label.append(0)
            else:
                seq = line[:-1]
                protein_seq_dict[protein_index] = seq
                protein_index = protein_index + 1
    # name_list = read_name_from_lncRNA_fasta('ncRNA-protein/lncRNA_RNA.fa')
    groups = ['AGV', 'ILFP', 'YMTS', 'HNQW', 'RK', 'DE', 'C']
    group_dict = TransDict_from_list(groups)
    protein_tris = get_3_protein_trids()
    # tris3 = get_3_trids()
    bpf=[]
    kmer=[]
    # get protein feature
    # pdb.set_trace()
    for i in protein_seq_dict:  # and protein_fea_dict.has_key(protein) and RNA_fea_dict.has_key(RNA):
        protein_seq = translate_sequence(protein_seq_dict[i], group_dict)
        bpf_feature = BPF(protein_seq_dict[i])
        # print('bpf:',shape(bpf_feature))
        # pdb.set_trace()
        # RNA_tri_fea = get_4_nucleotide_composition(tris, RNA_seq, pythoncount=False)
        protein_tri_fea = get_4_nucleotide_composition(protein_tris, protein_seq, pythoncount =False)

        bpf.append(bpf_feature)
        kmer.append(protein_tri_fea)
        # protein_index = protein_index + 1
        # chem_fea.append(chem_tmp_fea)
    return np.array(bpf), np.array(kmer), label

def BPF(seq_temp):
    seq = seq_temp
    chars = ['A', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'Y']
    fea = []
    tem_vec =[]
    k = 7
    for i in range(k):
        if seq[i] =='A':
            tem_vec = [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        elif seq[i]=='C':
            tem_vec = [0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        elif seq[i]=='D':
            tem_vec = [0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        elif seq[i]=='E':
            tem_vec = [0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        elif seq[i]=='F':
            tem_vec = [0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        elif seq[i]=='G':
            tem_vec = [0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        elif seq[i]=='H':
            tem_vec = [0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0]
        elif seq[i]=='I':
            tem_vec = [0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0]
        elif seq[i]=='K':
            tem_vec = [0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0]
        elif seq[i]=='L':
            tem_vec = [0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0]
        elif seq[i]=='M':
            tem_vec = [0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0]
        elif seq[i]=='N':
            tem_vec = [0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0]
        elif seq[i]=='P':
            tem_vec = [0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0]
        elif seq[i]=='Q':
            tem_vec = [0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0]
        elif seq[i]=='R':
            tem_vec = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0]
        elif seq[i]=='S':
            tem_vec = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0]
        elif seq[i]=='T':
            tem_vec = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0]
        elif seq[i]=='V':
            tem_vec = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0]
        elif seq[i]=='W':
            tem_vec = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0]
        elif seq[i]=='Y':
            tem_vec = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1]
        fea = fea + tem_vec
    return fea

# def prepare_feature():
#     label = []
#     interaction_pair = {}
#     RNA_seq_dict = {}
#     protein_seq_dict = {}
#     protein_index = 1
#     with open('acp740.txt', 'r') as fp:
#         for line in fp:
#             if line[0] == '>':
#                 values = line[1:].strip().split('|')
#                 label_temp = values[1]
#                 protein = values[0]
#                 if label_temp == '1':
#                     label.append(1)
#                 else:
#                     label.append(0)
#             else:
#                 seq = line[:-1]
#                 protein_seq_dict[protein_index] = seq
#                 protein_index = protein_index + 1
#     # name_list = read_name_from_lncRNA_fasta('ncRNA-protein/lncRNA_RNA.fa')
#     groups = ['AGV', 'ILFP', 'YMTS', 'HNQW', 'RK', 'DE', 'C']
#     group_dict = TransDict_from_list(groups)
#     protein_tris = get_3_protein_trids()

#     # tris3 = get_3_trids()
#     train = []
#     # get protein feature
#     # pdb.set_trace()
#     for i in protein_seq_dict:  # and protein_fea_dict.has_key(protein) and RNA_fea_dict.has_key(RNA):

#         protein_seq = translate_sequence(protein_seq_dict[i], group_dict)
#         # bpf_feature = BPF(protein_seq_dict[i])
#         # pdb.set_trace()
#         # RNA_tri_fea = get_4_nucleotide_composition(tris, RNA_seq, pythoncount=False)
#         protein_tri_fea = get_4_nucleotide_composition(protein_tris, protein_seq, pythoncount =False)

#         train.append(protein_tri_fea)
#         protein_index = protein_index + 1
#         # chem_fea.append(chem_tmp_fea)

#     return np.array(train), label