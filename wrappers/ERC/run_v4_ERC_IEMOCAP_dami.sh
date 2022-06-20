#!/bin/bash

echo 'START: script 02'

set -x

cv=$1
train_mode=$2
num_gpus=${3-1}
batch_size=${4-6}
gacc=${5-1}
concat_aug=${6--1}
seed=${7-42}
use_grid=${8-True}
task_name=${9-ConvClassif_Longformer}

######### paramters previously set as default.
# Now, you would like to write them per task to avoid danger of bugs. 
# Keeping it here as just a reference 

#corpus=IEMOCAP_v2 #_CV_${cv}
#no_epochs=50
#max_sequence_length=512
#frame_len=0.1
#results_suffix=.pkl
#model_name=longformer
#pre_trained_model=False
#test_file=test.tsv
#############################

emospotloss_wt=-100
emospot_concat=False
main_exp_dir=/export/c01/dkazeem/daseg_erc/daseg/journal_v2
# main_exp_dir=/export/c02/rpapagari/daseg_erc/daseg/journal_v2
label_smoothing_alpha=0
full_speech=False
classwts=1

##########
# you should have tasks for longformer, bilstm, ResNet, xformer, 2-stage training of ResNet and longformer
# uttclassif, conversations
# IEMOCAP, SWBD
# 

# corpus, max_sequence_length, model_name, pre_trained_model, frame_len, data_dir, no_epochs, suffix, test_file, results_suffix

######################## convclassif    #############################

if [[ $task_name == IEMOCAP_UttClassif_ResNet_longformer_2stages ]]; then
## convclassif with x-vector features   #####
    corpus=IEMOCAP_v2
    max_sequence_length=512
    model_name=longformer
    pre_trained_model=False
    xvector_model_id=SoTAEnglishXVector_IsolatedUttTraining_run1
    data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/xvectorfeat_data_dirs/${xvector_model_id}/data_v2_ERC_NoInfreqEmo_ExciteMapHap_fs10ms_clean_noise123_music123/cv_${cv}
    no_epochs=100
    frame_len=0.08
    suffix=${xvector_model_id}_ASHNF_ExciteMapHap_clean_noise123_music123_frame_len${frame_len}_ConvClassif_bs${batch_size}_gacc${gacc}_concat_aug_${concat_aug}_warmup200steps_${model_name}
    test_file=test.tsv
    results_suffix=.pkl
fi

if [[ $task_name == IEMOCAP_ConvClassif_Longformer ]]; then
    corpus=IEMOCAP_v2
    max_sequence_length=512
    model_name=longformer
    pre_trained_model=False
    frame_len=0.1
    data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ERC_NoInfreqEmo_ExciteMapHap_clean_noise123_music123/cv_${cv}
    no_epochs=100
    #suffix=_ASHNF_ExciteMapHap_clean_noise123_music123_frame_len${frame_len}_ConvClassif_bs${batch_size}_gacc${gacc}_concat_aug_${concat_aug}
    suffix=_ASHNF_ExciteMapHap_clean_noise123_music123_frame_len${frame_len}_ConvClassif_bs${batch_size}_gacc${gacc}_concat_aug_${concat_aug}_warmup200steps
    #suffix=_ASHNF_ExciteMapHap_clean_noise123_music123_frame_len${frame_len}_ConvClassif_bs${batch_size}_gacc${gacc}_concat_aug_${concat_aug}_warmup200steps_temp
    test_file=test.tsv
    results_suffix=.pkl
    results_suffix=temp.pkl
fi

if [[ $task_name == IEMOCAP_ConvClassif_BERT ]]; then
    corpus=IEMOCAP_v2
    max_sequence_length=512
    model_name=ERCTransformerBERT
    pre_trained_model=False
    frame_len=0.1
    data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ERC_NoInfreqEmo_ExciteMapHap_clean_noise123_music123/cv_${cv}
    no_epochs=100
    suffix=_ASHNF_ExciteMapHap_clean_noise123_music123_frame_len${frame_len}_ConvClassif_bs${batch_size}_gacc${gacc}_concat_aug_${concat_aug}_warmup200steps_${model_name}
    test_file=test.tsv
    results_suffix=.pkl
fi

if [[ $task_name == IEMOCAP_ConvClassif_Longformer_spkrind ]]; then
    corpus=IEMOCAP_v2
    #max_sequence_length=512
    #model_name=longformer
    #pre_trained_model=False
    #frame_len=0.1
    #data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ERC_NoInfreqEmo_ExciteMapHap_clean_noise123_music123/cv_${cv}
    #no_epochs=100
    #suffix=_ASHNF_ExciteMapHap_clean_noise123_music123_frame_len${frame_len}_ConvClassif_bs${batch_size}_gacc${gacc}_concat_aug_${concat_aug}
    #suffix=_ASHNF_ExciteMapHap_clean_noise123_music123_frame_len${frame_len}_ConvClassif_bs${batch_size}_gacc${gacc}_concat_aug_${concat_aug}_warmup200steps
    #test_file=test.tsv
    #results_suffix=.pkl
fi

if [[ $task_name == IEMOCAP_ConvClassif_bilstm ]]; then
    corpus=IEMOCAP_v2
    max_sequence_length=512
    model_name=bilstm
    pre_trained_model=False
    frame_len=0.1
    data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ERC_NoInfreqEmo_ExciteMapHap_clean_noise123_music123/cv_${cv}
    no_epochs=100
    suffix=_ASHNF_ExciteMapHap_clean_noise123_music123_frame_len${frame_len}_ConvClassif_bs${batch_size}_gacc${gacc}_concat_aug_${concat_aug}_${model_name}
    suffix=_ASHNF_ExciteMapHap_clean_noise123_music123_frame_len${frame_len}_ConvClassif_bs${batch_size}_gacc${gacc}_concat_aug_${concat_aug}_${model_name}_debug
    test_file=test.tsv
    results_suffix=.pkl
fi

if [[ $task_name == IEMOCAP_ConvClassif_ResNet ]]; then
    data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ERC_NoInfreqEmo_ExciteMapHap_fs10ms_clean_noise123_music123/cv_${cv}
    no_epochs=100
    frame_len=0.01
    model_name=ResNet
    max_sequence_length=2048
    xvector_model_id=_SoTAEnglishXVector
    pre_trained_model=True #False #True
    pre_train_suffix=${xvector_model_id}${pre_trained_model}
    suffix=${pre_train_suffix}_ASHNF_ExciteMapHap_clean_noise123_music123_frame_len${frame_len}_ConvClassif_bs${batch_size}_gacc${gacc}_concat_aug_${concat_aug}_${model_name}_maxseqlen_${max_sequence_length}
    
    
    ###################### convclassif with smoothed_overlap_silence_OOS    #############################
    #data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ERC_ExciteMapHap_smoothed_overlap_silence_OOS_clean_noise123_music123/cv_${cv}
    #no_epochs=100
    ##suffix=_ASHNF_ExciteMapHap_clean_noise123_music123_frame_len${frame_len}_ConvClassif_bs${batch_size}_gacc${gacc}_concat_aug_${concat_aug}_warmup200steps_smoothed_overlap_silence_OOS
    ##results_suffix=.pkl
    #
    #label_smoothing_alpha=0.05 # 0.1
    #suffix=_ASHNF_ExciteMapHap_clean_noise123_music123_frame_len${frame_len}_ConvClassif_bs${batch_size}_gacc${gacc}_concat_aug_${concat_aug}_warmup200steps_smoothed_overlap_silence_OOS_labelsmoothing${label_smoothing_alpha}
    #
    #data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ASHNF_ExciteMapHap_fs100ms_clean_noise123_music123/cv_${cv}
    #results_suffix=_ASHNF_UttEval_fs100ms.pkl
fi



if [[ $task_name == IEMOCAP_ConvClassif_xformer_NoInfreqEmo ]]; then
####################  convclassif with xformer and fs=10ms  ######################
    corpus=IEMOCAP_v2
    no_epochs=100
    frame_len=0.01
    model_name=xformer
    max_sequence_length=2048
    xvector_model_id=_SoTAEnglishXVector
    pre_trained_model=True #False #True
    pre_train_suffix=${xvector_model_id}${pre_trained_model}
    test_file=test.tsv
    results_suffix=_with_uttids.pkl

    data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ERC_NoInfreqEmo_ExciteMapHap_fs10ms_clean_noise123_music123/cv_${cv}
    suffix=${pre_train_suffix}_ASHNF_ExciteMapHap_clean_noise123_music123_frame_len${frame_len}_ConvClassif_bs${batch_size}_gacc${gacc}_concat_aug_${concat_aug}_warmup200steps_${model_name}_maxseqlen_${max_sequence_length}

    if [[ $eval == 1 ]]; then
        data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ASHNF_ExciteMapHap_fs10ms_clean_noise123_music123/cv_${cv}
        results_suffix=_ASHNF_ExciteMapHap_fs10ms_UttEval.pkl
    fi
fi

if [[ $task_name == IEMOCAP_ConvClassif_xformer_smoothed_overlap_silenceNone_OOSNone_spkrind ]]; then
####################  convclassif with xformer and fs=10ms  ######################
    corpus=IEMOCAP_v2
    no_epochs=100
    frame_len=0.01
    model_name=xformer
    max_sequence_length=2048
    xvector_model_id=_SoTAEnglishXVector
    pre_trained_model=True #False #True
    pre_train_suffix=${xvector_model_id}${pre_trained_model}
    test_file=test.tsv
    results_suffix=_with_uttids.pkl

    data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ERC_ExciteMapHap_smoothed_overlap_silenceNone_OOSNone_spkrind_fs10ms_clean_noise123_music123/cv_${cv}
    suffix=${pre_train_suffix}_ASHNF_ExciteMapHap_clean_noise123_music123_frame_len${frame_len}_ConvClassif_bs${batch_size}_gacc${gacc}_concat_aug_${concat_aug}_warmup200steps_${model_name}_maxseqlen_${max_sequence_length}_smoothed_overlap_silenceNone_OOSNone_spkrind
    #full_speech=True
    results_suffix=_with_uttids.pkl


    ################## only for evaluation
    #data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ERC_ExciteMapHap_smoothed_overlap_silenceNone_OOSNone_SpkrM_fs10ms_clean_noise123_music123/cv_${cv}
    #results_suffix=_with_uttids_SpkrM.pkl
    #data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ERC_ExciteMapHap_smoothed_overlap_silenceNone_OOSNone_SpkrF_fs10ms_clean_noise123_music123/cv_${cv}
    #results_suffix=_with_uttids_SpkrF.pkl
    #############
 
fi

if [[ $task_name == IEMOCAP_ConvClassif_xformer_smoothed_overlap_silenceNone_OOSNone ]]; then
####################  convclassif with xformer and fs=10ms  ######################
    corpus=IEMOCAP_v2
    no_epochs=100
    frame_len=0.01
    model_name=xformer
    max_sequence_length=2048
    xvector_model_id=_SoTAEnglishXVector
    pre_trained_model=True #False #True
    pre_train_suffix=${xvector_model_id}${pre_trained_model}
    test_file=test.tsv
    results_suffix=_with_uttids.pkl

    data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ERC_ExciteMapHap_smoothed_overlap_silenceNone_OOSNone_fs10ms_clean_noise123_music123/cv_${cv}
    suffix=${pre_train_suffix}_ASHNF_ExciteMapHap_clean_noise123_music123_frame_len${frame_len}_ConvClassif_bs${batch_size}_gacc${gacc}_concat_aug_${concat_aug}_warmup200steps_${model_name}_maxseqlen_${max_sequence_length}_smoothed_overlap_silenceNone_OOSNone
    ##full_speech=True
    results_suffix=_with_uttids.pkl
    
    ################## only for evaluation
    #data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ERC_ExciteMapHap_smoothed_overlap_silenceNone_OOSNone_SpkrM_fs10ms_clean_noise123_music123/cv_${cv}
    #results_suffix=_with_uttids_SpkrM.pkl
    #data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ERC_ExciteMapHap_smoothed_overlap_silenceNone_OOSNone_SpkrF_fs10ms_clean_noise123_music123/cv_${cv}
    #results_suffix=_with_uttids_SpkrF.pkl
    ################
fi

if [[ $task_name == IEMOCAP_ConvClassif_XFormerAddSpeakerEmb_smoothed_overlap_silenceNone_OOSNone ]]; then
####################  convclassif with xformer and fs=10ms  ######################
    corpus=IEMOCAP_v2
    no_epochs=100
    frame_len=0.01
    model_name=XFormerAddSpeakerEmb
    max_sequence_length=2048
    xvector_model_id=_SoTAEnglishXVector
    pre_trained_model=True #False #True
    pre_train_suffix=${xvector_model_id}${pre_trained_model}
    test_file=test.tsv
    results_suffix=_with_uttids.pkl

    data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ERC_ExciteMapHap_smoothed_overlap_silenceNone_OOSNone_fs10ms_clean_noise123_music123/cv_${cv}
    suffix=${pre_train_suffix}_ASHNF_ExciteMapHap_NoiseAug_frame_len${frame_len}_ConvClassif_bs${batch_size}_gacc${gacc}_CP_${concat_aug}_${model_name}_maxseqlen_${max_sequence_length}_smoothed_overlap_silenceNone_OOSNone
    results_suffix=_with_uttids.pkl
    
fi

if [[ $task_name == IEMOCAP_ConvClassif_XFormerAddAveSpeakerEmb_smoothed_overlap_silenceNone_OOSNone ]]; then
####################  convclassif with xformer and fs=10ms  ######################
    corpus=IEMOCAP_v2
    no_epochs=100
    frame_len=0.01
    model_name=XFormerAddAveSpeakerEmb
    max_sequence_length=2048
    xvector_model_id=_SoTAEnglishXVector
    pre_trained_model=True #False #True
    pre_train_suffix=${xvector_model_id}${pre_trained_model}
    test_file=test.tsv
    results_suffix=_with_uttids.pkl

    data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ERC_ExciteMapHap_smoothed_overlap_silenceNone_OOSNone_fs10ms_clean_noise123_music123/cv_${cv}
    suffix=${pre_train_suffix}_ASHNF_ExciteMapHap_NoiseAug_frame_len${frame_len}_ConvClassif_bs${batch_size}_gacc${gacc}_CP_${concat_aug}_${model_name}_maxseqlen_${max_sequence_length}_smoothed_overlap_silenceNone_OOSNone
    results_suffix=_with_uttids.pkl
    
fi



if [[ $task_name == IEMOCAP_ConvClassif_XFormerConcatSpeakerEmb_smoothed_overlap_silenceNone_OOSNone ]]; then
####################  convclassif with xformer and fs=10ms  ######################
    corpus=IEMOCAP_v2
    no_epochs=100
    frame_len=0.01
    model_name=XFormerConcatSpeakerEmb
    max_sequence_length=2048
    xvector_model_id=_SoTAEnglishXVector
    pre_trained_model=True #False #True
    pre_train_suffix=${xvector_model_id}${pre_trained_model}
    test_file=test.tsv
    results_suffix=_with_uttids.pkl

    data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ERC_ExciteMapHap_smoothed_overlap_silenceNone_OOSNone_fs10ms_clean_noise123_music123/cv_${cv}
    suffix=${pre_train_suffix}_ASHNF_ExciteMapHap_NoiseAug_frame_len${frame_len}_ConvClassif_bs${batch_size}_gacc${gacc}_CP_${concat_aug}_${model_name}_maxseqlen_${max_sequence_length}_smoothed_overlap_silenceNone_OOSNone
    results_suffix=_with_uttids.pkl
    
fi

if [[ $task_name == IEMOCAP_ConvClassif_XFormerConcatAveSpeakerEmb_smoothed_overlap_silenceNone_OOSNone ]]; then
####################  convclassif with xformer and fs=10ms  ######################
    corpus=IEMOCAP_v2
    no_epochs=100
    frame_len=0.01
    model_name=XFormerConcatAveSpeakerEmb
    max_sequence_length=2048
    xvector_model_id=_SoTAEnglishXVector
    pre_trained_model=True #False #True
    pre_train_suffix=${xvector_model_id}${pre_trained_model}
    test_file=test.tsv
    results_suffix=_with_uttids.pkl

    data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ERC_ExciteMapHap_smoothed_overlap_silenceNone_OOSNone_fs10ms_clean_noise123_music123/cv_${cv}
    suffix=${pre_train_suffix}_ASHNF_ExciteMapHap_NoiseAug_frame_len${frame_len}_ConvClassif_bs${batch_size}_gacc${gacc}_CP_${concat_aug}_${model_name}_maxseqlen_${max_sequence_length}_smoothed_overlap_silenceNone_OOSNone
    results_suffix=_with_uttids.pkl
    
fi

if [[ $task_name == IEMOCAP_ConvClassif_XFormerConcatAveSpeakerEmb_smoothed_overlap_silenceNone_OOSNone_spkrind ]]; then
####################  convclassif with xformer and fs=10ms  ######################
    corpus=IEMOCAP_v2
    no_epochs=100
    frame_len=0.01
    model_name=XFormerConcatAveSpeakerEmbSpkrDiarize
    max_sequence_length=2048
    xvector_model_id=_SoTAEnglishXVector
    pre_trained_model=True #False #True
    pre_train_suffix=${xvector_model_id}${pre_trained_model}
    test_file=test.tsv
    results_suffix=_with_uttids.pkl

    data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ERC_ExciteMapHap_smoothed_overlap_silenceNone_OOSNone_spkrind_fs10ms_clean_noise123_music123/cv_${cv}
    suffix=${pre_train_suffix}_ASHNF_ExciteMapHap_NoiseAug_frame_len${frame_len}_ConvClassif_bs${batch_size}_gacc${gacc}_CP_${concat_aug}_${model_name}_maxseqlen_${max_sequence_length}_smoothed_overlap_silenceNone_OOSNone_spkrind
    results_suffix=_with_uttids.pkl
    
fi

if [[ $task_name == IEMOCAP_ConvClassif_XFormerAddAveSpeakerEmb_smoothed_overlap_silenceNone_OOSNone_spkrind ]]; then
####################  convclassif with xformer and fs=10ms  ######################
    corpus=IEMOCAP_v2
    no_epochs=100
    frame_len=0.01
    model_name=XFormerAddAveSpeakerEmbSpkrDiarize
    max_sequence_length=2048
    xvector_model_id=_SoTAEnglishXVector
    pre_trained_model=True #False #True
    pre_train_suffix=${xvector_model_id}${pre_trained_model}
    test_file=test.tsv
    results_suffix=_with_uttids.pkl

    data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ERC_ExciteMapHap_smoothed_overlap_silenceNone_OOSNone_spkrind_fs10ms_clean_noise123_music123/cv_${cv}
    suffix=${pre_train_suffix}_ASHNF_ExciteMapHap_NoiseAug_frame_len${frame_len}_ConvClassif_bs${batch_size}_gacc${gacc}_CP_${concat_aug}_${model_name}_maxseqlen_${max_sequence_length}_smoothed_overlap_silenceNone_OOSNone_spkrind
    results_suffix=_with_uttids.pkl
    
fi

if [[ $task_name == IEMOCAP_ConvClassif_XFormerConcatTokenTypeEmb_smoothed_overlap_silenceNone_OOSNone_spkrind ]]; then
####################  convclassif with xformer and fs=10ms  ######################
    corpus=IEMOCAP_v2
    no_epochs=100
    frame_len=0.01
    model_name=XFormerConcatTokenTypeEmb
    max_sequence_length=2048
    xvector_model_id=_SoTAEnglishXVector
    pre_trained_model=True #False #True
    pre_train_suffix=${xvector_model_id}${pre_trained_model}
    test_file=test.tsv
    results_suffix=_with_uttids.pkl

    data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ERC_ExciteMapHap_smoothed_overlap_silenceNone_OOSNone_spkrind_fs10ms_clean_noise123_music123/cv_${cv}
    suffix=${pre_train_suffix}_ASHNF_ExciteMapHap_NoiseAug_frame_len${frame_len}_ConvClassif_bs${batch_size}_gacc${gacc}_CP_${concat_aug}_${model_name}_maxseqlen_${max_sequence_length}_smoothed_overlap_silenceNone_OOSNone_spkrind
    results_suffix=_with_uttids.pkl
    
fi



if [[ $task_name == IEMOCAP_ConvClassif_XFormerConcatAveParamSpeakerEmb_smoothed_overlap_silenceNone_OOSNone ]]; then
####################  convclassif with xformer and fs=10ms  ######################
    corpus=IEMOCAP_v2
    no_epochs=100
    frame_len=0.01
    model_name=XFormerConcatAveParamSpeakerEmb
    max_sequence_length=2048
    xvector_model_id=_SoTAEnglishXVector
    pre_trained_model=True #False #True
    pre_train_suffix=${xvector_model_id}${pre_trained_model}
    test_file=test.tsv
    results_suffix=_with_uttids.pkl

    data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ERC_ExciteMapHap_smoothed_overlap_silenceNone_OOSNone_fs10ms_clean_noise123_music123/cv_${cv}
    suffix=${pre_train_suffix}_ASHNF_ExciteMapHap_NoiseAug_frame_len${frame_len}_ConvClassif_bs${batch_size}_gacc${gacc}_CP_${concat_aug}_${model_name}_maxseqlen_${max_sequence_length}_smoothed_overlap_silenceNone_OOSNone_20AveWindow
    results_suffix=_with_uttids.pkl
fi



if [[ $task_name == IEMOCAP_ConvClassif_xformer_cnnop_segpool_smoothed_overlap_silence_OOSNone_spkrind ]]; then
    #data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ERC_NoInfreqEmo_ExciteMapHap_fs10ms_clean_noise123_music123/cv_${cv}
    corpus=IEMOCAP_v2
    no_epochs=100
    frame_len=0.01
    model_name=xformer_cnnop_segpool #xformersegpool
    max_sequence_length=2048
    xvector_model_id=_SoTAEnglishXVector
    pre_trained_model=True #False #True
    pre_train_suffix=${xvector_model_id}${pre_trained_model}
    results_suffix=_with_uttids.pkl

    data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ERC_ExciteMapHap_smoothed_overlap_silence_OOSNone_spkrind_fs10ms_clean_noise123_music123/cv_${cv}
    suffix=${pre_train_suffix}_ASHNF_ExciteMapHap_NoiseAug_frame_len${frame_len}_ConvClassif_bs${batch_size}_gacc${gacc}_CP_${concat_aug}_${model_name}_maxseqlen_${max_sequence_length}_smoothed_overlap_silence_OOSNone_spkrind_PoolSegments
    suffix=${pre_train_suffix}_ASHNF_ExciteMapHap_NoiseAug_frame_len${frame_len}_ConvClassif_bs${batch_size}_gacc${gacc}_CP_${concat_aug}_${model_name}_maxseqlen_${max_sequence_length}_smoothed_overlap_silence_OOSNone_spkrind_PoolSegments_debug
    test_file=test.tsv
    results_suffix=_with_uttids.pkl

    #data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ERC_ExciteMapHap_smoothed_overlap_silenceNone_OOSNone_spkrind_fs10ms_clean_noise123_music123/cv_${cv}
    #suffix=${pre_train_suffix}_ASHNF_ExciteMapHap_NoiseAug_frame_len${frame_len}_ConvClassif_bs${batch_size}_gacc${gacc}_CP_${concat_aug}_${model_name}_maxseqlen_${max_sequence_length}_smoothed_overlap_silenceNone_OOSNone_spkrind_PoolSegments
    #results_suffix=_with_uttids.pkl
fi 


######################   uttclassif   #############################
if [[ $task_name == IEMOCAP_UttClassif_longformer ]]; then
    corpus=IEMOCAP_v2
    max_sequence_length=512
    model_name=longformer
    pre_trained_model=False
    frame_len=0.1
    no_epochs=100
    test_file=test.tsv

    data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ASHNF_ExciteMapHap_fs100ms_clean_noise123_music123/cv_${cv}
    
    suffix=_ASHNF_ExciteMapHap_clean_noise123_music123_frame_len${frame_len}_UttClassif_bs${batch_size}_gacc${gacc}_concat_aug_${concat_aug}_warmup200steps
    results_suffix=.pkl

    data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ERC_NoInfreqEmo_ExciteMapHap_clean_noise123_music123/cv_${cv}
    results_suffix=_conversations.pkl
fi

if [[ $task_name == IEMOCAP_UttClassif_bilstm ]]; then
    ##data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ASHNF_ExciteMapHap_fs100ms/cv_${cv}
    data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ASHNF_ExciteMapHap_fs100ms_clean_noise123_music123/cv_${cv}
    corpus=IEMOCAP_v2
    no_epochs=100
    max_sequence_length=512
    frame_len=0.1
    pre_trained_model=False
    model_name=bilstm    
    test_file=test.tsv

    suffix=_ASHNF_ExciteMapHap_clean_noise123_music123_frame_len${frame_len}_UttClassif_bs${batch_size}_gacc${gacc}_concat_aug_${concat_aug}_${model_name}
    results_suffix=.pkl
    
    #data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ERC_NoInfreqEmo_ExciteMapHap_clean_noise123_music123/cv_${cv}
    #results_suffix=_conversations.pkl
fi

if [[ $task_name == IEMOCAP_UttClassif_ResNet ]]; then
    data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ASHNF_ExciteMapHap_fs10ms_clean_noise123_music123/cv_${cv}
    corpus=IEMOCAP_v2
    no_epochs=100
    frame_len=0.01
    model_name=ResNet
    max_sequence_length=2048
    xvector_model_id=_SoTAEnglishXVector
    pre_trained_model=True #False #True
    pre_train_suffix=${xvector_model_id}${pre_trained_model}
    suffix=${pre_train_suffix}_ASHNF_ExciteMapHap_clean_noise123_music123_frame_len${frame_len}_UttClassif_bs${batch_size}_gacc${gacc}_concat_aug_${concat_aug}_${model_name}_maxseqlen_${max_sequence_length}
    test_file=test.tsv    
    results_suffix=.pkl

    #data_dir=/export/b15/rpapagari/Tianzi_work/IEMOCAP_dataset/data_v2_ERC_NoInfreqEmo_ExciteMapHap_fs10ms_clean_noise123_music123/cv_${cv}
    #results_suffix=_conversations.pkl
fi



for label_scheme in Exact #E IE # Exact
do
for segmentation_type in smooth #fine #smooth
do
    python daseg/bin/run_journal_jobs_dami.py \
            --data-dir $data_dir \
            --exp-dir ${main_exp_dir}/${corpus}_CV_${cv}_${label_scheme}LabelScheme_${segmentation_type}Segmentation${suffix}/${model_name}_${corpus}_${seed} \
            --train-mode $train_mode --frame-len $frame_len \
            --label-scheme $label_scheme --segmentation-type $segmentation_type \
            --max-sequence-length $max_sequence_length \
            --use-grid $use_grid \
            --num-gpus $num_gpus \
            --batch-size $batch_size \
            --gacc $gacc \
            --results-suffix $results_suffix \
            --concat-aug $concat_aug \
            --corpus $corpus \
            --emospotloss-wt $emospotloss_wt \
            --no-epochs $no_epochs \
            --emospot-concat $emospot_concat \
            --seed $seed \
            --label-smoothing-alpha $label_smoothing_alpha \
            --model-name $model_name \
            --pre-trained-model $pre_trained_model \
            --test-file $test_file \
            --full-speech $full_speech \
            --classwts $classwts
done
done

echo 'END: script 02'

