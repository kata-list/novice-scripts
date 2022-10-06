from vapoursynth import core
from vardautomation import X265, FileInfo
from filter import filter_chain

SRC = FileInfo('bnha.s06e01.cr.mkv', idx=core.lsmas.LWLibavSource)

clip = SRC.clip

filtered = filter_chain(clip)

if __name__ == '__main__':
    SRC.name_clip_output = SRC.workdir / f'{SRC.name}.265'
    X265('x265-params.txt').run_enc(filtered, SRC)
else:
    clip.set_output(0)
    filtered.set_output(1)