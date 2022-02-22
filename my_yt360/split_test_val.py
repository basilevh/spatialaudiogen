# BVH, Feb 2022.
# Run this after test_preproc is done.

import os
import sys

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'my_yt360/'))

import glob
import numpy as np
import shutil
import pathlib


def main():

    test_dp = r'/proj/vondrick/datasets/YouTube-360/test_preproc/'
    val_dp = r'/proj/vondrick/datasets/YouTube-360/val_preproc/'
    # test_fp = 'my_yt360/split_test_ids.txt'
    # val_fp = 'my_yt360/split_val_ids.txt'
    test_keep_frac = 0.65

    if os.path.exists(val_dp):
        print('Destination directory (val) already exists! Exiting...')
        return

    if not os.path.isdir(val_dp):
        os.makedirs(val_dp)

    # if not os.path.exists(val_fp):
    all_ids = [os.path.split(fn)[-1].split('.')[0][:11]
                for fn in glob.glob('{}/*-video.*'.format(test_dp))]
    all_ids = np.array(sorted(all_ids))

    num_all = len(all_ids)
    num_test = int(num_all * test_keep_frac)
    num_val = num_all - num_test

    print('')
    print('num_all:', num_all)
    print('num_test:', num_test)
    print('num_val:', num_val)
    print('')

    val_sel = np.random.choice(len(all_ids), size=num_val, replace=False)
    val_sel = np.array(sorted(val_sel))
    
    print('val_sel:', val_sel)

    val_ids = all_ids[val_sel]
    test_ids = np.array(sorted(set(all_ids).difference(set(val_ids))))
    
    print('')
    print('all_ids:', all_ids.shape, all_ids[:7])
    print('val_ids:', val_ids.shape, val_ids[:7])
    print('test_ids:', test_ids.shape, test_ids[:7])
    print('')

    for id in val_ids:
        for fn in [id + '-video.mp4', id + '-ambix.m4a']:
            src_fp = os.path.join(test_dp, fn)
            dst_fp = os.path.join(val_dp, fn)
            shutil.move(src_fp, dst_fp)

    print('Done!')


if __name__ == '__main__':

    main()
