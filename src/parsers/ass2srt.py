import re, os


class Ass2srt:
    def __init__(self, filename):
        self.filename = filename
        self.encoding = "utf-8"
        self.load()

    def output_name(self, tag=None):
        outputfile = self.filename[0:-4]
        if tag:
            outputfile = outputfile+"."+tag
        return outputfile+".srt"

    def load(self, filename=None):
        if filename is None:
            filename = self.filename

        raw = open(filename, "rb").read()

        # Try common encodings for subtitle files
        for enc in ("utf-8-sig", "utf-8", "cp1256", "windows-1256"):
            try:
                text = raw.decode(enc)
                self.encoding = enc
                break
            except Exception:
                text = None

        if text is None:
            text = raw.decode("utf-8", errors="replace")
            self.encoding = "utf-8"

        data = text.splitlines(True)

        self.nodes = []
        for line in data:
            if line.startswith("Dialogue"):
                line = line.split(":", 1)[1]   # safer than lstrip("Dialogue:")
                node = line.split(",")
                node[1] = timefmt(node[1])
                node[2] = timefmt(node[2])
                node[9] = ",".join(node[9:])
                node[9] = re.sub(r'{[^}]*}', "", node[9]).strip()
                node[9] = re.sub(r'\\N', "\n", node[9])
                self.nodes.append(node)

    def to_srt(self, name=None, line=0, tag=None):
        if name is None:
            name = self.output_name(tag=tag)
        with open(file=name, mode="w", encoding=self.encoding) as f:
            index = 1
            for node in self.nodes:
                f.writelines(f"{index}\n")
                f.writelines(f"{node[1]} --> {node[2]}\n")
                if line == 1:
                    text = node[9].split("\n")[0]
                elif line == 2:
                    tmp = node[9].split("\n")
                    text = tmp[1] if len(tmp) > 1 else node[9]
                else:
                    text = node[9]
                f.writelines(f"{text}\n\n")
                index += 1

    def __str__(self):
        return f"{self.filename}\n{len(self.nodes)}\n"


def timefmt(strt):
    strt = strt.replace(".", ",")
    return f"{strt}0"