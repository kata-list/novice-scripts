import vapoursynth as vs
import vstools as t
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
    # Fixing dirty lines . 
    # Scene filtering with rektlvls was not worth the time .
    
    clip32 = t.initialize_clip(clip, 32)
    clip_y = t.get_y(clip32)

    descale_y = k.Bilinear.descale(clip_y, 1280, 720)
    # Source is native 720p . Studio upscaled it using bilinear kernel .
    # Descaled the Y(luma) Plane in 32bit float .
    
    upscale_y = NNEDI3().rpow2(descale_y)
    # 720p descaled clip -> 2x upscale with NNEDI3 (1440p) . 

    to_1080p = k.BicubicAuto(c=-1/4).scale(upscale_y, 1920, 1080)
    # Resizing the upscaled clip back to 1080p .
    # Chose bicubic kernel strength based on output sharpness and halos .

    descale_error = k.Bilinear.scale(descale_y, 1920, 1080)
    desc_mask = core.std.Expr([clip_y, descale_error], 'x y - abs')
    desc_mask = desc_mask.std.Binarize(0.04)
    desc_mask = t.iterate(desc_mask, core.std.Maximum, 12)
    desc_mask = t.iterate(desc_mask, core.std.Inflate, 6)
    masked_rescale = core.std.MaskedMerge(to_1080p, clip_y, desc_mask)
    # After descaling native 1080p objects get destroyed (Artifacts, Ringing, Blurring) .
    # Native 1080p object example : credits, titles etc .
    # So protecting(masking) the native 1080p objects 
    # by finding those artifacts based on 're-upscaled clip' difference .

    join_yuv = core.std.ShufflePlanes([masked_rescale, clip32], [0, 1, 2], vs.YUV)
    # Merging back the rescaled Y plane with UV(chroma) planes .

    resc16 = t.depth(join_yuv, 16)
    # Preparing the clip for dehaloing, denoising and debanding .
    
    dehalo = fine_dehalo(resc16, rx=2.3, darkstr=0, brightstr=0.9)

    denoise = DFTTest(dehalo, ftype=1, sigma=1, backend=Backend.CPU())

    deband = dumb3kdb(denoise, 16, 28, 15)

    detail_mask = FDoG().edgemask(t.get_y(resc16), 15<<8, 15<<8)\
                  .std.Maximum().std.Maximum().std.Minimum()
    # Preparing a strong detail mask to protect the edges .

    apply_mask = core.std.MaskedMerge(deband, dehalo, detail_mask)

    final = t.finalize_clip(apply_mask, 10)
    # Finalizing the filtered output to 10bit .
    
    return final