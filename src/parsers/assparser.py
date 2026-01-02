from __future__ import absolute_import

import os
import tempfile

from .baseparser import BaseParser, NoSubtitlesParseError
from .subrip import SubRipParser
from .ass2srt import Ass2srt


class AssParser(BaseParser):
    format = "ASS/SSA"
    parsing = (".ass", ".ssa")

    # IMPORTANT: override parse() to NOT use BaseParser.parse()
    def parse(self, text, fps=None):
        # keep dots! only remove NUL and trim
        if isinstance(text, bytes):
            text = text.decode("utf-8", errors="replace")
        if text.startswith(u"\ufeff"):
            text = text[1:]
        text = text.replace("\x00", "").strip()

        sublist = self._parse(text, fps)
        if len(sublist) <= 1:
            raise NoSubtitlesParseError()
        return sublist

    def _parse(self, text, fps):
        fd, ass_path = tempfile.mkstemp(suffix=".ass", prefix="subssupport_")
        os.close(fd)
        srt_path = ass_path[:-4] + ".srt"
        try:
            with open(ass_path, "w", encoding="utf-8", errors="replace") as f:
                f.write(text)

            conv = Ass2srt(ass_path)
            conv.to_srt(name=srt_path)

            # read with the encoding detected by Ass2srt.load()
            with open(srt_path, "r", encoding=conv.encoding, errors="replace") as f:
                srt_text = f.read()

            return SubRipParser(rowParse=self.rowParse).parse(srt_text, fps)
        finally:
            try:
                os.remove(ass_path)
            except Exception:
                pass
            try:
                os.remove(srt_path)
            except Exception:
                pass


parserClass = AssParser
