"""Local, ID-aligned pretranslation engine. No network or Luna dependencies."""
import collections
import difflib
import re
import unicodedata


def visible(text):
    text = re.sub(r"<ruby=[^>]*>", "", text).replace("</ruby>", "")
    return text.replace("<br>", "\n")


def compact(text):
    text = unicodedata.normalize("NFKC", visible(text))
    return "".join(text.split()).replace("~", "ー").replace("〜", "ー")


def body(text):
    return "".join(c for c in compact(text) if unicodedata.category(c)[0] not in "PS")


class Matcher:
    def __init__(self, data, rules):
        self.rules = rules
        self.records = {record[0]: record for record in data["records"]}
        self.history = []
        self.exact = collections.defaultdict(set)
        self.bodies = collections.defaultdict(set)
        self.fragments = collections.defaultdict(set)
        self.grams = collections.defaultdict(set)
        self.aliases = rules.get("aliases", {})
        for record in data["records"]:
            for column, language in [(2, "ja"), (3, "zh"), (4, "cht")]:
                text = visible(record[column])
                if not text:
                    continue
                entry = (record[0], language, column)
                # A punctuation-only line may disappear in OCR.
                parts = [line for line in text.splitlines() if body(line)]
                for line in parts:
                    self.fragments[body(line)].add(entry)
                for form in [text, "\n".join(parts)]:
                    self.exact[compact(form)].add(entry)
                    stem = body(form)
                    if stem:
                        self.bodies[stem].add(entry)
                stem = body(text)
                if len(stem) >= 5:
                    for gram in {stem[i:i+2] for i in range(len(stem)-1)}:
                        self.grams[gram].add(entry)
        self.map_labels = data.get("maps", [])

    def _source(self, entries, source):
        if source == "auto":
            return list(entries)
        return [entry for entry in entries if entry[1] == source]

    def _choose(self, entries, text):
        last = self.history[-1] if self.history else None
        window = self.rules.get("context_window", 100)
        if last is not None:
            script = self.records[last][1]
            nearby = [entry for entry in entries
                      if self.records[entry[0]][1] == script
                      and -8 <= entry[0]-last <= window]
            if nearby:
                entries = nearby

        def rank(entry):
            position, _, column = entry
            distance = sum(weight*(abs(position-anchor) +
                           (200 if position < anchor-8 else 0))
                           for weight, anchor in enumerate(self.history, 1))
            original = compact(self.records[position][column])
            # Punctuation is useful evidence when present in OCR.
            difference = 1-difflib.SequenceMatcher(None, compact(text), original).ratio()
            return (distance if last is not None else 0, difference, position)

        return min(entries, key=rank)

    def _map(self, text, source, target):
        text = compact(text)
        for wrong, corrected in self.aliases.items():
            text = text.replace(compact(wrong), compact(corrected))
        labels = []
        for row in self.map_labels:
            for language, column in [("ja", 0), ("zh", 1), ("cht", 2)]:
                if source in ("auto", language) and row[column]:
                    labels.append((compact(row[column]), row))
        labels.sort(key=lambda item: len(item[0]), reverse=True)
        output = []
        hits = 0
        while text:
            if text.startswith("?"):
                match = re.match(r"\?+", text).group()
                output.append(match)
                text = text[len(match):]
                continue
            found = next(((key, row) for key, row in labels
                          if key and text.startswith(key)), None)
            if found is None:
                return None
            key, row = found
            value = row[{"ja": 0, "zh": 3, "cht": 4}[target]]
            if not value:
                return None
            output.append(value)
            hits += 1
            text = text[len(key):]
        return "\n".join(output) if hits else None

    def _one(self, text, source, target):
        key = compact(text)
        corrected = self.aliases.get(key, text)
        key = compact(corrected)
        entries = self._source(self.exact.get(key, ()), source)
        strong = bool(entries)
        if not entries:
            entries = self._source(self.bodies.get(body(corrected), ()), source)
        if not entries:
            entries = self._source(self.fragments.get(body(corrected), ()), source)
        if not entries and len(body(corrected)) >= 5:
            stem = body(corrected)
            counts = collections.Counter()
            for gram in {stem[i:i+2] for i in range(len(stem)-1)}:
                counts.update(self.grams.get(gram, ()))
            scored = []
            for entry, _ in counts.most_common(80):
                if source not in ("auto", entry[1]):
                    continue
                original = body(self.records[entry[0]][entry[2]])
                ratio = difflib.SequenceMatcher(None, stem, original).ratio()
                if ratio >= self.rules.get("similarity", 0.80):
                    scored.append((ratio, entry))
            if scored:
                best = max(score for score, _ in scored)
                entries = [entry for score, entry in scored if score >= best-0.02]
        if not entries:
            return None
        if "?" in key:
            questioning = [entry for entry in entries
                           if "?" in compact(self.records[entry[0]][entry[2]])]
            if questioning:
                entries = questioning
        entry = self._choose(entries, corrected)
        record = self.records[entry[0]]
        # Failed or one-character OCR cannot move the scene anchor.
        unique_ids = {candidate[0] for candidate in entries}
        if strong and len(body(corrected)) >= 5 and len(unique_ids) == 1:
            if self.history and abs(entry[0]-self.history[-1]) > 400:
                self.history = []
            if not self.history or self.history[-1] != entry[0]:
                self.history.append(entry[0])
                self.history = self.history[-5:]
        return visible(record[{"ja": 2, "zh": 5, "cht": 6}[target]])

    def translate(self, text, source="auto", target="zh"):
        if source not in ("auto", "ja", "zh", "cht"):
            raise ValueError("源语言请选择自动、日语、简体中文或繁体中文")
        if target not in ("ja", "zh", "cht"):
            raise ValueError("目标语言请选择日语、简体中文或繁体中文")
        mapped = self._map(text, source, target)
        if mapped:
            return mapped
        # Multiple exact menu records take precedence over fuzzy whole-page matches.
        lines = [line for line in visible(text).splitlines() if body(line)]
        if len(lines) > 1 and all(self._source(self.exact.get(compact(line), ()), source)
                                  for line in lines):
            return "\n".join(self._one(line, source, target) for line in lines)
        return self._one(text, source, target)
