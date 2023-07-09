#!/usr/bin/env python3

import ffmpeg
import sys
from docopt import docopt

# Take a list of images in order that they want to be displayed,
# and make a video slideshow at desired resolution and timing

# TODO: input image list from file as well
USAGE = """slideshow.py

Usage:
    slideshow.py <img_duration> <width> <height> <output.mp4> <files>...
    slideshow.py (-h | --help)

Options:
    -h --help   Show this screen
"""

encoding_args = {
    # Don't need very high bitrate for static images 
    "b:v": "2000k",
    "c:v": "libx264"
}

args = docopt(USAGE)

fade_duration = 1
# Only count half the fade time as part of the slide time
slide_duration = int(args["<img_duration>"]) + fade_duration
width = int(args["<width>"])
height = int(args["<height>"])
output = args["<output.mp4>"]

images = []
for f in args["<files>"]:
    probe = ffmpeg.probe(f)
    img_stream = probe["streams"][0]
    img_w = img_stream["width"]
    img_h = img_stream["height"]

    img = ffmpeg.input(f, loop=1, t=slide_duration)

    # Pick aspect ratio force direction based on the image size
    force_direction = "decrease" if img_w >= width or img_h >= height else "increase"

    img = (
        img
        .filter("scale", width, height, force_original_aspect_ratio=force_direction)
        .filter("pad", width, height, -1, -1)
    )
    images.append(img)


# Build the fades and offsets for the images
fades = []
for i in range(1, len(images)):
    offset = i * (slide_duration - fade_duration)
    fade = (
        images[i]
        .filter("fade", d=fade_duration, t="in", alpha=1)
        .setpts(f"PTS-STARTPTS+{offset}/TB")
    )
    fades.append(fade)

# Now build the overlay chain to fade each next image on the overlay from before
slideshow_chain = images[0]
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

