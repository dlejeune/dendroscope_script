import ete3
from pathlib import Path

class Tree:

    def __init__(ete_tree: ete3.Tree):
        self.ete_tree = ete_tree
        self.nodes = []
        pass


    def populate_nodes(self):
        for node in self.ete_tree.get_tree_root().get_leaves():
            


    @classmethod
    def from_nexus(nx_filepath: Path) -> "Tree":
        pass


class Node:

    def __init__():
        pass