import os

import numpy as np
import pandas as pd

from filestruct import loader


def isupper(txt):
    if not txt.replace(" ", "").isalpha():
        return False
    if txt == txt.upper():
        return True
    return False


def importance_scores(ls_fontnames, ls_colors, size_line):
    """
    Calculate the rarity of font, colors, in the text.

    Parameters
    ----------
    ls_fontnames : array_like
        the name of the font for each spans.
    ls_colors : array_like
        the color for each spans.
    size_line : array_like
        the number of charactère for each spans.

    Returns
    -------
    (array, array)
        return 2 array that contain respectively font rarity and
        color rarity

    """
    rarity_fonts = {}
    rarity_colors = {}
    for font in np.unique(ls_fontnames):
        rarity_fonts[font] = 1 - sum(size_line[np.where(ls_fontnames == font)]) / sum(
            size_line
        )
    for color in np.unique(ls_colors):
        rarity_colors[color] = 1 - sum(size_line[np.where(ls_colors == color)]) / sum(
            size_line
        )

    font_score = [rarity_fonts[font] for font in ls_fontnames]
    color_score = [rarity_colors[color] for color in ls_colors]

    return np.array(font_score), np.array(color_score)


def normalize(data):
    if data.max() == 0:
        return 0
    return (data - data.min()) / (data.max() - data.min())


class Document:
    def __init__(
        self,
        font_factor=1,
        color_factor=1,
        size_factor=1,
        bold_bonus=1,
        upper_bonus=1,
    ):
        self.font_factor = font_factor
        self.color_factor = color_factor
        self.size_factor = size_factor
        self.bold_bonus = bold_bonus
        self.upper_bonus = upper_bonus
        # Preprocess the text (do nothing for the moment)
        self.preprocess_txt = lambda x: x

    def open(self, filename, ext="auto"):
        if ext == "auto":
            _, ext = os.path.splitext(filename)
            ext = ext[1:]
        ext = ext.lower()
        self.filename = filename
        if ext in ["pdf", "epub", "xps", "mobi", "fb2", "cbz", "svg"]:
            self.blocks = loader.load_PyMuPDF(filename)
        self.block_data = pd.DataFrame(self.blocks)
        self.block_data.text = self.block_data.text.astype("string")
        self.block_data.font = self.block_data.font.astype("string")

        # Assign a level to each span according to its importance
        self.score_span(
            font_factor=self.font_factor,
            color_factor=self.color_factor,
            size_factor=self.size_factor,
            bold_bonus=self.bold_bonus,
            upper_bonus=self.upper_bonus,
        )

        # determine level of text using scores
        self.down_level()

        # ------------- Graph Creation --------------
        # Create the graph according of the level of each span,
        # and its position in the document.

        idxs = self["id"]
        score = self["score"]

        self.graph = {i: [] for i in idxs}
        self.roots = []

        for i, (idx, s) in enumerate(zip(idxs, score)):
            assert i == idx
            for j in reversed(range(0, i)):
                if score[j] > s:
                    self.graph[j].append(idx)
                    break
            else:
                self.roots.append(idx)

    # --------- Function used in the initialization part ----------------

    def score_span(
        self, font_factor=1, color_factor=1, size_factor=1, bold_bonus=1, upper_bonus=1
    ):
        """
        Assign a score to each paragraph.

        Use the font-size, font-name rarity and color rarity to determine the score.
        Use the function importance_scores.

        Returns
        -------
        None.

        """

        colors = self["color"]
        fonts = self["font"]
        sizes = self["size"]
        text = self["text"]

        # If all text is upper it is likely to be a title
        upper = np.char.isupper(text) * upper_bonus

        # Text is in bold
        bold = np.char.find(np.char.lower(fonts), "bold") * bold_bonus

        # Size of each span
        len_line = np.array([len(x) for x in text])

        # Normalize the size between 0 and 1
        size_score = normalize(sizes)

        # Calculate the score
        font_score, color_score = importance_scores(fonts, colors, len_line)
        font_score = normalize(font_score)
        color_score = normalize(color_score)

        # Calculate the level (weighted sum)
        level = (
            font_score * font_factor
            + color_score * color_factor
            + size_score * size_factor
            + bold
            + upper
        )
        self["score"] = level

    def down_level(self):
        levels = self["score"]
        unique = list(sorted(np.unique(levels)))[::-1]
        l = []
        for e in levels:
            l.append(unique.index(e))
        self["level"] = np.array(l)

    # --------- Graph section ------------------------

    def get_graph(self):
        return self.graph

    def get_nodes(self):
        return list(self.graph.keys())

    def successeurs(self, node):
        """
        Return the successors of a node.

        Parameters
        ----------
        node : int
            The father node

        Returns
        -------
        list
            The list of successors

        """
        return self.graph[node]

    # --------- Utility function -----------

    def is_feuille(self, node):
        return not self.successeurs(node)  # si aucun successeur : feuille

    # --------- Rendering the CV (print) ---------------

    def to_json(self):
        info = ["size", "font", "color", "text"]
        nodes = {}
        for idx in self["id"]:
            nodes[idx] = {e: self[e][idx] for e in info}
        for idx in self["id"]:
            nodes[idx]["children"] = [nodes[s] for s in self.successeurs(idx)]
        return nodes

    def parcour_length(self):
        vis = []
        pile = self.roots
        while pile:
            elt = pile.pop(0)
            vis.append(elt)
            pile = self.successeurs(elt) + pile
        return vis

    def parcour_str(self, indent_level, node):
        str_succ = [
            self.parcour_str(indent_level + 1, n) for n in self.successeurs(node)
        ]

        return indent_level * 2 * " " + "\n".join([self["text"][node]] + str_succ)

    def __str__(self):
        return "\n".join([self.parcour_str(0, n) for n in self.roots])

    def __getitem__(self, key):
        ret_dtype = None
        if key == "id":
            key = "span_id"
        if self.block_data[key].dtype == "string":
            ret_dtype = str
        return self.block_data[key].to_numpy(dtype=ret_dtype)

    def __setitem__(self, key, value):
        self.block_data[key] = value

    def __len__(self):
        return len(self["id"])
