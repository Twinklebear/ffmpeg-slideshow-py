# FFmpeg Slideshow.py

Easily make a slideshow with crossfade transitions using ffmpeg via [ffmpeg-python](https://github.com/kkroening/ffmpeg-python).

The filter graph can be quite complex and the image->video conversion step is slow in FFmpeg.
To accelerate this process, the images are converted to 1s mp4 clips in `/tmp/`. Images are
converted in parallel asynchronously, as this step is roughly serial in FFmpeg.

The converted video files are much faster for FFmpeg to work with in the slideshow filter
graph, allowing the second step with the complex filter graph to be processed much faster as well.

# Example

This [video example](https://youtu.be/UwBLugxc73Y) was produced from 3 images by running:

```bash
./slideshow.py 5 1920 1080 out.mp4 DSCF9554.jpg DSCF9566.jpg DSCF9568.jpg
```

The image conversion filter graphs are shown below, which each generate a 1s clip to do the
image->video conversion and 1920x1080 resizing and padding operations:

![tmpif5hu1r5](https://github.com/Twinklebear/ffmpeg-slideshow-py/assets/1522476/f8e2ca2f-786d-4abe-bd87-430725b2bb35)
![tmp7ubuu_pg](https://github.com/Twinklebear/ffmpeg-slideshow-py/assets/1522476/ae742f0b-8e51-4b78-98f2-614305b4f31d)
![tmp4l7kpa1q](https://github.com/Twinklebear/ffmpeg-slideshow-py/assets/1522476/2ec15c33-1a37-4e03-b29f-fd88c8e647a9)

The generated 1s temporary video clips are then fed into a larger filter graph that
applies the fades, offsets (setpts) and overlays the clips on top of each other:

![tmp6hfrt5ll](https://github.com/Twinklebear/ffmpeg-slideshow-py/assets/1522476/f2390b1a-4946-4ab4-aee3-271ccc9d6222)
