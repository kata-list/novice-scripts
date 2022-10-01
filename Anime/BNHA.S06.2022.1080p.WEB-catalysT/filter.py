import vapoursynth as vs
import vsutil as u
import vskernels as k

from awsmfunc.base import bbmod
from rvsfunc.NNEDI3 import NNEDI3

core = vs.core

clip = core.lsmas.LWLibavSource('bnha.s06e01.cr.mkv')
clip = bbmod(clip, 1, 1, 1, 1)

clip_y = u.get_y(clip)
descale_y = k.Bilinear().descale(clip_y, 1280, 720)
upscale_y = NNEDI3().rpow2(descale_y)
to_1080p = k.BicubicAuto(c=-1/5).scale(upscale_y, 1920, 1080)
join_yuv = core.std.ShufflePlanes([to_1080p, clip], [0, 1, 2], vs.YUV)

clip.set_output(0)
join_yuv.set_output(1)