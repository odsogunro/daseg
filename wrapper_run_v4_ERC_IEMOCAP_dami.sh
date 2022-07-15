#!/bin/bash

# echo 'START: script 01'

# set -x

# source /home/rpapagari/.bashrc
# source activate daseg_v2


# https://linuxize.com/post/bash-comments/
<< MULTILINE-COMMENT
    1. [this wrapper]
        - script_name: wrapper_run_v4ERC_IEMOCAP.sh [OR] wrapper_run_v4ERC_IEMOCAP_dami.sh
    
    2. [calls this wrapper]
        - script_name: run_v4ERC_IEMOCAP.sh [OR] run_v4ERC_IEMOCAP_dami.sh
    
    3. [calls this wrapper]
        - script_name: run_journal_jobs.py [OR] run_journal_jobs_dami.py


    -----
    variables defined in this wrapper script
    
    concat_aug: 
        -1 for ?? 
        0  for ??
    
    task_name:

        #####
        # Utterance Classication
        #####

        [BiLSTM Models, https://arxiv.org/abs/1402.1128] 
        - RUN STATUS: Fails
            - task_name: IEMOCAP_UttClassif_bilstm
                - dataset: IEMOCAP
                - (downstream) task: Utterance Classication
                - (upstream) model: BILSTM NN

        [ResNet Models, https://arxiv.org/abs/1512.03385?context=cs]  
        - RUN STATUS: 
            - task_name: IEMOCAP_UttClassif_ResNet
                - dataset: IEMOCAP
                - (downstream) task: Utterance Classication
                - (upstream) model: ResNet CNN

        [Longformer Models, https://arxiv.org/abs/2004.05150]
        - RUN STATUS:     
            - task_name: IEMOCAP_UttClassif_longformer
                - dataset: IEMOCAP
                - (downstream) task: Utterance Classication
                - (upstream) model: Longformer
            
            - task_name: IEMOCAP_UttClassif_longformer
                - dataset: IEMOCAP
                - (downstream) task: Utterance Classication
                - (upstream) model: Longformer


        #####
        # Convultional NN Classication
        #####

        [BERT Models, https://arxiv.org/abs/1810.04805v2] 
        - RUN STATUS: Fails
            - task_name: IEMOCAP_ConvClassif_BERT
                - dataset: IEMOCAP
                - (downstream) task: CNN Classication
                - (upstream) model: BERT


        [XFormer Models, https://facebookresearch.github.io/xformers/, https://github.com/facebookresearch/xformers]
        
        - RUN STATUS: Fails
            - task_name: IEMOCAP_ConvClassif_XFormerConcatTokenTypeEmb_smoothed_overlap_silenceNone_OOSNone_spkrind
                - dataset: IEMOCAP
                - (downstream) task: CNN Classication
                - (upstream) model: XFormerConcatTokenTypeEmb
                - ?????: smoothed
                - ?????: overlap
                - ?????: silenceNone
                - ?????: OOSNone
                - ?????: spkrind

        - RUN STATUS: 
            - task_name: IEMOCAP_ConvClassif_XFormerConcatAveSpeakerEmb_smoothed_overlap_silenceNone_OOSNone_spkrind
                - dataset: IEMOCAP
                - (downstream) task: CNN Classication
                - (upstream) model: XFormerConcatAveSpeakerEmb
                - ?????: smoothed
                - ?????: overlap
                - ?????: silenceNone
                - ?????: OOSNone
                - ?????: spkrind
        
        - RUN STATUS: Fails
            - task_name: IEMOCAP_ConvClassif_xformer_NoInfreqEmo
                - dataset: IEMOCAP
                - (downstream) task: CNN Classication
                - (upstream) model: XFormer
                - ?????: NoInfreqEmo

        - RUN STATUS: 
            - task_name: IEMOCAP_ConvClassif_XFormerConcatAveParamSpeakerEmb_smoothed_overlap_silenceNone_OOSNone
                - dataset: IEMOCAP
                - (downstream) task: CNN Classication
                - (upstream) model: XFormerConcatAveParamSpeakerEmb
                - ?????: smoothed
                - ?????: overlap
                - ?????: silenceNone
                - ?????: OOSNone

        - RUN STATUS: 
            - task_name: IEMOCAP_ConvClassif_XFormerConcatAveSpeakerEmb_smoothed_overlap_silenceNone_OOSNone
                - dataset: IEMOCAP
                - (downstream) task: CNN Classication
                - (upstream) model: XFormerConcatAveSpeakerEmb
                - ?????: smoothed
                - ?????: overlap
                - ?????: silenceNone
                - ?????: OOSNone

        - RUN STATUS: Fails
            - task_name: IEMOCAP_ConvClassif_XFormerAddAveSpeakerEmb_smoothed_overlap_silenceNone_OOSNone
                - dataset: IEMOCAP
                - (downstream) task: CNN Classication
                - (upstream) model: XFormerAddAveSpeakerEmb
                - ?????: smoothed
                - ?????: overlap
                - ?????: silenceNone
                - ?????: OOSNone

        - RUN STATUS: 
            - task_name: IEMOCAP_ConvClassif_xformer_smoothed_overlap_silenceNone_OOSNone
                - dataset: IEMOCAP
                - (downstream) task: CNN Classication
                - (upstream) model: xformer
                - ?????: smoothed
                - ?????: overlap
                - ?????: silenceNone
                - ?????: OOSNone

        - RUN STATUS: 
            - task_name: IEMOCAP_ConvClassif_XFormerConcatSpeakerEmb_smoothed_overlap_silenceNone_OOSNone
                - dataset: IEMOCAP
                - (downstream) task: CNN Classication
                - (upstream) model: XFormerConcatSpeakerEmb
                - ?????: smoothed
                - ?????: overlap
                - ?????: silenceNone
                - ?????: OOSNone

        - RUN STATUS: 
            - task_name: IEMOCAP_ConvClassif_XFormerAddSpeakerEmb_smoothed_overlap_silenceNone_OOSNone
                - dataset: IEMOCAP
                - (downstream) task: CNN Classication
                - (upstream) model: XFormerAddSpeakerEmb
                - ?????: smoothed
                - ?????: overlap
                - ?????: silenceNone
                - ?????: OOSNone    
    
    train_mode:
        - TE: ?
        _ T: Train
        - E: Evaluate

    gpu: 
        - integer value

    grid:
        - boolean 0 or 1

    cv: 
        - cross validation sets numbered 1 through 5
MULTILINE-COMMENT

train_mode=TE

# << MULTILINE-COMMENT
#     - the for loop here is empty. WHY?
#     - what does -1 and 0 represent concat_aug --> concat augmentation
# MULTILINE-COMMENT

for concat_aug in -1 #0 # -1 ##-1 #-1 #-1 # 0 #-1
do

#####
# Convolutional NN Classification
#####
for task_name in IEMOCAP_ConvClassif_BERT

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


#####
# Utterance Classification
#####

# for task_name in IEMOCAP_UttClassif_bilstm 
# for task_name in IEMOCAP_UttClassif_ResNet
# for task_name in IEMOCAP_UttClassif_longformer

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

