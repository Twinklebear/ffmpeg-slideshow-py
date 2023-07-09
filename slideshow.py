#!/usr/bin/env python3

import ffmpeg
import multiprocessing
import tempfile
import os
import sys
from docopt import docopt

# Take a list of images in order that they want to be displayed,
# and make a video slideshow at desired resolution and timing

USAGE = """slideshow.py

Usage:
    slideshow.py <img_duration> <width> <height> <output.mp4> [-e <enc>] [-f <fade>] <files>...
    slideshow.py <img_duration> <width> <height> <output.mp4> [-e <enc>] [-f <fade>] -i <file>
    slideshow.py (-h | --help)

Options:
    -h --help   Show this screen
    -e <enc>    Specify the encoder to use, e.g. h264_nvenc or h264_qsv for
                hardware acceleration on Nvidia or Intel GPUs. Default is libx264 (CPU)
    -f <fade>   Specify the fade duration (default is 1), must be less than img_duration
    -i <file>   Specify the list of images are provided in a file. File should contain 1
                image name per line. Filenames are relative to the directory containing <file>
"""
args = docopt(USAGE)

encoding_args = {
    # Don't need very high bitrate for static images 
    "b:v": "3500k",
    "c:v": args["-e"] if args["-e"] else "libx264"
}

fade_duration = int(args["-f"]) if args["-f"] else 1
# Only count half the fade time as part of the slide time
slide_duration = int(args["<img_duration>"]) + fade_duration
width = int(args["<width>"])
height = int(args["<height>"])
output = args["<output.mp4>"]

input_images = []
if "<files>" in args:
    input_images = args["<files>"]
else:
    dirname = os.path.dirname(args["-i"])
    with open(args["-i"]) as f:
        input_images = [dirname + "/" + l.strip() for l in f.readlines()]

# FFmpeg is slow at looping images out to videos but fast at processing video files.
# So first generate short video clips for each image input that we'll feed in to the
# slideshow chain to accelerate it. All these image outputs are run in parallel,
# as FFmpeg seems to do it serially.
image_procs = []
# image_clips is the list of temporary video file names we've produced
image_clips = []
total_complete = 0
for f in input_images:
    img = ffmpeg.input(f, loop=1, t=1)
    clip_output = tempfile.NamedTemporaryFile(prefix="ffmpeg-slideshow-py", suffix=".mp4")
    img = (
        img
        .filter("scale", width, height, force_original_aspect_ratio="decrease")
        .filter("pad", width, height, -1, -1)
        .filter("format", pix_fmts="yuv420p")
        .output(clip_output.name, **encoding_args)
        .global_args("-hide_banner", "-loglevel", "error", "-nostdin")
        .overwrite_output()
        .run_async(quiet=True)
    )
    image_procs.append(img)
    image_clips.append(clip_output)

    # If we have 2 * # of cores processes running, wait for some to finish
    while len(image_procs) >= 2 * multiprocessing.cpu_count():
        done = [p for p in image_procs if p.poll() != None]
        image_procs = [p for p in image_procs if p.poll() == None]

        total_complete += len(done)
        if len(done) > 0:
            print(f"Completed image -> video conversions {total_complete}/{len(input_images)}")

        for d in done:
            _, err = d.communicate()
            if len(err) > 0:
                print(err.decode("utf8"))
                sys.exit(1)

print("All image -> video conversions running, waiting...")
for p in image_procs:
    p.wait()
    _, err = p.communicate()
    if len(err) > 0:
        print(err.decode("utf8"))
        sys.exit(1)

print("All image -> video conversions complete")

# Now load the image clip inputs
image_clip_inputs = [ffmpeg.input(f.name, stream_loop=slide_duration) for f in image_clips]

# Build the fades and offsets for the images
fades = []
for i in range(1, len(image_clip_inputs)):
    offset = i * (slide_duration - fade_duration)
    fade = (
        image_clip_inputs[i]
        .filter("fade", d=fade_duration, t="in", alpha=1)
        .setpts(f"PTS-STARTPTS+{offset}/TB")
    )
    fades.append(fade)

# Now build the overlay chain to fade each next image on the overlay from before
slideshow_chain = image_clip_inputs[0]
for img in fades:
    slideshow_chain = (
        ffmpeg
        .filter([slideshow_chain, img], "overlay")
    )

(
    slideshow_chain
    .filter("format", pix_fmts="yuv420p")
    .output(output, **encoding_args)
    .overwrite_output()
    .run()
)

