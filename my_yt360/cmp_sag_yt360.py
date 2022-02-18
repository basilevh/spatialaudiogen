# BVH, Feb 2022.
# Old vs new paper: is the new dataset a strict superset or are there unique ids in old?

import os
import sys


if __name__ == '__main__':

    sag_fp = r'/proj/vondrick2/basile/scratch/spatialaudiogen/meta/spatialaudiogen_db.lst'
    yt_train_fp = r'/proj/vondrick/datasets/YouTube-360/train.txt'
    yt_test_fp = r'/proj/vondrick/datasets/YouTube-360/test.txt'
    
    with open(sag_fp) as f:
        sag_list = f.readlines()
    with open(yt_train_fp) as f:
        yt_train_list = f.readlines()
    with open(sag_fp) as f:
        yt_test_list = f.readlines()

    # Merge splits.
    yt_list = yt_train_list + yt_test_list

    # Remove empty ids and line breaks.
    sag_list = [x[:-1] for x in sag_list if len(x) > 1]
    yt_list = [x[:-1] for x in yt_list if len(x) > 1]

    # Remove duplicate ids.
    sag_list = sorted(list(set(sag_list)))
    yt_list = sorted(list(set(yt_list)))

    print('')
    print('sag_list:', len(sag_list))  # 1189
    print('yt_list:', len(yt_list))  # 4772
    print('')
    
    print('sag_list:', sag_list[:6], '...', sag_list[-6:])
    print('yt_list:', yt_list[:6], '...', yt_list[-6:])
    print('')

    print('intersection:', len(set(sag_list) & set(yt_list)))  # 1189
    print('union:', len(set(sag_list) | set(yt_list)))  # 4772
    print('')

    # Conclusion: good news: YouTube-360 (train + test together) is indeed a strict superset of
    # spatialaudiogen!
