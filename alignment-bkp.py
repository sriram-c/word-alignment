#Program to align example sentences
import sys
import re
import os
import subprocess

def get_root(morph):
    root_wds = {}
    for wd in morph.split():
        roots = wd.split('/')
        rt_list = []
        for rt in roots:
            if '<' in rt:
                #root_wd = re.match(r'^([^<])*', rt)[0]
                root_wd = re.match(r'^([^<])*', rt).group(0)
                rt_list.append(root_wd)
            elif '^' in rt:
                if re.match(r'^\^(.*)$', rt):
                    #org_wd = re.match(r'^\^(.*)$', rt)[1]
                    org_wd = re.match(r'^\^(.*)$', rt).group(1)

        rt_list_final = list(set(rt_list))
        if(len(rt_list_final) > 0):
            root_wds[org_wd] = list(set(rt_list))
        else:
            root_wds[org_wd] = [org_wd]


    #make a reverse list root -> surface form
    root_wds_rev = {}
    for key in root_wds:
        val = root_wds[key]
        for l in val:
            root_wds_rev[l]= key

    return root_wds, root_wds_rev


def lwg_process(e_h_lwg):

    #For lwg give root and keep other words not to search
    #are_cutting    root:cut tam:are_ing ('are' not search)(are: rahe_hEM)

    lwg_dic = {}

    lwg_wd = e_h_lwg.split('\t')[0].split('_')
    lwg_hwd = e_h_lwg.split('\t')[5].split('_')
    lwg_root = e_h_lwg.split('\t')[1]
    lwg_aux = e_h_lwg.split('\t')[2]
    lwg_hindi = e_h_lwg.split('\t')[3]

    if '_' in lwg_aux:
        lwg_aux = lwg_aux.split('_')[:-1]
    if '0' in lwg_hindi:
        lwg_hindi = lwg_hindi.split('_')[1:]

    lwg_dic['_'.join(lwg_aux)] = lwg_hindi

    return lwg_wd, lwg_hwd


def align(E_H_sen, E_morph, H_morph, E_H_dic_processed, E_H_controlled_dic_processed, sbn_line, e_h_tam_dic, h_tam_all_form_dic):

    # function to align the English and Hindi sen
    # input : E_sen, H_sen, E_H_dic, E_H_dic controlled (user made)
    # output: aligned words

    E_wds = E_H_sen.split('\t')[0].split()
    H_wds = E_H_sen.split('\t')[1].split()
    E_root_wds, E_root_wds_rev = get_root(E_morph)
    H_root_wds, H_root_wds_rev = get_root(H_morph)


    H_root_wds_list = []
    for key in H_root_wds:
        H_root_wds_list.extend(H_root_wds[key])


    E_tam, E_root, E_vb, E_lwg = get_eng_tam_from_sbn(sbn_line)

    E_H_aligned = {}

    for ewd in E_wds:
        h_dic_wd = []

        # match original word lower case
        if ewd.lower() in E_H_dic_processed:
            h_dic_wd.extend(E_H_dic_processed[ewd.lower()])

        #match root word
        #for key in E_root_wds:
        if ewd in E_root_wds:
            for rt_wd in E_root_wds[ewd]:
                #rt_wd = E_root_wds[key][0]
                if rt_wd.lower() in E_H_dic_processed:
                    h_dic_wd.extend(E_H_dic_processed[rt_wd.lower()])

        #
        for hwd in h_dic_wd:
            if hwd in H_wds or hwd in H_root_wds_list:
                if hwd in H_root_wds_rev:
                    E_H_aligned[ewd] = H_root_wds_rev[hwd]
                    break
            else:
                if('_' in hwd) and ewd == E_vb:
                    kriyA_mula = hwd.split('_')[0]
                    if(kriyA_mula in H_wds):
                        E_H_aligned[ewd] = hwd
                        break


    #for tam processing using tam dic


    if('No' not in E_tam):
        h_eq_tam = e_h_tam_dic[E_tam]
        h_eq_tam_all_form = list(set(h_tam_all_form_dic[h_eq_tam]))

        e_h_lwg_dic = get_eng_hnd_tam_equivalent(E_H_aligned, H_wds, H_root_wds, E_wds, E_vb, E_lwg, h_eq_tam_all_form)

        for key in e_h_lwg_dic:
            E_H_aligned['_'.join(key.split())] = '_'.join(e_h_lwg_dic[key].split())
            for wd in key.split():
                if wd in E_H_aligned: del E_H_aligned[wd]


    '''
    #for lwg processing
    if len(e_h_lwg) > 0:
        lwg_wd, lwg_hwd = lwg_process(e_h_lwg)
        if set(lwg_hwd).issubset(set(H_wds)):

            E_H_aligned['_'.join(lwg_wd)] = '_'.join(lwg_hwd)

            for wd in lwg_wd:
                if wd in E_H_aligned: del E_H_aligned[wd]

    '''
    #for left over words to check meaning from controlled dic:
    for wd in E_wds:
        if wd not in E_H_aligned:
            if wd in E_H_controlled_dic_processed:
                hwd = E_H_controlled_dic_processed[wd]
                if set(hwd.split('_')).issubset(set(H_wds)):
                    E_H_aligned[wd] = hwd

    return E_H_aligned


def dic_process(E_H_dic):
    # read English-Hindi dictionary
    # store it in dictionary without the category info
    E_H_dic_processed = {}
    for line in E_H_dic:
        a =   (re.match('^#', line))
        if not(a):
            eng_wd_catg = line.split('\t')[0]
            eng_wd = eng_wd_catg.split('_')[0]
            hnd_wd = line.split('\t')[1].strip()
            hnd_wd_list = []
            if '/' in hnd_wd:
                hnd_wd_list = hnd_wd.split('/')
            else:
                hnd_wd_list.append(hnd_wd)

            if eng_wd in E_H_dic_processed:
                E_H_dic_processed[eng_wd].extend(hnd_wd_list)
            else:
                E_H_dic_processed[eng_wd] = hnd_wd_list

    return  E_H_dic_processed


def pmb_sbn_process(sbn_data):
    #processes the sbn data for each sentence
    for line in sbn_data:
        if('.v.' in line):
            verb = line.split()[0]

#compute tam information from sbn data
def get_eng_tam_from_sbn(sbn_data):

    found = 0

    for line in sbn_data:
        if '.v.' in line:
            root = line.split()[0].split('.')[0]
            wd = line.split('%')[1].split('[')[0].strip().split()[0]
            if 'Time -1' in line:
                index = sbn_data.index(line)
                prev_line = sbn_data[index-1]
                aux = prev_line.split('%')[1].split('[')[0].strip().split()[0]

                if(re.match(r'.*ing$',wd)):
                    return(aux+'_ing', root, wd, [aux, wd])

                elif (re.match(r'.*ed$', wd) and 'was' in prev_line):
                    return(aux+'_en', root, wd, [aux, wd])
                else:
                    return('No_tam', root, wd, wd)
                found = 1

    if not found:
            return ('No', 'No', 'No', 'No')


def get_eng_hnd_tam_equivalent(E_H_aligned, H_wds, H_root_wds, E_wds, E_vb, E_lwg, h_eq_tam_all_form):

    tam_eng_hnd = {}
    for tam in h_eq_tam_all_form:
        if('0_' in tam):
            tam_list = tam.split('_')[1:]
        else:
            tam_list = tam.split('_')

        if ' '.join(tam_list) in ' '.join(H_wds):
            if E_vb in E_H_aligned:
                h_eq = E_H_aligned[E_vb]
                #for handling kriyA_mula
                if '_' in h_eq:
                    kriyA_mula = h_eq.split('_')[0]
                    kriyA = h_eq.split('_')[1]
                    index = H_wds.index(kriyA_mula)
                    kriyA_in_sen = H_wds[index+1]
                    kriyA_in_sen_root = H_root_wds[kriyA_in_sen][0]
                    if kriyA_in_sen_root in kriyA:
                        E_H_aligned[E_vb] = kriyA_mula+'_'+kriyA_in_sen
                        tam_list = tam_list[1:]

                tam_eng_hnd[' '.join(E_lwg)] = E_H_aligned[E_vb]+' '+' '.join(tam_list)
            break

    return tam_eng_hnd


resource_path = '/home/sriram/ALIGNMENT/old-work/pmb-alignment/new/resources/'
#read English Hindi lwg info
with open(resource_path + 'controlled_dictionary.txt', 'r') as f:
    E_H_controlled_dic = f.readlines()
    E_H_controlled_dic_processed = {}
    for line in E_H_controlled_dic:
        eng_wd = line.split('\t')[0]
        hnd_wd = line.split('\t')[1].strip()
        E_H_controlled_dic_processed[eng_wd] = hnd_wd


#Read English Hindi dictionary
with open(resource_path + 'E_H_dictionary', 'r')as f:
    E_H_dic = f.readlines()
E_H_dic_processed = dic_process(E_H_dic)

#read eng_hnd_tam list
with open(resource_path + 'e_h_tam_list-wx', 'r') as f:
    e_h_tam = f.readlines()
    e_h_tam_dic = {}
    for line in e_h_tam:
        if(len(line.strip()) > 0):
            e_tam = line.split(';')[0].strip('"')
            h_tam = line.split(';')[1].strip('"').split('{')[0]
            e_h_tam_dic[e_tam] = h_tam


#read hnd_tam all forms
with open(resource_path + 'hnd_tam_all_form', 'r') as f:
    h_tam_all_form = f.readlines()
    h_tam_all_form_dic = {}
    for line in h_tam_all_form:
        h_tam = line.split(',')[0]
        h_form = line.split()[1].strip()
        if h_tam in h_tam_all_form_dic:
            h_tam_all_form_dic[h_tam].append(h_form)
        else:
            h_tam_all_form_dic[h_tam] = [h_form]


with open(resource_path + 'nmt-sbn.txt', 'r') as f:
    sbn_cont = f.read()

sbn_sent = sbn_cont.split('###')
eng_sen = open('eng.txt', 'w')
hnd_sen = open('hnd.txt', 'w')

sbn_sent1 = []
for s in sbn_sent:
    if (len(s.strip()) > 0):
        eng = s.strip().split('\n')[0].split('\t')[0]
        hnd = s.strip().split('\n')[0].split('\t')[1]

        eng_sen.write(eng+'\n')
        hnd_sen.write(hnd+'\n') 
        sbn_sent1.append(s)

eng_sen.close()
hnd_sen.close()

command = 'lt-proc -a ' + resource_path + 'en.morf.bin eng.txt  eng_morph'
os.system(command)
command = 'lt-proc -a -c ' + resource_path + 'hi.morf.bin hnd.txt hnd_morph'
os.system(command)

with open('eng_morph', 'r') as f:
    E_morph = f.readlines()

with open('hnd_morph', 'r') as f:
    H_morph = f.readlines()

for sbn, e_morph, h_morph in zip(sbn_sent1, E_morph, H_morph):
    eng_hnd = sbn.strip().split('\n')[0].strip()
    E_H_aligned = align(eng_hnd, e_morph, h_morph, E_H_dic_processed, E_H_controlled_dic_processed, sbn, e_h_tam_dic, h_tam_all_form_dic)
    print(eng_hnd)
    print(E_H_aligned)
    print('---------')

