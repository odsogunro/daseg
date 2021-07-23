#!/usr/bin/env python
# encoding: utf-8

import numpy as np
import pandas as pd
import random
import os, sys
import torch
from torch.utils.data import Dataset, DataLoader, Sampler, ConcatDataset
from torch.nn.utils.rnn import pad_sequence
import torch.nn.functional as F
import h5py
from collections import OrderedDict
import functools
from functools import partial
from sklearn import preprocessing
import copy
from daseg.utils_ner import InputExample, InputFeatures
from ordered_set import OrderedSet



def shuffle_chunks(batch_data, shuffle_ChunkLen_aug):
    batch_data_new = []
    chunk_len = shuffle_ChunkLen_aug #200 # 2 sec
    for utt_data in batch_data:
        utt_len = len(utt_data)
        no_chunks = int(np.ceil(utt_len/chunk_len))
        temp = [utt_data[i*chunk_len:(i+1)*chunk_len]  for i in range(no_chunks)]
        random.shuffle(temp)
        temp = torch.Tensor(np.concatenate(temp))
        batch_data_new.append(temp)
    return batch_data_new        


def obtain_batch_data_aug(aug_ind, batch_data_new, concat_portion):
    concat_order = np.random.choice(['First', 'Second'], 1, p=[0.5, 0.5])
    batch_data_new_aug = []
    for ind,pair_ind in enumerate(aug_ind):
        temp = batch_data_new[pair_ind[1]]
        if concat_order == 'Second':
            utt_feat = torch.Tensor(np.concatenate([batch_data_new[pair_ind[0]], temp[:int(concat_portion[ind]*len(temp))]]))
        else:
            utt_feat = torch.Tensor(np.concatenate([temp[:int(concat_portion[ind]*len(temp))], batch_data_new[pair_ind[0]]]))
        batch_data_new_aug.append(utt_feat)

    batch_data_new = batch_data_new_aug
    return batch_data_new


def obtain_batch_data_neworder(aug_ind, batch_data_new):
    batch_data_new_aug = []
    for ind,pair_ind in enumerate(aug_ind):
        utt_feat = torch.Tensor(batch_data_new[pair_ind[0]])
        batch_data_new_aug.append(utt_feat)
    return batch_data_new_aug


def obtain_interm_label(label_scheme, current_label, target_label_encoder):
    if label_scheme == 'Exact':
        if current_label == 'DoNotExist':
            return [-100]
        return target_label_encoder.transform([current_label])
    if label_scheme == 'E':
        return target_label_encoder.transform(['I-'])
    elif target_label_encoder.label_scheme == 'IE':
        return target_label_encoder.transform(['I-'+current_label])


def obtain_labels_fine_segmentation(seg_boundaries, label_scheme, new_labels, target_label_encoder):
    new_labels_temp = []
    for ind,boundary_flag in enumerate(seg_boundaries):
        current_label = new_labels[ind]
        intermediate_label = obtain_interm_label(label_scheme, current_label, target_label_encoder)
        if not boundary_flag:
            new_labels_temp.append(intermediate_label)
        else:
            if current_label == 'DoNotExist':
                new_labels_temp.append([-100])
            else:
                new_labels_temp.append(target_label_encoder.transform([current_label]))
    return new_labels_temp


def obtain_labels_smooth_segmentation(seg_boundaries, label_scheme, new_labels, target_label_encoder):
    new_seg_boundaries = []
    new_labels_temp = []
    for ind,boundary_flag in enumerate(seg_boundaries[:-1]):
        current_label = new_labels[ind]
        intermediate_label = obtain_interm_label(label_scheme, current_label, target_label_encoder)
        if new_labels[ind+1] != current_label:
            new_seg_boundaries += [True]
            if current_label == 'DoNotExist':
                new_labels_temp.append([-100])
            else:
                new_labels_temp.append(target_label_encoder.transform([current_label]))
        else:
            new_seg_boundaries += [False]
            new_labels_temp.append(intermediate_label)

    seg_boundaries = new_seg_boundaries + [True]
    current_label = new_labels[-1]
    if current_label == 'DoNotExist':
        new_labels_temp.append([-100])
    else:
        new_labels_temp.append(target_label_encoder.transform([current_label]))
    new_labels = new_labels_temp
    return new_labels, seg_boundaries


def dur2frame_map(frame_len, seg_labels_path, features, target_label_encoder, segmentation_type='fine', padding_value_labels=-100):
    # frame_len should be in seconds
    label_scheme = target_label_encoder.label_scheme
    new_features = []
    new_labels = []
    seg_boundaries = []
    ## first get the features and corresponding labels in a plain style (A,A,A,A,H,H,N,N) with original seg_boundaries
    if '/' in seg_labels_path: # assuming a path includes '/'
        if os.path.isfile(seg_labels_path):
            ### for ERC task
            seg_labels = pd.read_csv(seg_labels_path, sep=',')
            seg_labels = seg_labels.values.tolist()
            for i in seg_labels:
                begin_time, end_time, emo_label = i[0], i[1], i[2]
                emo_label_original = emo_label
                seg_count_frames = round((end_time - begin_time) / frame_len)    
                if not target_label_encoder is None:
                    emo_label = target_label_encoder.transform([emo_label]) if emo_label in target_label_encoder.classes_ else None
                else:
                    emo_label = emo_label
                if emo_label_original == 'DoNotExist':
                    emo_label = -100

                if (not emo_label is None) and (seg_count_frames > 0):
                    #### assign labels for each frame and possibly filter some frames
                    frame_indices = [begin_time + ind*frame_len  for ind in range(seg_count_frames)]
                    frame_indices = list(map(lambda x:int(x/frame_len), frame_indices))
                    new_features.append(features[frame_indices])
                    new_labels += [emo_label_original  for ind in range(seg_count_frames)]
        
                    temp = [False for _ in range(seg_count_frames)]
                    temp[-1] = True
                    seg_boundaries += temp
        else:
            print(f'{seg_labels_path} does not exist, please check')
            sys.exit()
    else:
        ###### for utterance based classification task
        seg_count_frames = len(features)
        if not target_label_encoder is None:
            emo_label = target_label_encoder.transform([seg_labels_path]) if seg_labels_path in target_label_encoder.classes_ else None
        else:
            emo_label = emo_label
        if (not emo_label is None)  and (seg_count_frames > 0):
            new_labels = [seg_labels_path for ind in range(seg_count_frames)]
            seg_boundaries = [False for _ in range(seg_count_frames)]
            seg_boundaries[-1] = True
        new_features = features

    new_labels = np.squeeze(np.vstack(new_labels))
    ### now adjust the labels and segmentation_labels to suit "fine" or "smooth" and label_scheme
    if segmentation_type == 'fine':
        # then adjust the labels only and keep seg_boundaries as it is as they are already fine-grained
        new_labels = obtain_labels_fine_segmentation(seg_boundaries, label_scheme, new_labels, target_label_encoder)
    if segmentation_type == 'smooth':
        new_labels, seg_boundaries = obtain_labels_smooth_segmentation(seg_boundaries, label_scheme, new_labels, target_label_encoder)

    seg_boundaries = 1*np.array(seg_boundaries)
    new_labels = np.squeeze(np.vstack(new_labels))
    new_features = np.vstack(new_features)
    assert new_features.shape[0] == new_labels.shape[0]
    return new_features, new_labels, seg_boundaries


def dur2frame_map_tokentypeids(frame_len, seg_labels_path, features, target_label_encoder, segmentation_type='fine', padding_value_labels=-100):
    '''tokentypeids in the function name suggest that token_type_ids are not just all zeros, they can be segment indices or speaker info
    '''
    # frame_len should be in seconds
    label_scheme = target_label_encoder.label_scheme
    new_features = []
    new_labels = []
    seg_boundaries = []
    token_type_ids = []
    ## first get the features and corresponding labels in a plain style (A,A,A,A,H,H,N,N) with original seg_boundaries
    if '/' in seg_labels_path: # assuming a path includes '/'
        if os.path.isfile(seg_labels_path):
            ### for ERC task
            seg_labels = pd.read_csv(seg_labels_path, sep=',')
            seg_labels = seg_labels.values.tolist()
            for i in seg_labels:
                if len(i) == 4:
                    begin_time, end_time, emo_label, spkr_ind = i[0], i[1], i[2], i[3]
                else:
                    begin_time, end_time, emo_label = i[0], i[1], i[2]
                    spkr_ind = '0'
                begin_time = round(begin_time, 2)
                end_time = round(end_time, 2)
                emo_label_original = emo_label
                seg_count_frames = round((end_time - begin_time) / frame_len)
                if not target_label_encoder is None:
                    emo_label = target_label_encoder.transform([emo_label]) if emo_label in target_label_encoder.classes_ else None
                else:
                    emo_label = emo_label
                if emo_label_original == 'DoNotExist':
                    emo_label = -100
                if (not emo_label is None) and (seg_count_frames > 0):
                    #### assign labels for each frame and possibly filter some frames
                    frame_indices = [begin_time + ind*frame_len  for ind in range(seg_count_frames)]
                    frame_indices = list(map(lambda x:int(x/frame_len), frame_indices))
                    if max(frame_indices) >= len(features):
                        print(f'WARNING: it seems max of frame_indices {max(frame_indices)} is higher than length of features {len(features)}. Check {seg_labels_path}')
                        if max(frame_indices) - len(features) < 5:
                            frame_indices = frame_indices[:-5]
                            seg_count_frames = len(frame_indices)
                        else:
                            raise ValueError(f'it seems max of frame_indices {max(frame_indices)} is a lot higher than length of features {len(features)} so exiting')
                    new_features.append(features[frame_indices])
                    new_labels += [emo_label_original  for ind in range(seg_count_frames)]

                    temp = [False for _ in range(seg_count_frames)]
                    temp[-1] = True
                    seg_boundaries += temp
                    token_type_ids += [spkr_ind for  _ in range(seg_count_frames)]
        else:
            print(f'{seg_labels_path} does not exist, please check')
            sys.exit()
    else:
        ###### for utterance based classification task
        seg_count_frames = len(features)
        if not target_label_encoder is None:
            emo_label = target_label_encoder.transform([seg_labels_path]) if seg_labels_path in target_label_encoder.classes_ else None
        else:
            emo_label = emo_label
        if (not emo_label is None)  and (seg_count_frames > 0):
            new_labels = [seg_labels_path for ind in range(seg_count_frames)]
            seg_boundaries = [False for _ in range(seg_count_frames)]
            seg_boundaries[-1] = True
            spkr_ind = '0' # TODO: You should inlcude actual spkear ind here but
            token_type_ids += [spkr_ind for  _ in range(seg_count_frames)]

        new_features = features

    new_labels = np.squeeze(np.vstack(new_labels))
    ### now adjust the labels and segmentation_labels to suit "fine" or "smooth" and label_scheme
    if segmentation_type == 'fine':
        # then adjust the labels only and keep seg_boundaries as it is as they are already fine-grained
        new_labels = obtain_labels_fine_segmentation(seg_boundaries, label_scheme, new_labels, target_label_encoder)
    if segmentation_type == 'smooth':
        new_labels, seg_boundaries = obtain_labels_smooth_segmentation(seg_boundaries, label_scheme, new_labels, target_label_encoder)

    seg_boundaries = 1*np.array(seg_boundaries)
    new_labels = np.squeeze(np.vstack(new_labels))
    new_features = np.vstack(new_features)
    assert new_features.shape[0] == new_labels.shape[0]
    return new_features, new_labels, seg_boundaries, token_type_ids


def concat_aug_ERC(batch_data, batch_mask_data, batch_label, seg_boundaries, batch_token_type_ids):
    indices = list(range(len(batch_data)))
    random.shuffle(indices)
    batch_data_new = [np.concatenate([batch_data[ind1], batch_data[ind2]]) for ind1,ind2 in enumerate(indices)]
    batch_mask_data_new = [np.concatenate([batch_mask_data[ind1], batch_mask_data[ind2]]) for ind1,ind2 in enumerate(indices)]
    batch_label_new = [np.concatenate([batch_label[ind1], batch_label[ind2]]) for ind1,ind2 in enumerate(indices)]
    seg_boundaries_new = [np.concatenate([seg_boundaries[ind1], seg_boundaries[ind2]]) for ind1,ind2 in enumerate(indices)]
    batch_token_type_ids_new = [np.concatenate([batch_token_type_ids[ind1], batch_token_type_ids[ind2]]) for ind1,ind2 in enumerate(indices)]
    return batch_data_new, batch_mask_data_new, batch_label_new, seg_boundaries_new, batch_token_type_ids_new


def map_tokentype_ids(batch_token_type_ids):
    new_batch_token_type_ids = []
    for utt_token_type_ids in batch_token_type_ids:
        unique_ids = set(utt_token_type_ids)
        map_unique_ids = {j:i for i,j in enumerate(unique_ids)}
        #print(map_unique_ids)
        new_batch_token_type_ids.append([map_unique_ids[i] for i in utt_token_type_ids])
    return new_batch_token_type_ids


def to_batch_tensors(batch_data_new, batch_mask_data_new, batch_label_new, seg_boundaries_new, token_type_ids, 
                                            padding_value_features, padding_value_mask, padding_value_labels, split, batch_key, task_type='SeqTagging'):
    ''' Does padding to features, labels, mask, token_type_ids
    '''
    ## TODO: check where to pad either left or right
    batch_data_new = [torch.Tensor(i) for i in batch_data_new]
    if len(batch_data_new[0].shape) == 2:
        ## usually when processing continuous inputs like MFCC...
        batch_data = pad_sequence(batch_data_new, padding_value=padding_value_features).permute(1,0,2)
    if len(batch_data_new[0].shape) == 1:
        ## usually when processing text data
        batch_data = pad_sequence(batch_data_new, padding_value=padding_value_features).permute(1,0)
        batch_data = batch_data.type(torch.LongTensor) # if input is token indices then they have to be of type Long
    batch_mask_data_new = [torch.Tensor(i) for i in batch_mask_data_new]
    batch_mask_data = pad_sequence(batch_mask_data_new, padding_value=padding_value_mask).permute(1, 0)
    #import pdb; pdb.set_trace()
    #if isinstance(batch_label_new[0], list):
    if task_type == 'SeqTagging':
        # each sequence sample has a sequence of labels
        batch_label_new = [torch.Tensor(i) for i in batch_label_new]
        batch_label = pad_sequence(batch_label_new, padding_value=padding_value_labels).permute(1, 0)
        batch_label = batch_label.type(torch.LongTensor)
    else:
        if isinstance(batch_label_new[0], float):
            # usually for regression tasks
            batch_label = torch.Tensor(batch_label_new)
            batch_label = batch_label.type(torch.FloatTensor)
        else:
            ## usually for classification tasks
            batch_label = torch.Tensor(batch_label_new)
            batch_label = batch_label.type(torch.LongTensor)
    seg_boundaries_new = [torch.Tensor(i) for i in seg_boundaries_new]
    seg_boundaries_new = pad_sequence(seg_boundaries_new, padding_value=-100).permute(1, 0)

    token_type_ids = [torch.Tensor(i) for i in token_type_ids]
    token_type_ids = pad_sequence(token_type_ids, padding_value=0).permute(1, 0)
    token_type_ids = token_type_ids.type(torch.LongTensor)
    #print(batch_key, batch_data.shape, batch_mask_data.shape, batch_label.shape)
    if split == 'test':
        ### Last field should always be keys. You can not convert keys (string) to tensors
        return (batch_data, batch_mask_data, batch_label, seg_boundaries_new, token_type_ids, batch_key)
    else:
        return (batch_data, batch_mask_data, batch_label, seg_boundaries_new, token_type_ids)


def cut_batch_to_maxlen(batch_data, batch_label, seg_boundaries, max_len, batch_mask=None, batch_token_type_ids=None, task_type='SeqTagging'):
    ''' Cuts the utterances longer than max_len to max_len. Shorter utts are kept as it is
    '''
    batch_data_new = []
    batch_mask_data_new = []
    batch_label_new = []
    seg_boundaries_new = []
    batch_token_type_ids_new = []
    for batch_ind,utt_feat in enumerate(batch_data):
        utt_labels = batch_label[batch_ind]
        utt_seg_boundaries = seg_boundaries[batch_ind]
        #utt_mask = np.ones(len(utt_feat)) if batch_mask is None else batch_mask[batch_ind]
        utt_mask = [1]*len(utt_feat) if batch_mask is None else batch_mask[batch_ind]
        utt_token_type_ids = np.zeros(len(utt_feat)) if batch_token_type_ids is None else batch_token_type_ids[batch_ind]
        if len(utt_feat) > max_len: # then randomly sample from the utterance
            begin_index = random.randrange(0, len(utt_feat) - max_len)
            utt_feat = utt_feat[begin_index:begin_index+max_len]
            if task_type == 'SeqClassif':
                pass
            else:
                utt_labels = utt_labels[begin_index:begin_index+max_len]
                utt_labels = np.squeeze(np.vstack(utt_labels))
            utt_seg_boundaries = utt_seg_boundaries[begin_index:begin_index+max_len]
            utt_mask = utt_mask[begin_index:begin_index+max_len]
            utt_token_type_ids = utt_token_type_ids[begin_index:begin_index+max_len]
        batch_data_new.append(utt_feat)
        batch_mask_data_new.append(utt_mask)
        batch_label_new.append(utt_labels)
        seg_boundaries_new.append(utt_seg_boundaries)
        batch_token_type_ids_new.append(utt_token_type_ids)
    
    return batch_data_new, batch_mask_data_new, batch_label_new, seg_boundaries_new, batch_token_type_ids_new


def select_few_samples(batch_data, batch_mask, batch_label, batch_seg_boundaries, batch_token_type_ids, no_batch_samples):
    random_indices = random.sample(list(range(len(batch_data))), no_batch_samples)
    batch_data = [batch_data[ind] for ind in random_indices]
    batch_mask = [batch_mask[ind] for ind in random_indices]
    batch_label = [batch_label[ind] for ind in random_indices]
    batch_seg_boundaries = [batch_seg_boundaries[ind] for ind in random_indices]
    batch_token_type_ids = [batch_token_type_ids[ind] for ind in random_indices]
    return batch_data, batch_mask, batch_label, batch_seg_boundaries, batch_token_type_ids
 

def build_segment_set(seg_boundaries):
    segment_set = OrderedSet()
    bounday_ind = [ind for ind,segment_flag in enumerate(seg_boundaries) if segment_flag]
    start = 0
    for end in bounday_ind:
        segment_set.add((start, end))
        start = end + 1
    return segment_set


def conv2isolatedsegments(batch_data, batch_label, batch_seg_boundaries, batch_token_type_ids, frame_len):
    batch_data_new = []
    batch_label_new = []
    batch_seg_boundaries_new = []
    batch_token_type_ids_new = []
    seg_dur_threshold = 1 # 1 sec
    seg_countframes_threshold = seg_dur_threshold/frame_len
    for conv_ind,utt_seg_boundaries in enumerate(batch_seg_boundaries):
        segment_set = build_segment_set(utt_seg_boundaries)
        for i in segment_set:
            start, end = i[0], i[1] + 1
            if  (end - start) > seg_countframes_threshold: # just to match with isoltaed_utt dataset where I think almost all utts are more than 1 sec
                batch_data_new.append(batch_data[conv_ind][start:end])
                batch_label_new.append(batch_label[conv_ind][start:end])
                batch_seg_boundaries_new.append(batch_seg_boundaries[conv_ind][start:end])
                batch_token_type_ids_new.append(batch_token_type_ids[conv_ind][start:end])

    return batch_data_new, batch_label_new, batch_seg_boundaries_new, batch_token_type_ids_new


def append_cls_token(batch_data, batch_mask, batch_seg_boundaries, batch_token_type_ids, padding_value_mask, cls_token):
    ## the following way of appending CLS token is BERT style which is same for Longformer too
    batch_data_new = []
    for i in batch_data:
        batch_data_new.append([cls_token] + i)
    batch_mask_new = []
    for i in batch_mask:
        batch_mask_new.append([1] + i)
    batch_seg_boundaries_new = []
    for i in batch_seg_boundaries:
        batch_seg_boundaries_new.append([False] + i) # batch_seg_boundaries are not relevant for the model training so it doesnt matter
    batch_token_type_ids_new = []
    #import pdb; pdb.set_trace()
    for i in batch_token_type_ids:
        batch_token_type_ids_new.append([i[0]] + i)
    return batch_data_new, batch_mask_new, batch_seg_boundaries_new, batch_token_type_ids_new


def transcript2tokenids(transcript_path, tokenizer):
    ## tokenize the text
    with open(transcript_path, 'r') as f:
        transcript = f.readlines()
    transcript = transcript[0]
    transcript_tokens = tokenizer.tokenize(transcript)
    input_ids = tokenizer.convert_tokens_to_ids(transcript_tokens)
    return input_ids


def obtain_text_fromcsv(tokenizer, transcript_path, seg_labels_path, target_label_encoder):
    input_ids = transcript2tokenids(transcript_path, tokenizer)
    if target_label_encoder is not None:
        utt_labels = target_label_encoder.transform([seg_labels_path])[0]
    else:
        utt_labels = float(seg_labels_path) #utt_labels
    utt_seg_boundaries = [True]*len(input_ids)
    utt_token_type_ids = [0]*len(input_ids) # for BERT
    mask = [1]*len(input_ids)
    return input_ids, utt_labels, utt_seg_boundaries, utt_token_type_ids, mask


def obtain_text_fromcsv_TrueCasing(tokenizer, transcript_path, seg_labels_path, target_label_encoder):

    with open(transcript_path, 'r') as f:
        transcript = f.readlines()
    transcript = transcript[0]
    transcript = transcript.split()
    utt_labels = []
    input_ids = [] 
    
    for word in transcript:
        #print(word)
        #import pdb; pdb.set_trace()
        if word != '<TURN>':
            if word.islower():
                word_label = 'LC'
            elif word.isupper():
                word_label = 'AUC' # All Upper Case
            else:
                # either mixed case or only beginning character is uppercase
                if word[0].isupper() and word[1:].islower():
                    word_label = 'UC'
                else:
                    word_label = 'MC'
    
            word_label = target_label_encoder.transform([word_label])[0]
            utt_labels.append(word_label)
            word = word.lower() ##### this needs to be the input and not the word with original case
        else:
            utt_labels += [-100] 
        subword_tokens = tokenizer.tokenize(word)
        subword_tokens = tokenizer.convert_tokens_to_ids(subword_tokens)
        input_ids += subword_tokens
        num_subwords = len(subword_tokens)
        if num_subwords > 1:
            utt_labels += [-100 for _ in range(num_subwords-1)]


    utt_seg_boundaries = [True]*len(input_ids)
    utt_token_type_ids = [0]*len(input_ids) # for BERT
    mask = [1]*len(input_ids)
    return input_ids, utt_labels, utt_seg_boundaries, utt_token_type_ids, mask


def obtain_text_fromcsv_TrueCasing_v2(tokenizer, transcript_path, seg_labels_path, target_label_encoder):
    '''This function is differey from obtain_text_fromcsv_TrueCasing. In this function, we assume the data dir
        already has labels and you need not detemine them here. Where as the function obtain_text_fromcsv_TrueCasing
        determines labels and hence it is not very flexible for diferent experiments
    '''

    #with open(transcript_path, 'r') as f:
    #    transcript = f.readlines()
    #transcript = transcript[0]
    #transcript = transcript.split()
    transcript = pd.read_csv(transcript_path, sep=',')
    transcript.dropna(axis=0, inplace=True)
    transcript = transcript[['word', 'label']]
    transcript = transcript.values.tolist()
    utt_labels = []
    input_ids = [] 
    
    for word_label_pair in transcript:
        #print(word)
        #import pdb; pdb.set_trace()
        
        word = word_label_pair[0]
        word_label = word_label_pair[1]

        if word_label == 'DoNotExist':
            word_label = -100
        else:
            word_label = target_label_encoder.transform([word_label])[0]
        utt_labels.append(word_label)

        subword_tokens = tokenizer.tokenize(word)
        subword_tokens = tokenizer.convert_tokens_to_ids(subword_tokens)
        input_ids += subword_tokens
        num_subwords = len(subword_tokens)
        if num_subwords > 1:
            utt_labels += [-100 for _ in range(num_subwords-1)]


    assert len(utt_labels) == len(input_ids)
    utt_seg_boundaries = [True]*len(input_ids)
    utt_token_type_ids = [0]*len(input_ids) # for BERT
    mask = [1]*len(input_ids)
    return input_ids, utt_labels, utt_seg_boundaries, utt_token_type_ids, mask


def obtain_text_fromcsv_Punctuation_v2(tokenizer, transcript_path, seg_labels_path, target_label_encoder):
    '''This function is differey from obtain_text_fromcsv_TrueCasing. In this function, we assume the data dir
        already has labels and you need not detemine them here. Where as the function obtain_text_fromcsv_TrueCasing
        determines labels and hence it is not very flexible for diferent experiments
    '''

    #with open(transcript_path, 'r') as f:
    #    transcript = f.readlines()
    #transcript = transcript[0]
    #transcript = transcript.split()
    transcript = pd.read_csv(transcript_path, sep=',')
    transcript.dropna(axis=0, inplace=True)
    transcript = transcript[['word', 'label']]
    transcript = transcript.values.tolist()
    utt_labels = []
    input_ids = [] 
    
    for word_label_pair in transcript:
        #print(word)
        #import pdb; pdb.set_trace()
        
        word = word_label_pair[0]
        word_label = word_label_pair[1]

        subword_tokens = tokenizer.tokenize(word)
        subword_tokens = tokenizer.convert_tokens_to_ids(subword_tokens)
        input_ids += subword_tokens
        num_subwords = len(subword_tokens)

        if word_label == 'DoNotExist':
            word_label = -100
        else:
            word_label = target_label_encoder.transform([word_label])[0]

        ## not computing loss for all the subtokens except last subtoken
        if num_subwords > 1:
            utt_labels += [-100 for _ in range(num_subwords-1)]
        utt_labels.append(word_label)

    assert len(utt_labels) == len(input_ids)
    utt_seg_boundaries = [True]*len(input_ids)
    utt_token_type_ids = [0]*len(input_ids) # for BERT
    mask = [1]*len(input_ids)
    return input_ids, utt_labels, utt_seg_boundaries, utt_token_type_ids, mask


def obtain_text_fromcsv_token_type_ids(tokenizer, transcript_path, seg_labels_path, target_label_encoder):
    if target_label_encoder is not None:
        utt_labels = target_label_encoder.transform([seg_labels_path])[0]
    else:
        utt_labels = float(seg_labels_path)

    utt_token_type_ids = []
    mask = []
    input_ids = []
    segmentation_info = pd.read_csv(transcript_path, sep=',')
    #import pdb; pdb.set_trace()
    segmentation_info = segmentation_info.values.tolist()
    ## not adding [CLS] token here because the total length could be > 512 and this token may be lost when we cut the sequence to 512 
    ## so added later after shortening the length


    for ind,i in enumerate(segmentation_info):
        begin, end, word, speaker = i
        temp = tokenizer.tokenize(word)
        if ind == 0:
            prev_spkr = speaker

        #if (prev_spkr != speaker):
        #    temp = ['[SEP]'] + temp
            #token_type = 1 - token_type # trying to alternate token_type_embeddings when new speaker occurs. Ideally, different token_type need to be added but pre-trained model only has 2 token_type_embeddings

        ############# put [SEP] only before 
        if speaker == 'INV':
            token_type = 1
        else:
            token_type = 0
        #############

        temp = tokenizer.convert_tokens_to_ids(temp)
        utt_token_type_ids += [token_type for i in range(len(temp))]
        mask += [1 for i in range(len(temp))]
        prev_spkr = speaker
        input_ids += temp
        
    utt_seg_boundaries = [True]*len(input_ids)

    return input_ids, utt_labels, utt_seg_boundaries, utt_token_type_ids, mask


def collate_fn_text(batch, split = 'train', max_len=None, target_label_encoder=None, concat_aug=0.5, padding_value_features=0, padding_value_mask=0, padding_value_labels=0, frame_len=0.1, label_scheme='E', segmentation_type='smooth', tokenizer=None):
    if isinstance(batch[0], tuple) and (len(batch[0]) == 1):
        batch = [batch[i][0] for i in range(len(batch))]

    batch_key = []
    batch_data = []
    batch_label = []
    batch_length = []
    batch_original_labels = []
    batch_seg_boundaries = []
    batch_token_type_ids = []
    batch_mask = []
    batch_size = len(batch)
    cls_token = tokenizer.convert_tokens_to_ids('CLS')
    for seq in batch:
        if seq[3] > 0:
            batch_key.append(seq[0])
            batch_original_labels.append(seq[2])
            #import pdb; pdb.set_trace()
            transcript_path = seq[1]
            with open(transcript_path, 'r') as f:
                transcript = f.readlines()
            if (transcript[0].startswith('start')) and (transcript[0].endswith('spkr_ind\n')):
                input_ids, utt_labels, utt_seg_boundaries, utt_token_type_ids, mask = obtain_text_fromcsv_token_type_ids(tokenizer, seq[1], seq[2], target_label_encoder)
            else:
                input_ids, utt_labels, utt_seg_boundaries, utt_token_type_ids, mask = obtain_text_fromcsv(tokenizer, seq[1], seq[2], target_label_encoder)
            # TODO: you temoporarily made it to work with transcript alignments. Please find a way to make it work both transcrupts as well as aligned transcripts
            #input_ids, utt_labels, utt_seg_boundaries, utt_token_type_ids, mask = obtain_text_fromcsv_token_type_ids(tokenizer, seq[1], seq[2], target_label_encoder)

            batch_data.append(input_ids)
            batch_label.append(utt_labels)
            batch_seg_boundaries.append(utt_seg_boundaries)
            batch_token_type_ids.append(utt_token_type_ids)
            batch_mask.append(mask)

    #if (split == 'test') and ((len(batch) == 1) or (max_len is None)):
    #    batch_mask = [[1]*len(batch_data[0])]  #*(1, batch_data[0].shape[0]))
    #else:
    if split != 'test':
        ## cutting to max_len before concat_aug is to make sure you have variety after concat_aug. 
        ## otherwise you might not have that variety because conversations can be long and you end up picking segment mostly only from one conv
        # max_len-1 is used to account for CLS token later 
        batch_data, batch_mask, batch_label, batch_seg_boundaries, batch_token_type_ids = cut_batch_to_maxlen(batch_data, batch_label, 
                                                        batch_seg_boundaries, max_len-1, batch_token_type_ids=batch_token_type_ids, task_type='SeqClassif', batch_mask=batch_mask)


    batch_data, batch_mask, batch_seg_boundaries, batch_token_type_ids = append_cls_token(batch_data, batch_mask, batch_seg_boundaries, batch_token_type_ids, padding_value_mask, cls_token)
    #import pdb; pdb.set_trace()
    batch_token_type_ids = map_tokentype_ids(batch_token_type_ids)
    return to_batch_tensors(batch_data, batch_mask, batch_label, batch_seg_boundaries, batch_token_type_ids,
                        padding_value_features, padding_value_mask, padding_value_labels, split, batch_key)
 

def collate_fn(batch, split = 'train', max_len=None, target_label_encoder=None, concat_aug=0.5, padding_value_features=0, padding_value_mask=0, padding_value_labels=0, frame_len=0.1, label_scheme='E', segmentation_type='smooth'):
    ''' It deals with either data files with one label per utteance (independent utterance classification) or files with sequence of labels like in conversations
        At any time it can deal with either one but not both. For collate_fn that deals with both, please refer to "collate_fn_EmoSpot"
    '''
    if isinstance(batch[0], tuple) and (len(batch[0]) == 1):
        batch = [batch[i][0] for i in range(len(batch))]

    batch_key = []
    batch_data = []
    batch_label = []
    batch_length = []
    batch_original_labels = []
    batch_seg_boundaries = []
    batch_token_type_ids = []
    batch_size = len(batch)
    for seq in batch:
        if seq[3] > 0:
            batch_key.append(seq[0])
            batch_original_labels.append(seq[2])
            if os.path.isfile(seq[2]):
                ip_data_type = 'conversation'
            else:
                ip_data_type = 'isolated_utt'
            utt_feat, utt_labels, utt_seg_boundaries, utt_token_type_ids = dur2frame_map_tokentypeids(frame_len, seq[2], seq[1], target_label_encoder, segmentation_type, padding_value_labels=padding_value_labels)
            #utt_feat, utt_labels, utt_seg_boundaries = dur2frame_map(frame_len, seq[2], seq[1], target_label_encoder, segmentation_type)
            batch_data.append(torch.Tensor(utt_feat))
            batch_label.append(utt_labels)
            batch_seg_boundaries.append(utt_seg_boundaries)
            #batch_token_type_ids.append(np.zeros(utt_feat.shape[0]))
            batch_token_type_ids.append(utt_token_type_ids)
            batch_length.append(seq[3])
       
    ## only at test time you can load full utterance irrespective of the max_len because utt is forward passed
    ## in windows. 
    if (split == 'test') and ((len(batch) == 1) or (max_len is None)):
        batch_mask = np.ones((1, batch_data[0].shape[0]))
    
    else: # make sure all the uttrenaces in the batch have max_len features
    
        if (ip_data_type == 'conversation') and (concat_aug == 1):
            ## concat_aug=1 if you want to remove context between all segments in a given conversation
            batch_data, batch_label, batch_seg_boundaries, batch_token_type_ids = conv2isolatedsegments(batch_data, 
                                                            batch_label, batch_seg_boundaries, batch_token_type_ids, frame_len)
            ## from here on, the data is like isolated_utt so assigning some variables
            ip_data_type = 'isolated_utt'
            concat_aug = 0
            batch_size = len(batch_data)

        if ip_data_type == 'conversation':
            if (split == 'train') and (not concat_aug < 0) and (batch_size > 1):
                if target_label_encoder.label_scheme != 'Exact':
                    raise ValueError(f'concat_aug {concat_aug} is still not supported for {target_label_encoder.label_scheme}')
                max_len = int(max_len/2)

            ## cutting to max_len before concat_aug is to make sure you have variety after concat_aug. 
            ## otherwise you might not have that variety because conversations can be long and you end up picking segment mostly only from one conv
            batch_data, batch_mask, batch_label, batch_seg_boundaries, batch_token_type_ids = cut_batch_to_maxlen(batch_data, batch_label, 
                                                            batch_seg_boundaries, max_len, batch_token_type_ids=batch_token_type_ids)
            if (split == 'train') and (not concat_aug < 0) and (batch_size > 1):
                batch_data, batch_mask, batch_label, batch_seg_boundaries, batch_token_type_ids = concat_aug_ERC(batch_data, batch_mask, batch_label, batch_seg_boundaries, batch_token_type_ids)

        elif ip_data_type == 'isolated_utt':
            batch_data, batch_mask, batch_label, batch_seg_boundaries, batch_token_type_ids = cut_batch_to_maxlen(batch_data, batch_label,
                                                        batch_seg_boundaries, max_len, batch_token_type_ids=batch_token_type_ids)
            if (split == 'train') and (not concat_aug < 0) and (batch_size > 1):
                ####  just keep concatenating until min concat_utt_length is more than half of max_len and choose only few concatenated utts
                no_times_concat = 1
                while 1:
                    batch_data, batch_mask, batch_label, batch_seg_boundaries, batch_token_type_ids = concat_aug_ERC(batch_data, batch_mask, batch_label, batch_seg_boundaries, batch_token_type_ids)
                    utt_lengths = [len(feat) for feat in batch_data]
                    no_times_concat += 1
                    if (min(utt_lengths) > int(max_len/2)) and (max(utt_lengths) > max_len):
                        break
                batch_data, batch_mask, batch_label, batch_seg_boundaries, batch_token_type_ids = cut_batch_to_maxlen(batch_data, batch_label,
                                                            batch_seg_boundaries, max_len, batch_token_type_ids=batch_token_type_ids)
                #### choose only few concatenated utts as there will be a lot of repetition 
                no_batch_samples = 6 #int(batch_size/no_times_concat) ##### higher number will likely result in memory errors
                batch_data, batch_mask, batch_label, batch_seg_boundaries, batch_token_type_ids = select_few_samples(batch_data, 
                                                            batch_mask, batch_label, batch_seg_boundaries, batch_token_type_ids, no_batch_samples)

    batch_token_type_ids = map_tokentype_ids(batch_token_type_ids)
    return to_batch_tensors(batch_data, batch_mask, batch_label, batch_seg_boundaries, batch_token_type_ids,
                        padding_value_features, padding_value_mask, padding_value_labels, split, batch_key)
    

def concat_indeputt_conv(feats1, labels1, bounds1, feats2, labels2, bounds2, token_type_ids1, token_type_ids2, mask1, mask2, padding_value_mask, padding_value_labels):
    assert feats1.shape[-1] == feats2.shape[-1]
    seq_seperator_vec = np.zeros((1, feats1.shape[-1]))
    feats = np.concatenate([feats1, seq_seperator_vec, feats2])

    seq_label = labels1[-1]
    labels2 = 1*(labels2 == seq_label)
    labels = np.concatenate([labels1, np.array([padding_value_labels]), labels2])

    bounds = np.concatenate([bounds1, np.array([padding_value_labels]), labels2])
    mask = np.concatenate([mask1, np.array([padding_value_mask]), mask2])
    #mask = np.concatenate([np.ones(len(feats1)), np.array([padding_value_mask]), np.ones(len(feats2))])

    token_type_ids = np.concatenate([token_type_ids1, np.array([0]), token_type_ids2])
    return feats, mask, labels, bounds, token_type_ids

 
def collate_fn_EmoSpot(batch, split = 'train', max_len=None, target_label_encoder=None, concat_aug=0.5, padding_value_features=0, padding_value_mask=0, padding_value_labels=0, frame_len=0.1, label_scheme='E', segmentation_type='smooth'):
    batch_data = []
    batch_mask = []
    batch_label = []
    batch_seg_boundaries = []
    batch_token_type_ids = []

    batch_data_indeputt = []
    batch_mask_indeputt = []
    batch_label_indeputt = []
    batch_seg_boundaries_indeputt = []
    batch_token_type_ids_indeputt = []

    batch_data_conv = []
    batch_mask_conv = []
    batch_label_conv = []
    batch_seg_boundaries_conv = []
    batch_token_type_ids_conv = []

    batch_size = len(batch)
    for seq_indeputt_conv in batch: # for EmoSpot: seq_indeputt_conv=[seq_indeputt, seq_conv]
        #### independent utt processing
        seq = seq_indeputt_conv[0] 
        if seq[3] > 0:
            indeputt_feat, indeputt_labels, indeputt_seg_boundaries = dur2frame_map(frame_len, seq[2], seq[1], 
                                                        target_label_encoder, segmentation_type)
            utt_token_type_ids = np.zeros(len(indeputt_feat))
            indeputt_mask = np.ones(len(indeputt_feat))

        batch_data_indeputt.append(indeputt_feat)
        batch_mask_indeputt.append(indeputt_mask)
        batch_label_indeputt.append(indeputt_labels)
        batch_seg_boundaries_indeputt.append(indeputt_seg_boundaries)
        batch_token_type_ids_indeputt.append(utt_token_type_ids)
        #### conv processing
        seq = seq_indeputt_conv[1]
        if seq[3] > 0:
            conv_feat, conv_labels, conv_seg_boundaries = dur2frame_map(frame_len, seq[2], seq[1], target_label_encoder, segmentation_type)
            conv_token_type_ids = np.ones(len(conv_feat))
            #conv_token_type_ids = np.zeros(len(conv_feat))
            conv_mask = np.ones(len(conv_feat))
            #conv_mask = np.zeros(len(conv_feat))

        batch_data_conv.append(conv_feat)
        batch_mask_conv.append(conv_mask)
        batch_label_conv.append(conv_labels)
        batch_seg_boundaries_conv.append(conv_seg_boundaries)
        batch_token_type_ids_conv.append(conv_token_type_ids)
 
    ## only at test time you can load full utterance irrespective of the max_len because utt is forward passed
    ## in windows. 
    if (split == 'test') and ((len(batch) == 1) or (max_len is None)):
        raise ValueError(f'Not implemented yet for EmoSpot at test time')
    else: # make sure all the uttrenaces in the batch have max_len features
        if (split == 'train') and (not concat_aug < 0) and (len(batch) > 1):
            if target_label_encoder.label_scheme != 'Exact':
                raise ValueError(f'concat_aug {concat_aug} is still not supported for {target_label_encoder.label_scheme}')
            max_len_conv = int(max_len/4) ## to create more variety in each sample
        
            batch_data_conv, batch_mask_conv, batch_label_conv, batch_seg_boundaries_conv, batch_token_type_ids_conv = cut_batch_to_maxlen(
                                    batch_data_conv, batch_label_conv, batch_seg_boundaries_conv,
                                    max_len_conv, batch_mask=batch_mask_conv, batch_token_type_ids=batch_token_type_ids_conv)

            ## doing concat aug 2 times because maxlen_conv is set to max_len/4 and we can get to max_len only if we do 2 times concat aug
            for _ in range(2):        
                batch_data_conv, batch_mask_conv, batch_label_conv, batch_seg_boundaries_conv, batch_token_type_ids_conv = concat_aug_ERC(
                                    batch_data_conv, batch_mask_conv, batch_label_conv, batch_seg_boundaries_conv, batch_token_type_ids_conv)

        for batch_ind in range(batch_size):
            indeputt_feat, indeputt_mask  = batch_data_indeputt[batch_ind], batch_mask_indeputt[batch_ind]
            indeputt_labels, indeputt_seg_boundaries = batch_label_indeputt[batch_ind], batch_seg_boundaries_indeputt[batch_ind]
            utt_token_type_ids = batch_token_type_ids_indeputt[batch_ind]

            indeputt_len = len(indeputt_feat)
            conv_maxlen = max_len - indeputt_len - 1
            conv_feat, conv_mask = batch_data_conv[batch_ind], batch_mask_conv[batch_ind]
            conv_labels, conv_seg_boundaries = batch_label_conv[batch_ind], batch_seg_boundaries_conv[batch_ind]
            conv_token_type_ids = batch_token_type_ids_conv[batch_ind]
            conv_feat, conv_mask, conv_labels, conv_seg_boundaries, conv_token_type_ids = cut_batch_to_maxlen(
                        [conv_feat], [conv_labels], [conv_seg_boundaries], 
                        conv_maxlen, batch_token_type_ids=[conv_token_type_ids], batch_mask=[conv_mask])
            conv_feat, conv_mask, conv_labels, conv_seg_boundaries, conv_token_type_ids = conv_feat[0], conv_mask[0], conv_labels[0], conv_seg_boundaries[0], conv_token_type_ids[0]

            emospot_feat, emospot_mask, emospot_labels, emospot_seg_boundaries, emo_spot_token_type_ids = concat_indeputt_conv(
                        indeputt_feat, indeputt_labels, indeputt_seg_boundaries, 
                        conv_feat, conv_labels, conv_seg_boundaries, 
                        utt_token_type_ids, conv_token_type_ids,
                        indeputt_mask, conv_mask,
                        padding_value_mask, padding_value_labels)
            batch_data.append(emospot_feat)
            batch_mask.append(emospot_mask)
            batch_label.append(emospot_labels)
            batch_seg_boundaries.append(emospot_seg_boundaries)
            batch_token_type_ids.append(emo_spot_token_type_ids)


    return to_batch_tensors(batch_data, batch_mask, batch_label, batch_seg_boundaries, batch_token_type_ids,
                        padding_value_features, padding_value_mask, padding_value_labels)
 
class BaseDataset(Dataset):

    def __init__(self, utt2label, hdf5_path, max_len=None):
        #self.csv = pd.read_csv(csv_path, sep=',', header=None)
        self.utt2label = utt2label #dict(zip(list(self.csv[0].values), list(self.csv[1].values)))
                
        self.keys = self.utt2label[:, 0] #list(self.utt2label.keys())
        self.hdf5 = h5py.File(hdf5_path,'r')
        self.max_len = max_len
        super().__init__()

    def __len__(self):
        return len(self.keys)
    
    def __getitem__(self,index):
        key = self.keys[index]
        try:
            utt_len = len(self.hdf5[key])            
            max_len = self.max_len
        
            ## the following snippet is not suitable for ERC task
            if (max_len is None) or (utt_len < max_len):
                X = self.hdf5[key][()]
            else:
                begin_index = random.randrange(0, utt_len-max_len)
                X = self.hdf5[key][begin_index:begin_index+max_len]

            y = self.utt2label[index, 1] #self.utt2label[key]
            spk = None
            length = X.shape[0]
            return key, X, y, length, spk
        except:
            print(f'possible  {key} could not be found in features h5 file')
            return key, None, 0, 0, 0

    def close(self):
        self.f.close()
        return None


class SpeechDataset(BaseDataset):
    def __init__(self, utt2label, features_path=None, max_len=None):
        super().__init__(utt2label, features_path, max_len)


def get_dataset(data_dir, features_path=None, data_csv='train.tsv', max_len=None):
    train_ds = []
    train_csv = pd.read_csv(data_csv, sep=',', header=None)
    utt2label_train = dict(zip(list(train_csv[0].values), list(train_csv[1].values)))
    train_tsv_size = len(utt2label_train)

    if os.path.exists(data_dir+'/feats.scp_h5'):
        print(f'feats.scp_h5 exists in the data dir {data_dir} so using that and ignoring the features path supplied')
        feats_csv = pd.read_csv(data_dir+'/feats.scp_h5', sep=',', header=None)                        
        feats_csv_groups = feats_csv.groupby(1)
        feats_csv_groups_list = list(feats_csv_groups.groups.keys())
        for feat_group in feats_csv_groups_list:
            temp_utt_list = list(feats_csv_groups.get_group(feat_group)[0].values)
            #utt2label_train_temp = {utt_id:utt2label_train[utt_id]  for utt_id in temp_utt_list if utt_id in utt2label_train}
            utt2label_train_temp = [(utt_id, utt2label_train[utt_id])  for utt_id in temp_utt_list if utt_id in utt2label_train]
            if utt2label_train_temp:
                utt2label_train_temp = np.vstack(utt2label_train_temp)

                train_ds.append(SpeechDataset(utt2label=utt2label_train_temp, features_path=feat_group, max_len=max_len))

    else:
        print(f'feats.scp_h5 do not exist in the data dir {data_dir} so using the features path supplied')
        utt2label_train_temp = np.vstack([(i[0], i[1]) for i in zip(list(train_csv[0]), list(train_csv[1]))])
        train_ds.append(SpeechDataset(utt2label=utt2label_train_temp, features_path=features_path, max_len=max_len))

    train_ds = ConcatDataset(train_ds)
    dataloader_size = len(train_ds)
    missing_feature_files_count = train_tsv_size - dataloader_size
    if missing_feature_files_count > dataloader_size/2:
        print(f'ERROR: More than half of the utterances do not have feature, so exiting ...')
        sys.exit()
    if missing_feature_files_count>0:
        print(f'WARNING: {missing_feature_files_count} utterances do not have features')

    return train_ds


def get_target_encoder(data_dir, expt_dir):
    ''' As data_dir can consist of multiple data dirs, storing target encoder in the expt_dir makes more sense
    '''
    
    if ',' in data_dir:
        data_dir = data_dir.split(',')
    else:
        data_dir = [data_dir]

    train_targets = []
    for temp_data_dir in data_dir:
        train_data_csv = temp_data_dir + '/train.tsv'
        temp = pd.read_csv(train_data_csv, sep=',', header=None)
        train_targets.append(temp[1].values)
    train_targets = np.concatenate(train_targets).reshape(-1)
    from sklearn import preprocessing
    label_enc = preprocessing.LabelEncoder()
    label_enc.fit(train_targets)
    return label_enc


def get_target_encoder_ERC(train_tsv, additional_labels=[], remove_labels=[], label_scheme=None):
    train_targets = []
    train_data = pd.read_csv(train_tsv, sep=',', header=None)
    train_targets += list(train_data[1])
    train_labels = []
    if os.path.isfile(train_targets[0]):
        for utt_label_path in train_targets:
            temp = pd.read_csv(utt_label_path, sep=',')
            train_labels += list(set(temp['label'].values))
    else:
        train_labels = train_targets
    train_labels = list(set(train_labels))
    train_labels = [i for i in train_labels if not i in remove_labels if not pd.isna(i)]
    from sklearn import preprocessing
    label_enc = preprocessing.LabelEncoder()
    if label_scheme == 'Exact':
        train_labels = train_labels
    elif label_scheme == 'E':
        train_labels += ['I-']
    elif label_scheme == 'IE':
        train_labels += ['I-'+i for i in train_labels]     
    else:
        raise ValueError('invalid label scheme')
   
    train_labels += additional_labels
    label_enc.fit(train_labels)
    label_enc.label_scheme = label_scheme
    return label_enc


def get_target_encoder_TrueCasing(train_tsv, additional_labels=[], remove_labels=[], label_scheme=None):
    ### it is an improvement to get_target_encoder
    ### if all the utt in train.tsv have only one label then it looks for "labels" file in the same dir
    ### if it exists then this script uses the contents of that file for model targets
    train_targets = []
    train_data = pd.read_csv(train_tsv, sep=',', header=None)
    train_targets += list(train_data[1])
    train_labels = []
    if os.path.isfile(train_targets[0]):
        for utt_label_path in train_targets:
            temp = pd.read_csv(utt_label_path, sep=',')
            train_labels += list(set(temp['label'].values))
    else:
        train_labels = train_targets
    train_labels = list(set(train_labels))
    train_labels = [i for i in train_labels if not i in remove_labels if not pd.isna(i)]

    if len(train_labels) == 1:
        print(f'\n All utts in train.tsv seem to have only one label which is strange, so if there is "labels" file in that dir then we use that for model targets \n ')
        data_dir = os.path.dirname(train_tsv)
        labels_path = data_dir + '/labels'
        if os.path.exists(labels_path):        
            with open(labels_path, 'r') as f:
                train_labels = []
                for label in f.readlines():
                    train_labels.append(label.strip())
        else:
            print(f'{labels_path} file is not found in data_dir so going with whatever labels we have from train.tsv {train_labels} ')

    print(f'num labels for model taining are {len(train_labels)}')
    from sklearn import preprocessing
    label_enc = preprocessing.LabelEncoder()
    if label_scheme == 'Exact':
        train_labels = train_labels
    elif label_scheme == 'E':
        train_labels += ['I-']
    elif label_scheme == 'IE':
        train_labels += ['I-'+i for i in train_labels]     
    else:
        raise ValueError('invalid label scheme')
   
    train_labels += additional_labels
    label_enc.fit(train_labels)
    label_enc.label_scheme = label_scheme
    return label_enc



def get_utt_weights(data_dir):
    if ',' in data_dir:
        print(f'multiple data dirs {data_dir}  are provided and get_utt_weights function is not implemented for multiple data dirs yet. so exiting..')
        sys.exit()

    train_csv = pd.read_csv(data_dir+'/train.tsv', sep=',', header=None)
    utt2label_train = dict(zip(list(train_csv[0].values), list(train_csv[1].values)))

    generator_utt_order = [] # usually it shoukd be in the order of train.tsv but as we concatenate multiple generators based on the feature h5 file this order changes
    if os.path.exists(data_dir+'/feats.scp_h5'):
        print(f'feats.scp_h5 exists in the data dir {data_dir} so using that and ignoring the features path supplied')
        feats_csv = pd.read_csv(data_dir+'/feats.scp_h5', sep=',', header=None)                        
        feats_csv_groups = feats_csv.groupby(1)
        feats_csv_groups_list = list(feats_csv_groups.groups.keys())
        for feat_group in feats_csv_groups_list:
            temp_utt_list = list(feats_csv_groups.get_group(feat_group)[0].values)
            generator_utt_order += [utt_id  for utt_id in temp_utt_list if utt_id in utt2label_train]

    else:
        generator_utt_order = [i for i in train_csv[0]]

    assert len(generator_utt_order) == len(utt2label_train), "NOT all utt in train.tsv do have features, please check "
    class2weight, class2count = obtain_class_weights(data_dir)    
    utt_weights = []
    for utt_id in generator_utt_order:
        class_id = utt2label_train[utt_id]
        utt_weights += [class2weight[class_id]]

    return utt_weights


def obtain_class_weights(data_dir):
    train_csv = pd.read_csv(data_dir + '/train.tsv', sep=',', header=None)
    counts = train_csv.groupby([1]).count().values
    counts = np.hstack(counts)
    classes = list(train_csv.groupby([1]).groups.keys())
    class2weight = {i:1/j for i,j in zip(classes,counts)}
    class2count = {i:j for i,j in zip(classes,counts)}
    return class2weight, class2count


class BaseSiameseDataset(Dataset):
    def __init__(self, csv_path, hdf5_path):
        self.csv = pd.read_csv(csv_path, sep=',', header=None)
        self.data_list = list(zip(self.csv[0], self.csv[1], self.csv[2]))
        self.hdf5 = h5py.File(hdf5_path,'r')
        super().__init__()

    def __len__(self):
        return len(self.data_list)

    def __getitem__(self,index):
        pair_keys = self.data_list[index]
        utt1 = pair_keys[0]
        utt2 = pair_keys[1]
        label = [pair_keys[2]]
        #try:
        feat1 = self.hdf5[utt1][()]
        feat2 = self.hdf5[utt2][()]
        siamese_data = np.concatenate([feat1, feat2])
        return (torch.tensor(siamese_data), pair_keys[0]+'_vs._'+pair_keys[0], pair_keys[0]+'_vs._'+pair_keys[0]), torch.tensor(label)
        #except:
        #    print(f'possible  {utt1} or {utt2} could not be found in features h5 file')
        #    return siamese_data, label

    def close(self):
        self.f.close()
        return None


def get_Siamese_dataset(data_dir, features_path, data_csv='train.tsv', max_len=None, only_train_data=False):
    ''' Currently does not support feats.scp_h5
    '''
    train_ds = []

    print(f'feats.scp_h5 do not exist in the data dir {data_dir} so using the features path supplied')
    train_ds.append(BaseSiameseDataset(data_csv, hdf5_path=features_path))
    train_ds = ConcatDataset(train_ds)
    dataloader_size = len(train_ds)
    #missing_feature_files_count = train_tsv_size - dataloader_size
    #if missing_feature_files_count > dataloader_size/2:
    #    print(f'ERROR: More than half of the utterances do not have feature, so exiting ...')
    #    sys.exit()
    #if missing_feature_files_count>0:
    #    print(f'WARNING: {missing_feature_files_count} utterances do not have features')

    return train_ds


def collate_online_siamese_fn(batch,use_grl = False,use_add=False, split = 'train', max_len = None,use_key = False, target_label_encoder=None, concat_aug=0.5):
    ''' Currently it supports only for single vector feature inputs, hence max_len is always None here
    
    '''
    batch_key = []
    batch_data = []
    batch_label = []
    batch_length = []
    batch_spk = []
    batch_original_labels = []
    for seq in batch:
        if seq[3] > 0:
            batch_key.append(seq[0])
            batch_label.append(seq[2])
            batch_length.append(seq[3])
            batch_spk.append(seq[4])
            batch_data.append(seq[1])
    batch_data = np.vstack(batch_data)

    if (len(batch) == 1): # or (max_len is None):
        # then pad the sequences, by default padding is done to maximum length in the batch 
        print(f'siamese network training expects minimum of two samples in each batch but only 1 is given')
        sys.exit()
    else: # make sure all the uttrenaces in the batch have max_len features
        unique_batch_labels = np.unique(batch_label)
        batch_label2utt = {}
        for ind,i in enumerate(batch_label):
            if not i in batch_label2utt:
                batch_label2utt[i] = []
            batch_label2utt[i].append(ind)

        pair_ind = []
        siamese_label = []
        positive_pairs_count = 0
        batch_size = len(batch_label)
        prev_pair_len = len(pair_ind)

        for ind in range(batch_size):
            label = batch_label[ind]
            if positive_pairs_count <= int(len(batch_label)/2):
                possible_companions = batch_label2utt[label]
                possible_companions = [i for i in possible_companions if i!=ind]
                if possible_companions:
                    pair_ind.append(np.random.choice(possible_companions, 1))
                    positive_pairs_count += 1 
                    siamese_label.append(1) # positive pairs mapped to 1
            if len(pair_ind) == prev_pair_len:
                possible_label_of_pair = [i for i in unique_batch_labels if i!=label]
                if possible_label_of_pair:
                    while 1:
                        label_of_pair = np.random.choice(possible_label_of_pair, 1)
                        possible_companions = batch_label2utt[label]
                        if possible_companions:
                            pair_ind.append(np.random.choice(possible_companions, 1))
                            siamese_label.append(0) # negative pairs mapped to 0
                            break
            prev_pair_len = len(pair_ind)
                                 
        pair_ind = np.concatenate(pair_ind)
        assert len(pair_ind) == batch_data.shape[0], "Number of companions did not match with batch length"
        companion_data = batch_data[pair_ind]
        siamese_batch_data = np.concatenate([batch_data, companion_data], axis=-1)
        siamese_batch_label = siamese_label

        return (torch.tensor(siamese_batch_data), torch.tensor(batch_length)),torch.tensor(siamese_batch_label)


class MultiSpkrUttEvalDataset(Dataset):
    def __init__(self, csv_path, feats_path):
        self.csv = pd.read_csv(csv_path, sep=',', header=None)
        self.data_list = list(zip(self.csv[0], self.csv[1], self.csv[2]))
        self.utt2feats_h5 = {}        
        utt2feats_h5 = pd.read_csv(feats_path, sep=',', header=None)        
        self.utt2feats_h5 = dict(zip(utt2feats_h5[0], utt2feats_h5[1]))
        super().__init__()

    def __len__(self):
        return len(self.data_list)
    
    def h5_read(self, h5_path, dataset):
        f_read = h5py.File(h5_path, 'r')
        feat = f_read[dataset][()]
        f_read.close()
        return feat

    def __getitem__(self,index):
        pair_keys = self.data_list[index]
        utt1 = pair_keys[0]
        utt2 = pair_keys[1]
        label = [pair_keys[2]]
        utt1_feat_h5_path = self.utt2feats_h5[utt1]
        utt2_feat_h5_path = self.utt2feats_h5[utt2]
        feat1 = self.h5_read(utt1_feat_h5_path, utt1)
        feat2 = self.h5_read(utt2_feat_h5_path, utt2)
        concat_feat = np.concatenate([feat1, feat2], 0)
        return 'concat_'+utt1+'_'+utt2, concat_feat, label, 100, None

    def close(self):
        self.f.close()
        return None


class ConcatDataset_SidebySide(torch.utils.data.Dataset):
    def __init__(self, *datasets):
        self.datasets = datasets
        lengths = [len(i) for i in self.datasets]
        print(f'concatenating datasets of lengths {lengths}')

    def __getitem__(self, i):
        return tuple(d[i] for d in self.datasets)

    def __len__(self):
        min_len = min(len(d) for d in self.datasets)
        print(f'assigning minimum length ({min_len}) of datasets as length of concatenated dataset')
        return min_len


class ConcatDataset_SidebySide_EqualizingLength(torch.utils.data.Dataset):
    def __init__(self, *datasets):
        self.datasets = datasets
        self.lengths = [len(i) for i in self.datasets]
        self.min_len = min(self.lengths)
        self.max_len = max(self.lengths)
        self.min2maxlen_ratio = self.min_len/self.max_len
        self.concat_datasetlen = self.max_len
        print(f'concatenating datasets of lengths {self.lengths}')
        print(f'Length equalization is done to make sure all samples in each dataset are sampled in each epoch')

    def __getitem__(self, i):
        indices = [i if i<dataset_len else int(i*self.min2maxlen_ratio) for dataset_len in self.lengths]
        return tuple(d[ind] for ind,d in zip(indices, self.datasets))
 
    def __len__(self):
        #min_len = min(len(d) for d in self.datasets)
        print(f'assigning length ({self.concat_datasetlen}) of datasets as length of concatenated dataset')
        return self.concat_datasetlen


class TextDataset(Dataset):

    def __init__(self, utt2label, features_path=None, max_len=None):
        #self.csv = pd.read_csv(csv_path, sep=',', header=None)
        self.utt2label = utt2label #dict(zip(list(self.csv[0].values), list(self.csv[1].values)))
                
        self.keys = self.utt2label[:, 0] #list(self.utt2label.keys())
        self.utt2csvpath = features_path
        self.max_len = max_len
        super().__init__()

    def __len__(self):
        return len(self.keys)
    
    def __getitem__(self,index):
        key = self.keys[index]
        csvpath = self.utt2csvpath[key]
        y = self.utt2label[index, 1]
        return key, csvpath, y,  100, 'Unknown'

    def close(self):
        self.f.close()
        return None


def get_dataset_text(data_dir, features_path=None, data_csv='train.tsv', max_len=None):
    train_ds = []
    train_csv = pd.read_csv(data_csv, sep=',', header=None)
    utt2label_train = dict(zip(list(train_csv[0].values), list(train_csv[1].values)))
    train_tsv_size = len(utt2label_train)

    if os.path.exists(data_dir+'/feats.scp_h5'):
        print(f'feats.scp_h5 exists in the data dir {data_dir} so using that and ignoring the features path supplied')
        feats_csv = pd.read_csv(data_dir+'/feats.scp_h5', sep=',', header=None)                        
        feats_csv_groups = feats_csv.groupby(1)
        feats_csv_groups_list = list(feats_csv_groups.groups.keys())
        for feat_group in feats_csv_groups_list:
            temp_utt_list = list(feats_csv_groups.get_group(feat_group)[0].values)
            #utt2label_train_temp = {utt_id:utt2label_train[utt_id]  for utt_id in temp_utt_list if utt_id in utt2label_train}
            utt2label_train_temp = [(utt_id, utt2label_train[utt_id])  for utt_id in temp_utt_list if utt_id in utt2label_train]
            if utt2label_train_temp:
                utt2label_train_temp = np.vstack(utt2label_train_temp)

                train_ds.append(SpeechDataset(utt2label=utt2label_train_temp, features_path=feat_group, max_len=max_len))

    elif os.path.exists(data_dir+'/utt2csvpath'):
        print(f'feats.scp_h5 do not exist in the data dir {data_dir} so using the utt2csvpath in the data dir')
        utt2label_train_temp = np.vstack([(i[0], i[1]) for i in zip(list(train_csv[0]), list(train_csv[1]))])
        utt2csvpath = pd.read_csv(data_dir+'/utt2csvpath',  sep=',', header=None)
        utt2csvpath = dict(zip(utt2csvpath[0], utt2csvpath[1]))
        train_ds.append(TextDataset(utt2label=utt2label_train_temp, features_path=utt2csvpath, max_len=max_len))

    train_ds = ConcatDataset(train_ds)
    dataloader_size = len(train_ds)
    missing_feature_files_count = train_tsv_size - dataloader_size
    if missing_feature_files_count > dataloader_size/2:
        print(f'ERROR: More than half of the utterances do not have feature, so exiting ...')
        sys.exit()
    if missing_feature_files_count>0:
        print(f'WARNING: {missing_feature_files_count} utterances do not have features')

    return train_ds


def get_dataset_text_TrueCasing(data_dir, features_path=None, data_csv='train.tsv', max_len=None):
    train_ds = []
    train_csv = pd.read_csv(data_csv, sep=',', header=None)
    train_csv[0] = train_csv[0].astype(str)
    utt2label_train = dict(zip(list(train_csv[0].values), list(train_csv[1].values)))
    train_tsv_size = len(utt2label_train)

    if os.path.exists(data_dir+'/feats.scp_h5'):
        print(f'feats.scp_h5 exists in the data dir {data_dir} so using that and ignoring the features path supplied')
        feats_csv = pd.read_csv(data_dir+'/feats.scp_h5', sep=',', header=None)                        
        feats_csv_groups = feats_csv.groupby(1)
        feats_csv_groups_list = list(feats_csv_groups.groups.keys())
        for feat_group in feats_csv_groups_list:
            temp_utt_list = list(feats_csv_groups.get_group(feat_group)[0].values)
            #utt2label_train_temp = {utt_id:utt2label_train[utt_id]  for utt_id in temp_utt_list if utt_id in utt2label_train}
            utt2label_train_temp = [(utt_id, utt2label_train[utt_id])  for utt_id in temp_utt_list if utt_id in utt2label_train]
            if utt2label_train_temp:
                utt2label_train_temp = np.vstack(utt2label_train_temp)

                train_ds.append(SpeechDataset(utt2label=utt2label_train_temp, features_path=feat_group, max_len=max_len))

    elif os.path.exists(data_dir+'/utt2csvpath'):
        print(f'feats.scp_h5 do not exist in the data dir {data_dir} so using the utt2csvpath in the data dir')
        utt2label_train_temp = np.vstack([(i[0], i[1]) for i in zip(list(train_csv[0]), list(train_csv[1]))])
        utt2csvpath = pd.read_csv(data_dir+'/utt2csvpath',  sep=',', header=None)
        utt2csvpath[0] = utt2csvpath[0].astype(str)
        utt2csvpath = dict(zip(utt2csvpath[0], utt2csvpath[1]))
        train_ds.append(TextDataset(utt2label=utt2label_train_temp, features_path=utt2csvpath, max_len=max_len))

    train_ds = ConcatDataset(train_ds)
    dataloader_size = len(train_ds)
    missing_feature_files_count = train_tsv_size - dataloader_size
    if missing_feature_files_count > dataloader_size/2:
        print(f'ERROR: More than half of the utterances do not have feature, so exiting ...')
        sys.exit()
    if missing_feature_files_count>0:
        print(f'WARNING: {missing_feature_files_count} utterances do not have features')

    return train_ds


def collate_fn_text_TrueCasing(batch, split = 'train', max_len=None, target_label_encoder=None, concat_aug=0.5, padding_value_features=0, padding_value_mask=0, padding_value_labels=0, frame_len=0.1, label_scheme='E', segmentation_type='smooth', tokenizer=None):
    if isinstance(batch[0], tuple) and (len(batch[0]) == 1):
        batch = [batch[i][0] for i in range(len(batch))]

    batch_key = []
    batch_data = []
    batch_label = []
    batch_length = []
    batch_original_labels = []
    batch_seg_boundaries = []
    batch_token_type_ids = []
    batch_mask = []
    batch_size = len(batch)
    cls_token = tokenizer.convert_tokens_to_ids('CLS')
    
    for seq in batch:
        if seq[3] > 0:
            batch_key.append(seq[0])
            batch_original_labels.append(seq[2])
            #import pdb; pdb.set_trace()
            transcript_path = seq[1]
            
            input_ids, utt_labels, utt_seg_boundaries, utt_token_type_ids, mask = obtain_text_fromcsv_TrueCasing_v2(tokenizer, seq[1], seq[2], target_label_encoder)

            batch_data.append(input_ids)
            batch_label.append(utt_labels)
            batch_seg_boundaries.append(utt_seg_boundaries)
            batch_token_type_ids.append(utt_token_type_ids)
            batch_mask.append(mask)


    if split != 'test':
        batch_data, batch_mask, batch_label, batch_seg_boundaries, batch_token_type_ids = cut_batch_to_maxlen(batch_data, batch_label, 
                                                        batch_seg_boundaries, max_len, batch_token_type_ids=batch_token_type_ids, task_type='SeqTagging', batch_mask=batch_mask)

    
    ## cls token may not be required for token classification tasks 
    #batch_data, batch_mask, batch_seg_boundaries, batch_token_type_ids = append_cls_token(batch_data, batch_mask, batch_seg_boundaries, batch_token_type_ids, padding_value_mask, cls_token)
    #import pdb; pdb.set_trace()
    batch_token_type_ids = map_tokentype_ids(batch_token_type_ids)
    batch_text = to_batch_tensors(batch_data, batch_mask, batch_label, batch_seg_boundaries, batch_token_type_ids,
                        padding_value_features, padding_value_mask, padding_value_labels, split, batch_key, task_type='SeqTagging')
    op = {}
    model_ip_keys = ['input_ids', 'attention_mask', 'labels', 'seg_boundaries', 'token_type_ids']
    if split == 'test':
        model_ip_keys.append('utt_id')

    for ind,i in enumerate(batch_text):
        temp = model_ip_keys[ind]
        op[temp] = i
    
    return op


def collate_fn_text_Punctuation(batch, split = 'train', max_len=None, target_label_encoder=None, concat_aug=0.5, padding_value_features=0, padding_value_mask=0, padding_value_labels=0, frame_len=0.1, label_scheme='E', segmentation_type='smooth', tokenizer=None):
    if isinstance(batch[0], tuple) and (len(batch[0]) == 1):
        batch = [batch[i][0] for i in range(len(batch))]

    batch_key = []
    batch_data = []
    batch_label = []
    batch_length = []
    batch_original_labels = []
    batch_seg_boundaries = []
    batch_token_type_ids = []
    batch_mask = []
    batch_size = len(batch)
    cls_token = tokenizer.convert_tokens_to_ids('CLS')
    
    for seq in batch:
        if seq[3] > 0:
            batch_key.append(seq[0])
            batch_original_labels.append(seq[2])
            #import pdb; pdb.set_trace()
            transcript_path = seq[1]
            
            input_ids, utt_labels, utt_seg_boundaries, utt_token_type_ids, mask = obtain_text_fromcsv_Punctuation_v2(tokenizer, seq[1], seq[2], target_label_encoder)

            batch_data.append(input_ids)
            batch_label.append(utt_labels)
            batch_seg_boundaries.append(utt_seg_boundaries)
            batch_token_type_ids.append(utt_token_type_ids)
            batch_mask.append(mask)


    if split != 'test':
        batch_data, batch_mask, batch_label, batch_seg_boundaries, batch_token_type_ids = cut_batch_to_maxlen(batch_data, batch_label, 
                                                        batch_seg_boundaries, max_len, batch_token_type_ids=batch_token_type_ids, task_type='SeqTagging', batch_mask=batch_mask)

    
    ## cls token may not be required for token classification tasks 
    #batch_data, batch_mask, batch_seg_boundaries, batch_token_type_ids = append_cls_token(batch_data, batch_mask, batch_seg_boundaries, batch_token_type_ids, padding_value_mask, cls_token)
    #import pdb; pdb.set_trace()
    batch_token_type_ids = map_tokentype_ids(batch_token_type_ids)
    batch_text = to_batch_tensors(batch_data, batch_mask, batch_label, batch_seg_boundaries, batch_token_type_ids,
                        padding_value_features, padding_value_mask, padding_value_labels, split, batch_key, task_type='SeqTagging')
    op = {}
    model_ip_keys = ['input_ids', 'attention_mask', 'labels', 'seg_boundaries', 'token_type_ids']
    if split == 'test':
        model_ip_keys.append('utt_id')

    for ind,i in enumerate(batch_text):
        temp = model_ip_keys[ind]
        op[temp] = i
    
    return op


