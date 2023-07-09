# FFmpeg Slideshow.py

Easily make a slideshow with crossfade transitions using ffmpeg via [ffmpeg-python](https://github.com/kkroening/ffmpeg-python).

The filter graph can be quite complex and the image->video conversion step is slow in FFmpeg.
To accelerate this process, the images are converted to 1s mp4 clips in `/tmp/`. Images are
converted in parallel asynchronously, as this step is roughly serial in FFmpeg.

The converted video files are much faster for FFmpeg to work with in the slideshow filter
graph, allowing the second step with the complex filter graph to be processed much faster as well.

