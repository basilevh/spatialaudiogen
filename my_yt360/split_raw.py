# BVH, Feb 2022.
# Run this after split_test_val is done.

import os
import sys

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'my_yt360/'))

import glob
import numpy as np
import shutil
import pathlib
import tqdm


def main():

    imitate_dp = r'/proj/vondrick/datasets/YouTube-360/prep_dset/val/'
    test_dp = r'/proj/vondrick/datasets/YouTube-360/test_raw_1080/'
    val_dp = r'/proj/vondrick/datasets/YouTube-360/val_raw_1080/'

    # if os.path.exists(val_dp):
    #     print('Destination directory (val) already exists! Exiting...')
    #     return

    if not os.path.isdir(val_dp):
        os.makedirs(val_dp, exist_ok=True)

    youtube_ids = [os.path.split(fn)[-1].split('.')[0][:-6]
                   for fn in glob.glob('{}/*-video.*'.format(imitate_dp))]
    youtube_ids = sorted(list(set(youtube_ids)))

    for id in tqdm.tqdm(youtube_ids):
        print(id)
        src_fp = os.path.join(test_dp, id + '.webm')
        
        if not os.path.exists(src_fp):
            src_fp = os.path.join(test_dp, id + '.mkv')
            
            if not os.path.exists(src_fp):
                print('Skip!')
                continue
        
        dst_fp = os.path.join(val_dp, id + '.webm')
        shutil.move(src_fp, dst_fp)

    print('Done!')


if __name__ == '__main__':

    main()
