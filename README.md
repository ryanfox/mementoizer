# Mementoizer

A python library to [Memento-ize](https://en.wikipedia.org/wiki/Memento_(film)) videos.

Meaning, cut the video up into scenes, pass the first half through a black-and-white filter, and interleave them.

Created for NaMoGenMo 2022. For an example, see:
https://www.youtube.com/watch?v=vkgGLhG3ccI


The original film for comparison can be viewed here:
https://en.wikipedia.org/wiki/File:The_Memphis_Belle_-_A_Story_of_a_Flying_Fortress.webm

## Installation
Mementoizer can be installed from PyPI:

`pip install mementoizer`

## Usage

Command-line usage:
`mementoize <video-filename>`

Programmatic usage:
```
from mementoizer import mementoize

mementoize(video_filename, ...)
```

### Options

`--skip-start` Number of seconds to ignore for cutting purposes at the beginning of the video file. For example, skipping intro credits. Default: 0

`--skip-end` Number of seconds to ignore for cutting purposes at the end of the video file. For example, skipping end credits. Default: 0

`--min-scene-length` Minimum number of seconds to count as a scene. If a cut is detected less than this many seconds after a previous one, it is disregarded. Default: 120 seconds

`--threshold` Parameter for tuning cut detection. Must be a float between 0 and 1. Typical values for normal shot detection are 0.4-0.6. Since we are trying to detect _scene_ boundaries rather than plain shots, it's set a little higher by default. Default: 0.7

`--overlap` Number of seconds to overlap between clips (chronologically). You will see this many seconds repeated to connect the previous scene to the one you are watching now. Default: 4

`--cuts` Manually specify cut times, in seconds after the start of the video. If this is provided, cut detection is skipped. `--skip-start`, `--skip-end`, and `--min-scene-length` are still applied. Values should be comma-separated integers.
NOTE: the resulting video will start at the first timestamp you provide. So you must start the list with `0` if you don't want to skip the first scene.

`--verbose` Print out the cut times detected (or supplied if `--cuts` is specified).

`--dry-run` Print detected cut timstamps and exit. Do not write or modify any files.
