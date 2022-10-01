import vapoursynth as vs
import vsutil as u
import vskernels as k

from awsmfunc.base import bbmod
from rvsfunc.NNEDI3 import NNEDI3
from vsdehalo.alpha import fine_dehalo

core = vs.core

clip = core.lsmas.LWLibavSource('bnha.s06e01.cr.mkv')
clip = bbmod(clip, 1, 1, 1, 1)

clip_y = u.get_y(clip)

descale_y = k.Bilinear().descale(clip_y, 1280, 720)
upscale_y = NNEDI3().rpow2(descale_y)

to_1080p = k.BicubicAuto(c=-1/5).scale(upscale_y, 1920, 1080)

dehalo = fine_dehalo(to_1080p, rx=2.3, darkstr=0, brightstr=0.9)

descale_error = k.Bilinear().scale(descale_y, 1920, 1080)

desc_mask = core.std.Expr([clip_y, descale_error], 'x y - abs')
desc_mask = desc_mask.std.Binarize(8)
desc_mask = u.iterate(desc_mask, core.std.Maximum, 12)
desc_mask = u.iterate(desc_mask, core.std.Inflate, 6)

masked_rescale = core.std.MaskedMerge(dehalo, clip_y, desc_mask)

join_yuv = core.std.ShufflePlanes([masked_rescale, clip], [0, 1, 2], vs.YUV)

clip.set_output(0)
join_yuv.set_output(1)