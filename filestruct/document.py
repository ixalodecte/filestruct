import os
import numpy as np

from filestruct import loader
from filestruct.utils import unique_n_uplet
from filestruct.loader import Style


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


def normalize(value, mini, maxi):
    if maxi == 0:
        return 0
    return (value - mini) / (maxi - mini)


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
            data = loader.load_PyMuPDF(filename)
        blocks = data["span"]
        self.style_set = data["style_set"]

        # Transform list of dictionary (blocks) into dictonary of list (block_data)
        self.block_data = {key: np.array([i[key] for i in blocks]) for key in blocks[0]}
        self.block_data["id"] = np.arange(len(blocks))

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

        maxi_size = max(x.size for x in self.style_set)
        mini_size = min(x.size for x in self.style_set)
        char_num = self.get_n_char()

        for style in self.style_set:
            # Normalize the size between 0 and 1
            size_score = normalize(style.size, mini_size, maxi_size)

            # Calculate the font rarity
            font_num = sum(x.num_char for x in self.style_set if x.font == style.font)
            font_score = 1 - font_num / char_num

            # Calculate the color rarity
            color_num = sum(
                x.num_char for x in self.style_set if x.color == style.color
            )
            color_score = 1 - color_num / char_num

            bold = style.bold
            upper = style.upper

            # Calculate the total score (weighted sum)
            score = (
                font_score * font_factor
                + color_score * color_factor
                + size_score * size_factor
                + bold
                + upper
            )
            style.score = score

    def down_level(self):
        scores = self["score"]
        unique = list(sorted(np.unique(scores)))[::-1]
        levels = []
        for s in scores:
            levels.append(unique.index(s))
        for s, l in zip(self["style"], levels):
            s.level = l

    def down_level(self):
        scores = sorted(list(set(e.score for e in self.style_set)))[::-1]
        for style in self.style_set:
            style.level = scores.index(style.score)

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

    def is_feuille(self, node):
        return not self.successeurs(node)  # si aucun successeur : feuille

    # --------- Utility function -----------

    def get_n_char(self):
        return sum(x.num_char for x in self.style_set)

    # --------- Rendering the document (print) ---------------

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

    def info(self):
        page_n = len(np.unique(self["page_id"]))
        paragraph_n = len(np.unique(self["paragraph_id"]))
        line_n = np.unique(self["line_id"])
        char_n = len("".join(self["text"]))
        print(f"{page_n} page | {paragraph_n} paragraphs | {char_n} characters")
        print()
        styles_sorted = sorted(self.style_set, key=lambda x: x.level)
        for style in styles_sorted:
            print(f"level {style.level} :")
            percentage = round((style.num_char / char_n) * 100)
            print("  ", style, "|", str(percentage) + "%")

    def __str__(self):
        return "\n".join([self.parcour_str(0, n) for n in self.roots])

    def __getitem__(self, key):
        if key in self.block_data:
            return self.block_data[key]
        elif key in Style.style_attribute:
            return np.array([elt.__getattribute__(key) for elt in self["style"]])
        else:
            raise KeyError("f{key} not an attribute of Document or Style")

    def __setitem__(self, key, value):
        self.block_data[key] = value

    def __len__(self):
        return len(self["id"])
