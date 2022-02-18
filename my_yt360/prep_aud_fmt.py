# BVH, Feb 2022.

import os
import sys

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'my_yt360/'))
sys.path.append(os.path.join(os.getcwd(), 'scraping/'))

import copy
import pickle
import tqdm
from pyutils.iolib.video import getFFprobeMeta


def main():

    # src_dp = r'/proj/vondrick2/datasets/SpatialAudio360/orig'
    src_dp = r'/proj/vondrick/datasets/YouTube-360/test_raw_1080'
    dst_fp1 = r'my_yt360/test_aud_fmt_auto.txt'  # OLD / OBSOLETE, see vid fmt instead
    dst_fp2 = r'my_yt360/test_metadata_auto.txt'

    src_fns = sorted(list(os.listdir(src_dp)))
    metadatas = dict()
    codec_names = dict()
    print('src_fns:', len(src_fns))

    for fn in tqdm.tqdm(src_fns):

        print(fn)
        
        try:

            src_fp = os.path.join(src_dp, fn)

            youtube_id = fn.split('.')[0]

            metadata = copy.deepcopy(getFFprobeMeta(src_fp))
            
            metadatas[youtube_id] = metadata
            codec_names[youtube_id] = metadata['audio']['codec_name']
            
            print(metadata['audio']['codec_name'])
            print('')

        except:

            print('FAIL!')
            print('')

        pass

    codec_names_lines = [k + ' ' + v + '\n' for (k, v) in codec_names.items()]
    codec_names_lines = sorted(codec_names_lines, key=lambda s: s.lower())
    with open(dst_fp1, 'w') as f:
        f.writelines(codec_names_lines)
    with open(dst_fp2, 'wb') as f:
        pickle.dump(metadatas, f)

    print('')
    print('codec_names written to:', dst_fp1)
    print('metadatas written to:', dst_fp2)
    print('Done!')
    print('')

    pass


if __name__ == '__main__':

    main()
