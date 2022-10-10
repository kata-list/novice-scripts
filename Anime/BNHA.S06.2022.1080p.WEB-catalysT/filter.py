import vapoursynth as vs
import vsutil as u
import vskernels as k

from awsmfunc.base import bbmod
from rvsfunc.NNEDI3 import NNEDI3
from vsdehalo.alpha import fine_dehalo
from dfttest2 import DFTTest, Backend
from vsmask.edge import FDoG
from debandshit.debanders import dumb3kdb

core = vs.core

def filter_chain(clip: vs.VideoNode) -> vs.VideoNode:
    
    clip = bbmod(clip, 1, 1, 1, 1)
    
    clip32 = u.depth(clip, 32)
    clip_y = u.get_y(clip32)

    descale_y = k.Bilinear().descale(clip_y, 1280, 720)
    upscale_y = NNEDI3().rpow2(descale_y)

    to_1080p = k.BicubicAuto(c=-1/4).scale(upscale_y, 1920, 1080)

    descale_error = k.Bilinear().scale(descale_y, 1920, 1080)
    desc_mask = core.std.Expr([clip_y, descale_error], 'x y - abs')
    desc_mask = desc_mask.std.Binarize(0.04)
    desc_mask = u.iterate(desc_mask, core.std.Maximum, 12)
    desc_mask = u.iterate(desc_mask, core.std.Inflate, 6)

    masked_rescale = core.std.MaskedMerge(to_1080p, clip_y, desc_mask)

    join_yuv = core.std.ShufflePlanes([masked_rescale, clip32], [0, 1, 2], vs.YUV)

    resc16 = u.depth(join_yuv, 16)
    
    dehalo = fine_dehalo(resc16, rx=2.3, darkstr=0, brightstr=0.9)

    denoise = DFTTest(dehalo, ftype=1, sigma=1, backend=Backend.CPU())

    deband = dumb3kdb(denoise, 16, 28, 15)

    detail_mask = FDoG().edgemask(u.get_y(resc16), 15<<8, 15<<8)\
                  .std.Maximum().std.Maximum().std.Minimum()

    apply_mask = core.std.MaskedMerge(deband, dehalo, detail_mask)

    final = u.depth(apply_mask, 10)

    return final