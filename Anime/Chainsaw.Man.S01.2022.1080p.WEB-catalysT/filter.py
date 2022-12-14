import vapoursynth as vs
import vstools as t
import vskernels as k
from rvsfunc.NNEDI3 import NNEDI3
from vsdehalo import fine_dehalo, edge_cleaner
from vsrgtools import contra_dehalo
from dfttest2 import DFTTest, Backend
from vsdeband import F3kdb
from xvs import WarpFixChromaBlend
from vsmask.edge import FDoG
from vsaa import fine_aa

core = vs.core

def csm_filter_chain(
    clip: vs.VideoNode,
    op_ed: list = None
    ) -> vs.VideoNode:

    nh = 844
    nw = (16/9)*nh

    clip32 = t.initialize_clip(clip, 32)
    clip_y = t.get_y(clip32)
    desc_y = k.Bilinear.descale(clip_y, nw, nh)
    upsc_y = NNEDI3().rpow2(desc_y)
    resc_y = k.Hermite.scale(upsc_y, 1920, 1080)
    
    aa = fine_aa(resc_y)

    descale_error = k.Bilinear.scale(desc_y, 1920, 1080)

    desc_mask = core.akarin.Expr([clip_y, descale_error], 'x y - abs')
    desc_mask = desc_mask.std.Binarize(0.04)
    desc_mask = t.iterate(desc_mask, core.std.Maximum, 10)
    desc_mask = t.iterate(desc_mask, core.std.Inflate, 4)

    masked_resc = core.std.MaskedMerge(aa, clip_y, desc_mask)
    
    resc_y = masked_resc
    
    if op_ed:
        exclude_op_ed = t.replace_ranges(resc_y, clip_y, ranges=op_ed)
        resc_y = exclude_op_ed
    
    join_yuv = core.std.ShufflePlanes([resc_y, clip32], [0, 1, 2], vs.YUV)

    resc16 = t.depth(join_yuv, 16)

    dehalo = fine_dehalo(resc16, rx=2.1, brightstr=0.8)
    dehalo = edge_cleaner(dehalo, strength=8, rmode=16, smode=1, hot=True)
    dehalo = contra_dehalo(dehalo, resc16)

    uv_warp = WarpFixChromaBlend(dehalo)

    denoise = DFTTest(uv_warp, 1, 1, backend=Backend.CPU())

    deband = F3kdb.deband(denoise, radius=16, thr=[29, 17, 17])

    mask = FDoG().edgemask(t.depth(clip_y, 16), 15<<8, 15<<8).std.Maximum().std.Minimum()

    a_m = deband.std.MaskedMerge(uv_warp, mask)

    final = t.finalize_clip(a_m, 10)
    
    return final