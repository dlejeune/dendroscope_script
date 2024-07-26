from ete3 import Tree
import subprocess
import numpy as np
import argparse
from pathlib import Path


DENDRO_PATH = "/home/dlejeune/dendroscope/Dendroscope"


COLOUR_LIST = [(255, 0, 0), (255, 38, 0), (255, 77, 0), (255, 115, 0), (255, 153, 0), (255, 229, 0), (242, 255, 0),
            (204, 255, 0), (166, 255, 0), (128, 255, 0), (89, 255, 0), (51, 255, 0), (12, 255, 0), (0, 255, 25),
            (0, 255, 64), (0, 255, 102), (0, 255, 140), (0, 255, 178), (0, 255, 217), (0, 255, 255), (0, 217, 255),
            (0, 179, 255), (0, 140, 255), (0, 102, 255), (0, 64, 255)]

class GroupStyle:

    def __init__(self, selector: str, colour: str = None, shape: str = None, size: str = None, font: str = None, fillcolour: str = None):
        
        self.selector = selector

        self.colour: str | None = colour
        self.shape: str | None = shape
        self.size: str | None = size
        self.font: str | None = font
        self.fillcolour: str | None = fillcolour


    def to_dendro_string(self) -> str:
        output_string = f"find searchtext='{self.selector}' target=Nodes regex=true;"

        if self.colour:
            output_string += f"set labelcolor={self.colour} 255;\n"

        if self.size:
            output_string += f"set nodesize={self.size};\n"
        
        if self.shape:
            output_string += f"set nodeshape={self.shape};\n"
        
        if self.font:
            output_string += f"set font={self.font};\n"

        if self.fillcolour:
            output_string += f"set fillcolor={self.fillcolour} 150;\n"
        
        output_string += "deselect all;\n"


        return output_string
       

class Tree:

    def __init__():
        pass


def generate_dendro_preamble(tree_file: Path, 
                             width: int = 1920,
                             height: int = 1080, 
                             drawer: str="CircularPhylogram", 
                             zoom: str = "expand", 
                             radial_labels: bool = True, 
                             ladderize:str="right", 
                             sparse_labels:bool = False) -> str:
    
    return f'''
        open file='{str(tree_file)}';
        set window width={width} height={height};
        set drawer={drawer};
        zoom what={zoom};
        set radiallabels={str(radial_labels).lower()};
        ladderize={ladderize};
        set sparselabels={str(sparse_labels).lower()};
        '''


def generate_dendro_export_command(main_output_file: Path, linear_output_file: Path, nexus_output_file: Path) -> str:
    return f'''
        exportimage file='{str(main_output_file)}' format=PNG replace=true;
        set drawer=RectangularPhylogram;
        exportimage file='{str(linear_output_file)}' format=PNG replace=true;
        save format=NeXML file={str(nexus_output_file)}
        quit;'''


def build_dendro_command(tree_file: Path, main_output_file: Path, linear_output_file: Path, nexus_output_file: Path) -> str:
    input_tree = Tree(str(tree_file))
    
    root_node = input_tree.get_tree_root()
    leaf_names = [node.name for node in root_node.get_leaves()]

    wpi_list = extract_wpis_from_sample_names(leaf_names)
    wpi_gradient_styles = create_gradient_group_styles(wpi_list)
    ogv_style = GroupStyle("OGV", colour="255 61 240", shape="rectangle", size="20", font="arial-bold-16", fillcolour="255 255 255")

    dendro_command = generate_dendro_preamble(tree_file)

    for wpi_style in wpi_gradient_styles:
        dendro_command += wpi_style.to_dendro_string()
    
    dendro_command += ogv_style.to_dendro_string()

    dendro_command += generate_dendro_export_command(main_output_file, linear_output_file, nexus_output_file)

    return dendro_command


def extract_wpis_from_sample_names(sample_names: list) -> list:
    
    wpis = []

    for sample_name in sample_names:
        wpi = int(sample_name.split("_")[2].replace("WPI", ""))

        if wpi and (wpi not in wpis) and (wpi != 0):
            wpis.append(wpi)

    return wpis


def create_gradient_group_styles(wpis: list) -> list:

    # This is a convoluted line, but makes life so easy. 
    # np.linspace will generate an evently-spaced list of floats between 0 and the length of the colour list
    # np.round will round those floats to the nearest integer
    # astype(int) will convert those floats to integers
    colour_indexes = np.round(np.linspace(0, len(COLOUR_LIST) - 1, len(wpis))).astype(int)

    group_styles = []

    for wpi, colour_index in zip(wpis, colour_indexes):
        colour = COLOUR_LIST[colour_index]

        padded_wpi = str(wpi).rjust(3, "0")
        regex_selector = f"(.*({padded_wpi}WPI))(.*(NGS)).*"

        group_style = GroupStyle(regex_selector, colour=f"{colour[0]} {colour[1]} {colour[2]}", font="arial-italic-8")
        group_styles.append(group_style)

    return group_styles


def build_dendro_command_from_tree(tree_file: Path) -> Path:
    output_filename = tree_file.with_suffix(".dendro_tree.png")
    linear_output_filename = tree_file.with_suffix(".dendro_tree_linear.png")
    nexus_output_filename = tree_file.with_suffix(".dendro_NEXUS.nex")

    dendro_command_filename = tree_file.parent / "dendro_command_file.txt"


    dendro_command = build_dendro_command(tree_file, output_filename, linear_output_filename, nexus_output_filename)

    with open(dendro_command_filename, "w") as dendro_command_file:
        dendro_command_file.write(dendro_command)

    return dendro_command_filename



def main(tree_file: Path):
    dendro_command_file = build_dendro_command_from_tree(tree_file)
    error_log_file = tree_file.parent / "warnings_errors.txt"

    command = f"{DENDRO_PATH} -g --commandFile {dendro_command_file} 2>&1 | tee -a {error_log_file}"
    subprocess.call(command, shell=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate a dendroscope tree with formattting from a Newick Tree File')
    parser.add_argument('-i', '--intree', type=str,
                        help='Newick format tree file', required=True)

    args = parser.parse_args()
    tree_path = Path(args.intree)

    main(tree_path)
