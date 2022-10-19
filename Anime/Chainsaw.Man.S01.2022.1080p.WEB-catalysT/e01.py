from vapoursynth import core
from vardautomation import X265, FileInfo
from filter import csm_filter_chain

SRC = FileInfo('chainsaw.man.s01e01.cr-web.mkv', idx=core.lsmas.LWLibavSource)

clip = SRC.clip

op_ed = [(3237, 5394), (34405, 35564)]

filtered = csm_filter_chain(clip, op_ed)

if __name__ == '__main__':
    SRC.name_clip_output = SRC.workdir / f'{SRC.name}.265'
    X265('x265-params.txt').run_enc(filtered, SRC)
else:
    clip.set_output(0)
    filtered.set_output(1)