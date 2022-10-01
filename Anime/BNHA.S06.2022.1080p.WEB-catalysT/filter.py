import vapoursynth as vs

from awsmfunc.base import bbmod

core = vs.core

clip = core.lsmas.LWLibavSource('bnha.s06e01.cr.mkv')
dirt = bbmod(clip, 1, 1, 1, 1)

clip.set_output(0)
dirt.set_output(1)