import argparse
import itertools
import os
import re
import subprocess

import imageio_ffmpeg
from moviepy.editor import VideoFileClip, CompositeVideoClip, ColorClip, concatenate_videoclips
from moviepy.video.fx.blackwhite import blackwhite
from moviepy.video.fx.fadein import fadein


def split_scenes(clip, timestamps, overlap):
    """Split a video clip into subclips, separated at the provided timestamps"""
    clips = []
    for i in range(len(timestamps)):
        try:
            scene = clip.subclip(timestamps[i], timestamps[i + 1] + overlap)
            clips.append(fadein(scene, 0.5))
        except IndexError:
            clips.append(fadein(clip.subclip(timestamps[-1]), 0.5))

    return clips


def detect_cuts(filename, threshold):
    """
    Detect cuts in a video file, via ffmpeg's scenedetect filter
    :param filename: the video file to process
    :param threshold: the parameter to use for ffmpeg's scenedetect filter
    :return: a list of timestamps detected by ffmpeg, in seconds
    """
    ffmpeg_results = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-i', filename, '-filter:v', f'select=\'gt(scene,{threshold})\',showinfo', '-f', 'null', '-'], capture_output=True)

    timestamps = re.findall(r'pts_time:([\d.]+)', ffmpeg_results.stderr.decode())
    return [float(timestamp) for timestamp in timestamps]


def mementoize(filename, skip_start=0, skip_end=0, min_scene_length=120, threshold=0.7, overlap=4, cuts=None, verbose=False, dry_run=False):
    """
    Memento-ize a video file.

    How it works:
    1. Cut the video into scenes
    2. Black-and-white filter the first half
    3. Interleave the scenes, starting with the ends and working toward the middle
    4. When the middle is reached, fade from black and white to color to indicate the transition

    :param filename: the video file to process
    :param skip_start: how much time at the beginning of the file to declare off-limits for scene changes, in seconds
    :param skip_end: how much time at the end of the file to declare off-limits for scene changes, in seconds
    :param min_scene_length: if supplied, cuts detected less than this amount of time after the previous cut will be ignored. In seconds
    :param threshold: similarity threshold for detecting scene cuts. A float, must be between 0-1. Lower numbers mean more cuts will be detected. Typical values are .4-.6
    :param overlap: how many seconds to overlap between clips
    :param cuts: manually specify the scene times. ffmpeg is not used for scene detection in this case
    :param verbose: whether to print timestamps of each cut
    :param dry_run: if true, print detected cut timestamps and exit without writing any files. Implies verbose=True
    :return: the filename of the processed video
    """
    if not cuts:
        cuts = detect_cuts(filename, threshold)

        if verbose or dry_run:
            print('cuts detected at')
            print(cuts)

    if skip_start:
        cuts = [cut for cut in cuts if cut >= skip_start]
    if skip_end:
        cuts = [cut for cut in cuts if cut <= skip_end]

    if min_scene_length:
        new_cuts = [0]
        for cut in cuts:
            if new_cuts[-1] + min_scene_length <= cut:
                new_cuts.append(cut)

        cuts = new_cuts

    if verbose or dry_run:
        print(len(cuts), 'final cuts at:')
        print(cuts)

    if not dry_run:
        original_clip = VideoFileClip(filename)
        clips = split_scenes(original_clip, cuts, overlap)

        first_half = clips[:len(clips) // 2]
        second_half = clips[len(clips) // 2:]
        clip_order = []
        while len(first_half) > 0 or len(second_half) > 0:
            try:
                clip_order.append(second_half.pop())
            except IndexError:
                pass

            try:
                clip_order.append(first_half.pop(0))
            except IndexError:
                pass

        # bw filter the early clips
        for i in range(len(clip_order) - 2):
            if i % 2 == 1:
                clip_order[i] = blackwhite(clip_order[i])

        # handle the transition
        if len(clip_order) % 2 == 0:  # bw -> color transition happens halfway through last clip
            last_clip = clip_order[-1]
            faded_clip = CompositeVideoClip([
                blackwhite(last_clip.subclip(0, last_clip.duration / 2 + overlap)).crossfadeout(overlap),
                last_clip.subclip(last_clip.duration / 2).set_start(last_clip.duration / 2).crossfadein(overlap)
            ])
            clip_order[-1] = faded_clip

        else:  # bw -> color transition happens between last two clips
            fade_out = blackwhite(clip_order[-2]).crossfadeout(overlap)
            faded_clip = CompositeVideoClip([fade_out, clip_order[-1].set_start(fade_out.end - overlap).crossfadein(overlap)])
            clip_order[-2] = faded_clip
            del clip_order[-1]

        spacer = ColorClip(clip_order[0].size, (0, 0, 0), duration=0.5)
        final_clip_order = [item for pair in zip(clip_order, itertools.repeat(spacer)) for item in pair]
        final_clip = concatenate_videoclips(final_clip_order)

        filename_parts = os.path.splitext(filename)
        output_filename = filename_parts[0] + '_mementized' + filename_parts[1]
        final_clip.write_videofile(output_filename)
        return output_filename


def cli():
    parser = argparse.ArgumentParser(prog='Mementoizer', description='Memento-ize a video file')
    parser.add_argument('filename')
    parser.add_argument('--skip-start', type=int, help='No scene cuts allowed for this many seconds after start', default=0)
    parser.add_argument('--skip-end', type=int, help='No scene cuts allowed for this many seconds before end', default=0)
    parser.add_argument('--min-scene-length', type=int, help='Scene cuts closer together than this are not allowed (in seconds)', default=120)
    parser.add_argument('--threshold', type=float, help='Similarity threshold for scene detection. Lower values will detect more cuts. Float between 0 and 1. Typical values are 0.4-0.6', default=0.7)
    parser.add_argument('--overlap', type=int, help='Number of seconds to overlap scenes', default=4)
    parser.add_argument('--cuts', help='If supplied, use these timestamps for scene cuts rather than detecting them. Comma separated, in seconds')
    parser.add_argument('-v', '--verbose', help='verbose mode. Print timestamp for each cut', action='store_true')
    parser.add_argument('--dry-run', help='Print detected cut timestamps and exit. Don\'t write any video file or make changes. Implies --verbose.', action='store_true')
    args = parser.parse_args()

    if args.cuts:
        args.cuts = [float(timestamp.strip()) for timestamp in args.cuts.split(',')]

    mementoize(filename=args.filename,
               skip_start=args.skip_start,
               skip_end=args.skip_end,
               min_scene_length=args.min_scene_length,
               threshold=args.threshold,
               overlap=args.overlap,
               cuts=args.cuts,
               verbose=args.verbose,
               dry_run=args.dry_run)
