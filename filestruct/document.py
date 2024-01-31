import numpy as np
import pandas as pd

import fitz


def isupper(txt):
    if not txt.replace(" ", "").isalpha():
        return False
    if txt == txt.upper():
        return True
    return False


def importance_scores(ls_fontnames, ls_colors, size_line):
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


class PDFDocument:
    def __init__(
        self,
        filename,
        n_columns="auto",
        txt_unidecode=True,
        cut_span=True,
        font_factor=1,
        color_factor=1,
        size_factor=1,
        bold_bonus=1,
        upper_bonus=1,
    ):
        self.filename = filename
        self.blocks = self.extract_blocks()
        self.block_data = pd.DataFrame(self.blocks)
        self.block_data.text = self.block_data.text.astype("string")
        self.block_data.font = self.block_data.font.astype("string")

        self.preprocess_txt = lambda x: x
        # if txt_unidecode == True:
        #    self.preprocess_txt = unidecode

        # On ouvre le document avec fitz
        # doc = fitz.open(filename)

        # Assign a level to each line according to its importance
        self.level_size_font_color(
            font_factor=font_factor,
            color_factor=color_factor,
            size_factor=size_factor,
            bold_bonus=bold_bonus,
            upper_bonus=upper_bonus,
        )

        self.down_level()

        # ------------- Création du graphe --------------
        # Création du graphe en fonction du level de chaque paragraphe.
        # Chaque paragraphe est un sous noeud du premier paragraphe au dessus
        # de lui qui possède un level plus grand (qui est plus important).

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

    def extract_blocks(self):
        doc = fitz.open(self.filename)
        page_id = 0
        paragraph_id = 0
        line_id = 0
        span_id = 0
        spans = []
        for page in doc:
            # Récupère les blocs (paragraphe)
            txt = page.get_text("dict", flags=4)["blocks"]
            for paragraph in txt:
                if paragraph["type"] == 0:
                    for line in paragraph["lines"]:
                        for span in line["spans"]:
                            d = {
                                "size": span["size"],
                                "flags": span["flags"],
                                "font": span["font"],
                                "color": span["color"],
                                "text": span["text"],
                                "x": span["bbox"][0],
                                "y": span["bbox"][1],
                                "w": span["bbox"][2],
                                "h": span["bbox"][3],
                                "page_id": page_id,
                                "paragraph_id": paragraph_id,
                                "page_id": page_id,
                                "line_id": line_id,
                                "span_id": span_id,
                            }
                            spans.append(d)
                            span_id += 1
                        line_id += 1
                    paragraph_id += 1
            page_id += 1
        return spans

    def level_size_font_color(
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

        # If all text is upper it is likely to be a title
        upper = np.char.isupper(self["text"]) * upper_bonus

        colors = self["color"]
        fonts = self["font"]
        sizes = self["size"]

        bold = np.char.find(np.char.lower(self["font"]), "bold") * bold_bonus
        # bold == bold_bonus if "bold" is in fontnames, else = 0

        len_line = np.array([len(x) for x in self["text"]])

        # Normalize the size between 0 and 1
        size_score = normalize(sizes)

        font_score, color_score = importance_scores(fonts, colors, len_line)
        font_score = normalize(font_score)
        color_score = normalize(color_score)
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
