# BVH, Feb 2022.

import os
import sys

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'my_yt360/'))
sys.path.append(os.path.join(os.getcwd(), 'scraping/'))

import librosa
import mutagen
import pathlib
import tinytag
import torchaudio
from pyutils.iolib.video import getFFprobeMeta


def main():

    src_dp = r'/proj/vondrick2/datasets/SpatialAudio360/orig'

    for fn in os.listdir(src_dp):

        if 'audio' in fn:

            print(fn)
            src_fp = os.path.join(src_dp, fn)

            # print('tinytag')
            # try:
            #     metadata = tinytag.TinyTag.get(src_fp)
            #     print(metadata.channels)
            # except:
            #     print('fail')

            # print('mutagen')
            # try:
            #     metadata = mutagen.File(src_fp)
            #     if metadata is not None:
            #         print(metadata.info.codec)
            #     else:
            #         print('None?')
            # except:
            #     print('fail')

            # print('torchaudio')
            # try:
            #     metadata = torchaudio.info(src_fp)
            #     print(metadata)
            # except:
            #     print('fail')

            # print('librosa')
            # try:
            #     y, sr = librosa.load(src_fp)
            #     print(y.shape, sr)
            # except:
            #     print('fail')

            # print('cmd ffmpeg')
            # cmd = 'ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 '
            # cmd += src_fp
            # stdout = os.popen(cmd).read()
            # print(stdout)
            
            # print('getFFprobeMeta')
            metadata = getFFprobeMeta(src_fp)['audio']
            print(metadata['codec_name'])
            
            print('')

            pass

    pass


if __name__ == '__main__':

    main()
