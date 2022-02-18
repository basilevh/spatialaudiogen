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
    metadata_fp = r'my_yt360/test_metadata_auto.txt'
    dst_fp = r'my_yt360/test_fmt_auto.txt'

    src_fns = sorted(list(os.listdir(src_dp)), key=lambda s: s.lower())
    
    # DEBUG:
    # src_fns = src_fns[-88:]

    with open(metadata_fp, 'rb') as f:
        metadatas = pickle.load(f)
    formats = dict()
    print('src_fns:', len(src_fns))

    for fn in tqdm.tqdm(src_fns):

        print(fn)
        
        try:

            src_fp = os.path.join(src_dp, fn)

            youtube_id = fn.split('.')[0]

            metadata = metadatas[youtube_id]

            codec_name = metadata['audio']['codec_name']
            projection = '?'
            stereo = 'mono'
            
            if 'side_data_type' in metadata['video']:
                side_data_type = metadata['video']['side_data_type']
                if side_data_type == 'Spherical Mapping':
                    projection = 'ER'
                elif side_data_type == 'Stereo 3D':
                    projection = 'EAC'
                else:
                    projection = side_data_type

            if 'TAG:stereo_mode' in metadata['video']:
                stereo = metadata['video']['TAG:stereo_mode']

            formats[youtube_id] = codec_name + ' ' + stereo + ' ' + projection
            
            print('stereo:', stereo)
            print('projection:', projection)
            # if 'type' in metadata['video']:
            #     print('type:', metadata['video']['type'])
            print('')

        except Exception as e:

            print('FAIL!')
            print(e)
            print('')

        pass

    formats_lines = [k + ' ' + v + '\n' for (k, v) in formats.items()]
    formats_lines = sorted(formats_lines, key=lambda s: s.lower())
    with open(dst_fp, 'w') as f:
        f.writelines(formats_lines)

    print('')
    print('projections / formats written to:', dst_fp)
    print('Done!')
    print('')

    pass


if __name__ == '__main__':

    main()
