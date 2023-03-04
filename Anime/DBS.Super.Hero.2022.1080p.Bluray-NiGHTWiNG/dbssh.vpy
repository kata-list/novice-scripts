import vapoursynth as vs
import vstools as t
import vskernels as k
from vsdehalo import YAHR, fine_dehalo
from vardefunc import DebugOutput
from vsrgtools import contra_dehalo, contrasharpening
from vsaa import fine_aa
from vsmasktools import FDoG
from vsdeband import F3kdb, mdb_bilateral
from dfttest2 import DFTTest
from adptvgrnMod import adptvgrnMod

core = vs.core

def remove_green_tint(clip: vs.VideoNode) -> vs.VideoNode:
    to_rgbs = clip.fmtc.resample(css='444', kernel='blackman').fmtc.matrix(mat='709', col_fam=vs.RGB).fmtc.bitdepth(bits=32)
    detint = core.timecube.Cube(to_rgbs, 'dbssh_dci_to_d65_lut_catalyst.cube')
    # Removed the green tint by doing DCI to D65 Chroma Adaptation in DaVinci Resolve -> Extracted the lut(.cube) file afterwards
    # -> Applied the lut file in VS through timecube plugin
    to_yuv = core.fmtc.matrix(detint, mat='709', col_fam=vs.YUV)
    to_420 = core.fmtc.resample(to_yuv, css=420, kernel='blackman')
    return t.depth(to_420, clip.format.bits_per_sample)

def deband_generic(clip: vs.VideoNode) -> vs.VideoNode:
    denoise = DFTTest(clip, 1, 2)
    deband = F3kdb.deband(denoise, 20, 40)
    contra = contrasharpening(deband, clip)
    grain = adptvgrnMod(contra, 0.3, luma_scaling=8)
    edge_mask = FDoG.edgemask(t.get_y(clip), 25<<8, 25<<8).std.Maximum().std.Minimum()
    return core.std.MaskedMerge(grain, clip, edge_mask)

def deband_heavy(clip: vs.VideoNode) -> vs.VideoNode:
    denoise = DFTTest(clip, 1, 2)
    deband = mdb_bilateral(denoise, thr=60)
    contra = contrasharpening(deband, clip)
    grain = adptvgrnMod(contra, 0.5, luma_scaling=7, sharp=70)
    edge_mask = FDoG.edgemask(t.get_y(clip), 20<<8, 20<<8).std.Maximum().std.Minimum()
    return core.std.MaskedMerge(grain, clip, edge_mask)

# Filter Chain Start
src = core.lsmas.LWLibavSource('dbssh.bdremux.mkv')
src = t.initialize_clip(src, bits=16)

detint = remove_green_tint(src)
clip16 = detint

dehalo = fine_dehalo(clip16, rx=2.1)
edge_clean = YAHR(dehalo)
contra = contra_dehalo(edge_clean, dehalo)

clip32 = t.depth(contra, 32)

faa = t.depth(fine_aa(clip32), 16)

deband0 = deband_generic(faa)
deband1 = deband_heavy(faa)

heavy_deband_ranges = [(9969,10120),(27727,27754),(62080,63705),(63922,65013)]

deband = t.rfs(deband0, deband1, heavy_deband_ranges)

final = t.finalize_clip(deband, 8)

final.set_output()