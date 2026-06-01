from __future__ import absolute_import
import re

from .baseparser import BaseParser, ParseError


class SubViewerParser(BaseParser):
    """Parser for SubViewer 1.x / 2.0 text subtitles.

    SubViewer files normally use the .sub extension.  They contain a time
    range on one line followed by the subtitle text.  SubViewer 2.0 uses
    ``[br]`` markers for explicit line breaks and can contain an optional
    metadata header such as ``[INFORMATION]`` and ``[SUBTITLE]``.
    """

    parsing = ('.sub',)
    format = "SubViewer"

    _BLOCK_RE = re.compile(
        r'(?ms)^\s*'
        r'(\d{1,2}):(\d{2}):(\d{2})[\.,](\d{1,3})\s*,\s*'
        r'(\d{1,2}):(\d{2}):(\d{2})[\.,](\d{1,3})\s*\r?\n'
        r'(.*?)'
        r'(?=\r?\n\s*\r?\n|\Z)'
    )

    def _parse(self, text, fps=None):
        subs = []
        idx = 0

        # Normalize line endings for predictable block matching.  Preserve
        # text punctuation and only translate SubViewer line-break markers.
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        for match in self._BLOCK_RE.finditer(text):
            try:
                idx += 1
                start = self._time_to_ms(*match.groups()[0:4])
                end = self._time_to_ms(*match.groups()[4:8])
                subtitle_text = match.group(9).strip()
                subtitle_text = re.sub(r'(?i)\[br\]', '\n', subtitle_text)

                # Ignore empty blocks but keep valid punctuation-only entries.
                if subtitle_text:
                    subs.append(self.createSub(subtitle_text, start, end))
            except Exception as e:
                raise ParseError(str(e) + ', subtitle_index: %d' % idx)

        return subs

    @staticmethod
    def _time_to_ms(hours, minutes, seconds, fraction):
        # SubViewer normally stores centiseconds, but accepting one to three
        # digits also handles files exported with tenths or milliseconds.
        fraction = str(fraction)
        if len(fraction) == 1:
            millis = int(fraction) * 100
        elif len(fraction) == 2:
            millis = int(fraction) * 10
        else:
            millis = int(fraction[:3])
        return ((int(hours) * 3600 + int(minutes) * 60 + int(seconds)) * 1000) + millis


parserClass = SubViewerParser
