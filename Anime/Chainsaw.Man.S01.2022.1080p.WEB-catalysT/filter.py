import vapoursynth as vs
import vstools as t
import vskernels as k
from rvsfunc.NNEDI3 import NNEDI3

core = vs.core

clip = core.lsmas.LWLibavSource('chainsaw.man.s01e01.cr-web.mkv')

nh = 844
nw = (16/9)*nh

clip32 = t.initialize_clip(clip, 32)
clip_y = t.get_y(clip32)
desc_y = k.Bilinear.descale(clip_y, nw, nh)
upsc_y = NNEDI3().rpow2(desc_y)
resc_y = k.Hermite.scale(upsc_y, 1920, 1080)

descale_error = k.Bilinear.scale(desc_y, 1920, 1080)

desc_mask = core.akarin.Expr([clip_y, descale_error], 'x y - abs')
desc_mask = desc_mask.std.Binarize(0.04)
desc_mask = t.iterate(desc_mask, core.std.Maximum, 10)
desc_mask = t.iterate(desc_mask, core.std.Inflate, 4)

masked_resc = core.std.MaskedMerge(resc_y, clip_y, desc_mask)

op_ed = [(3237, 5394), (34405, 35564)]

exclude_op_ed = t.replace_ranges(masked_resc, clip_y, ranges=op_ed)

resc_y = exclude_op_ed

join_yuv = core.std.ShufflePlanes([resc_y, clip32], [0, 1, 2], vs.YUV)

clip.set_output(0)
join_yuv.set_output(1)