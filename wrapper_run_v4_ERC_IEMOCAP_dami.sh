#!/bin/bash

# echo 'START: script 01'

# set -x

# source /home/rpapagari/.bashrc
# source activate daseg_v2


# https://linuxize.com/post/bash-comments/
<< 'MULTILINE-COMMENT'
    variables defined in this wrapper
    
    concat_aug: 
        -1 for ?? 
        0  for ??
    
    task_name:

        [BERT Models]
            - task_name: IEMOCAP_ConvClassif_BERT
                - dataset: IEMOCAP
                - (downstream) task: CNN Classication
                - (upstream) model: BERT

        [BiLSTM Models]

            - task_name: IEMOCAP_UttClassif_bilstm
                - dataset: IEMOCAP
                - (downstream) task: Utterance Classication
                - (upstream) model: BILSTM NN

        [ResNet Models, https://arxiv.org/abs/1512.03385?context=cs]

            - task_name: IEMOCAP_UttClassif_ResNet
                - dataset: IEMOCAP
                - (downstream) task: Utterance Classication
                - (upstream) model: ResNet CNN

        [Longformer Models, https://arxiv.org/abs/2004.05150]
            
            - task_name: IEMOCAP_UttClassif_longformer
                - dataset: IEMOCAP
                - (downstream) task: Utterance Classication
                - (upstream) model: Longformer
            
            - task_name: IEMOCAP_UttClassif_longformer
                - dataset: IEMOCAP
                - (downstream) task: Utterance Classication
                - (upstream) model: Longformer

        [XFormer Models, https://facebookresearch.github.io/xformers/, https://github.com/facebookresearch/xformers]
            
            - task_name: IEMOCAP_ConvClassif_XFormerConcatTokenTypeEmb_smoothed_overlap_silenceNone_OOSNone_spkrind
                - dataset: IEMOCAP
                - (downstream) task: CNN Classication
                - (upstream) model: Longformer
    
    cv: 
        cross validation sets numbered 1 through 5
MULTILINE-COMMENT

train_mode=TE
for concat_aug in -1 #0 # -1 ##-1 #-1 #-1 # 0 #-1
do

for task_name in IEMOCAP_ConvClassif_BERT

# for task_name in IEMOCAP_UttClassif_bilstm 
# for task_name in IEMOCAP_UttClassif_ResNet
# for task_name in IEMOCAP_UttClassif_longformer

# for task_name in IEMOCAP_ConvClassif_XFormerConcatTokenTypeEmb_smoothed_overlap_silenceNone_OOSNone_spkrind
# for task_name in IEMOCAP_ConvClassif_XFormerAddAveSpeakerEmb_smoothed_overlap_silenceNone_OOSNone_spkrind
# for task_name in IEMOCAP_ConvClassif_XFormerConcatAveSpeakerEmb_smoothed_overlap_silenceNone_OOSNone_spkrind
# for task_name in IEMOCAP_ConvClassif_xformer_NoInfreqEmo
# for task_name in IEMOCAP_ConvClassif_XFormerConcatAveParamSpeakerEmb_smoothed_overlap_silenceNone_OOSNone
# for task_name in IEMOCAP_ConvClassif_XFormerConcatAveSpeakerEmb_smoothed_overlap_silenceNone_OOSNone
# for task_name in IEMOCAP_ConvClassif_XFormerAddAveSpeakerEmb_smoothed_overlap_silenceNone_OOSNone
# for task_name in IEMOCAP_ConvClassif_xformer_smoothed_overlap_silenceNone_OOSNone
# for task_name in IEMOCAP_ConvClassif_XFormerConcatSpeakerEmb_smoothed_overlap_silenceNone_OOSNone 
# for task_name in IEMOCAP_ConvClassif_XFormerAddSpeakerEmb_smoothed_overlap_silenceNone_OOSNone


###
# Raghu - SEE ABOVE 
###
#IEMOCAP_UttClassif_bilstm 
#IEMOCAP_UttClassif_ResNet
#IEMOCAP_UttClassif_longformer

# IEMOCAP_ConvClassif_XFormerConcatTokenTypeEmb_smoothed_overlap_silenceNone_OOSNone_spkrind
#IEMOCAP_ConvClassif_XFormerAddAveSpeakerEmb_smoothed_overlap_silenceNone_OOSNone_spkrind
#IEMOCAP_ConvClassif_XFormerConcatAveSpeakerEmb_smoothed_overlap_silenceNone_OOSNone_spkrind
#IEMOCAP_ConvClassif_xformer_NoInfreqEmo
#IEMOCAP_ConvClassif_XFormerConcatAveParamSpeakerEmb_smoothed_overlap_silenceNone_OOSNone
#IEMOCAP_ConvClassif_XFormerConcatAveSpeakerEmb_smoothed_overlap_silenceNone_OOSNone
#IEMOCAP_ConvClassif_XFormerAddAveSpeakerEmb_smoothed_overlap_silenceNone_OOSNone
# IEMOCAP_ConvClassif_xformer_smoothed_overlap_silenceNone_OOSNone
#IEMOCAP_ConvClassif_XFormerConcatSpeakerEmb_smoothed_overlap_silenceNone_OOSNone 
#IEMOCAP_ConvClassif_XFormerAddSpeakerEmb_smoothed_overlap_silenceNone_OOSNone

do
    for cv in 1 # 2 3 4 #1 2 3 4 5 
    do
        gpu=1
        grid=True
        bash run_v4_ERC_IEMOCAP_dami.sh $cv $train_mode $gpu 3 10 $concat_aug 42 $grid $task_name
        
        #bash run_v4_ERC_IEMOCAP_.sh $cv $train_mode $gpu 3 10 $concat_aug 42 $grid $task_name
        #bash run_v4_ERC_IEMOCAP.sh $cv $train_mode $gpu 6 5 $concat_aug 42 $grid $task_name
        #bash run_v4_ERC_IEMOCAP.sh $cv $train_mode $gpu 100 5 $concat_aug 42 $grid $task_name
    done
done
done
# echo 'END: script 01'

