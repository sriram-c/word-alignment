#Program to align example sentences

import sys
import re
import os
import subprocess
from util import *


resource_path = '/home/sriram/ALIGNMENT/PMB/pmb-alignment/resources/'
debug_level = sys.argv[1]

sbn_sent1, E_morph, H_morph, E_H_dic_processed, E_H_controlled_dic_processed, e_h_tam_dic, h_tam_all_form_dic = read_all_resources(resource_path)

for sbn, e_morph, h_morph in zip(sbn_sent1, E_morph, H_morph):

    eng_hnd = sbn.strip().split('\n')[0].strip()

    print(eng_hnd)

    E_H_aligned = align(eng_hnd, e_morph, h_morph, E_H_dic_processed, E_H_controlled_dic_processed, sbn, e_h_tam_dic, h_tam_all_form_dic, debug_level)

    print(E_H_aligned)
    print('#############################################')

