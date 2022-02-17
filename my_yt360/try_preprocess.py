# BVH, Feb 2022.
# Adapted from scraping/preprocess.py.


import os
import sys

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'my_yt360/'))
sys.path.append(os.path.join(os.getcwd(), 'scraping/'))

import pathlib
import tempfile
import glob
import argparse
import shutil
import numpy as np
from skimage import io as sio
from pyutils.iolib.video import getFFprobeMeta
from utils import gen_eac2eqr_maps, save_pgm
from pyutils.iolib.audio import save_wav, AudioReader
from pyutils.iolib.video import VideoReader
import feeder
import multiprocessing as mp


def main():

    # stereopsis = MONO / STEREO.
    # projection = ER / EAC.
    # audioenc = aac / opus / vorbis.

    # Try SA raw => works
    if 0:
        src_vid_fp = r'/proj/vondrick2/datasets/SpatialAudio360/orig/z_RHMC7qAJM.video.mp4'
        src_aud_fp = r'/proj/vondrick2/datasets/SpatialAudio360/orig/z_RHMC7qAJM.audio.f327.m4a'
        dst_vid_fp = r'/proj/vondrick/datasets/YouTube-360/prep_test/SA.z_RHMC7qAJM.video.mp4'
        dst_aud_fp = r'/proj/vondrick/datasets/YouTube-360/prep_test/SA.z_RHMC7qAJM.ambix.m4a'

        dst_dp = str(pathlib.Path(dst_vid_fp).parent)
        if not os.path.exists(dst_dp):
            os.makedirs(dst_dp)

        stereopsis = 'MONO'
        projection = 'EAC'
        audioenc = 'aac'

        prepare_video(src_vid_fp, stereopsis, projection,
                      dst_vid_fp, (224, 448), 10, overwrite=True)
        prepare_ambisonics(src_aud_fp, dst_aud_fp, audioenc, overwrite=True)

    # Try YT raw:
    if 1:
        src_vid_fp = r'/proj/vondrick/datasets/YouTube-360/test_raw_1080/Zzv73j1pFMM.webm'
        src_aud_fp = src_vid_fp
        dst_vid_fp = r'/proj/vondrick/datasets/YouTube-360/prep_test/YT.Zzv73j1pFMM.video.mp4'
        dst_aud_fp = r'/proj/vondrick/datasets/YouTube-360/prep_test/YT.Zzv73j1pFMM.ambix.m4a'

        stereopsis = 'MONO'
        projection = 'EAC'
        audioenc = 'opus'

        prepare_video(src_vid_fp, stereopsis, projection,
                      dst_vid_fp, (224, 448), 10, overwrite=True)
        prepare_ambisonics(src_aud_fp, dst_aud_fp, audioenc, overwrite=True)

    pass


# ==================================
# Below is copied from preprocess.py
# ==================================

def prepare_ambisonics(inp_fn, out_fn, inp_codec, overwrite=False):
    if overwrite and os.path.exists(out_fn):
        os.remove(out_fn)
    if not overwrite and os.path.exists(out_fn):
        return
    assert not os.path.exists(out_fn)

    cmd = 'ffmpeg -y -i "{}" -vn -ar 48000'.format(inp_fn)
    if inp_codec == 'aac':
        remap = [2, 1, 4, 0]
    elif inp_codec in ('vorbis', 'opus'):
        remap = [0, 1, 2, 3]
    else:
        raise ValueError, '{}: Unknown input codec: {}.'.format(inp_fn, inp_codec)
    cmd += ' -af "pan=4c|c0=c{}|c1=c{}|c2=c{}|c3=c{}"'.format(*remap)
    cmd += ' "{}"'.format(out_fn)

    print("\nINPUT:", inp_fn, inp_codec)
    print("COMMAND:", cmd)
    print("")
    stdout = os.popen(cmd).read()


def prepare_video(inp_fn, stereopsis, projection, out_fn, out_shape, out_rate, overwrite=False):
    if overwrite and os.path.exists(out_fn):
        os.remove(out_fn)
    if not overwrite and os.path.exists(out_fn):
        return
    assert not os.path.exists(out_fn)

    meta = getFFprobeMeta(inp_fn)['video']
    height, width = int(meta['height']), int(meta['width'])

    inputs = [inp_fn]
    filter_chain = []
    if projection == 'ER':
        # Split stereo if necessary and scale down
        if stereopsis == 'STEREO':
            filter_chain.append('crop=in_w:in_h/2:0:0')
        filter_chain.append('scale={}:{}'.format(out_shape[1], out_shape[0]))

    elif projection == 'EAC':
        xmap_fn = 'scraping/pgms/xmap_{}x{}_{}x{}_{}.pgm'.format(
            height, width, out_shape[0] * 2, out_shape[1] * 2, stereopsis)
        ymap_fn = 'scraping/pgms/ymap_{}x{}_{}x{}_{}.pgm'.format(
            height, width, out_shape[0] * 2, out_shape[1] * 2, stereopsis)
        if not os.path.isfile(xmap_fn) or not os.path.isfile(ymap_fn):
            # Generate coord maps
            xmap, ymap = gen_eac2eqr_maps(
                (height, width), (out_shape[0] * 2, out_shape[1] * 2), stereopsis)

            # Save coord maps
            with open(xmap_fn, 'w') as f:
                save_pgm(f, xmap.astype(np.uint16), 2**16 - 1)

            with open(ymap_fn, 'w') as f:
                save_pgm(f, ymap.astype(np.uint16), 2**16 - 1)

        inputs.extend([xmap_fn, ymap_fn])

    # Run ffmpeg
    cmd = ['ffmpeg -y -ss 0']
    for inp in inputs:
        cmd += ['-i', '"' + inp + '"']
    cmd += ['-an', '-r', str(out_rate)]  # 10, 30
    if projection == 'EAC':
        cmd += ['-lavfi', 'remap']
    else:
        # Remap+pix_fmt turns image into gray-scale ????
        cmd += ['-pix_fmt', 'yuv420p']

    if filter_chain:
        cmd += ['-vf', ','.join(filter_chain)]
    cmd += ['"' + out_fn + '"']

    print(' '.join(cmd))
    stdout = os.popen(' '.join(cmd)).read()

    # Clean pgm files
    if projection == 'EAC':
        tmp_fn = tempfile.NamedTemporaryFile(prefix='/tmp/', suffix='.mp4', delete=False)
        tmp_fn.close()
        os.system('mv {} {}'.format(out_fn, tmp_fn.name))
        stdout = os.popen('ffmpeg -i "{}" -pix_fmt yuv420p -vf scale={}:{} "{}"'.format(
            tmp_fn.name, out_shape[1], out_shape[0], out_fn)).read()
        os.remove(tmp_fn.name)


if __name__ == '__main__':

    main()
