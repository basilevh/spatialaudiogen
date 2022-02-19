# BVH, Feb 2022.
# Adapted from scraping/preprocess.py.
# Uses custom format txt files.

import os
import sys

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'my_yt360/'))
sys.path.append(os.path.join(os.getcwd(), 'scraping/'))  # for utils etc.

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

    parser = argparse.ArgumentParser()
    parser.add_argument('--formats_fp', default='my_yt360/test_fmt_fix.txt',
                        help='File containing list of youtube ids + video + audio formats.')
    parser.add_argument('--orig_dp', default='/proj/vondrick/datasets/YouTube-360/test_raw_1080',
                        help='Folder containing raw downloaded videos.')
    parser.add_argument('--output_dp', default='/proj/vondrick/datasets/YouTube-360/test_preproc',
                        help='Output folder for preprocessed videos.')
    parser.add_argument('--num_workers', default=8, type=int,
                        help='Number of parallel workers.')
    parser.add_argument('--prep_hr_video', action='store_true',
                        help='Flag to pre-process videos in high-resolution (for deployment only).')
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args(sys.argv[1:])

    if not os.path.isdir(args.output_dp):
        os.makedirs(args.output_dp)
    if not os.path.isdir('my_yt360/pgms'):
        os.makedirs('my_yt360/pgms')

    def worker(q, gpu):
        while not q.empty():
            yid, raw_fn = q.get()
            print('=' * 10, int(q.qsize()), 'remaining', yid, '=' * 10)

            # Obtain format.
            audioenc = [l.split()[1] for l in open(args.formats_fp) if l.split()[0] == yid][0]
            stereopsis = [l.split()[2] for l in open(args.formats_fp) if l.split()[0] == yid][0]
            projection = [l.split()[3] for l in open(args.formats_fp) if l.split()[0] == yid][0]
            if projection == '?':
                projection = 'EAC'

            # Prepare audio.
            prep_audio_fn = os.path.join(args.output_dp, '{}-ambix.m4a'.format(yid))
            prepare_ambisonics(raw_fn, prep_audio_fn, audioenc, args.overwrite)

            # Prepare video.
            prep_video_fn = os.path.join(args.output_dp, '{}-video.mp4'.format(yid))
            if args.prep_hr_video:
                prepare_video(raw_fn, stereopsis, projection,
                              prep_video_fn, (1080, 1920), 30, args.overwrite)
            else:
                prepare_video(raw_fn, stereopsis, projection,
                              prep_video_fn, (224, 448), 10, args.overwrite)

    to_process = sorted([l.split()[0] for l in open(args.formats_fp)])
    youtube_files = {os.path.split(fn)[-1].split('.')[0]: fn for fn in glob.glob('{}/*.*'.format(args.orig_dp))}
    
    q = mp.Queue()
    for yid in to_process:
        if yid in youtube_files:
            q.put((yid, youtube_files[yid]))

    proc = []
    for i in range(args.num_workers):
        gpu = 0
        p = mp.Process(target=worker, args=(q, gpu))
        p.daemon = True
        p.start()
        proc.append(p)

    for p in proc:
        p.join()


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
        xmap_fn = 'my_yt360/pgms/xmap_{}x{}_{}x{}_{}.pgm'.format(
            height, width, out_shape[0] * 2, out_shape[1] * 2, stereopsis)
        ymap_fn = 'my_yt360/pgms/ymap_{}x{}_{}x{}_{}.pgm'.format(
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
