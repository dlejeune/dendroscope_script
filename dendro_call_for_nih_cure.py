import sys
from ete3 import Tree
import subprocess
import os
import argparse
import socket


def get_dendro_call():
    hn = socket.gethostname()
    dendo_lookup = {'dave-w540': '/home/dave/Software/dendroscope/Dendroscope -g',
                    'srvubugal001.uct.ac.za': ' xvfb-run --auto-servernum --server-num=1 Dendroscope -g '}
    if hn in dendo_lookup.keys():
        return dendo_lookup[hn]
    else:
        print("We don't know how to run dendroscope on your computer")
        r = input("Enter how we should call dendroscope on this computer:\n")
        return r


def main(intree_fn):
    #dendro_cmd = "/home/dave/Software/dendroscope/Dendroscope -g"
    # dendro_cmd = "/data/software/dendroscope/Dendroscope -g"
    dendro_cmd = "/home/dlejeune/dendroscope/Dendroscope -g"
    #get_dendro_call()


    wd = os.path.split(intree_fn)[0]
    out_fn = os.path.splitext(intree_fn)[0] + "_dendro_tree.png"
    out_fn_linear = os.path.splitext(intree_fn)[0] + "_dendro_tree_linear.png"
    nexus_fn = os.path.splitext(intree_fn)[0] + "_dendro_NEXUS.nex"

    t = Tree(intree)
    root_node = t.get_tree_root()
    all_leaves = root_node.get_leaves()
    leaf_names = [node.name for node in all_leaves]
    #OGV_names = [ln for ln in leaf_names if ln.split("_")[5] == "OGV"]


    # CAP336_4210_138WPI_NEF_1_NGS_353_0.001
    all_wpis = []
    for lf in leaf_names:
        all_wpis.append(int(lf.upper().split("_")[2].replace("WPI", "")))
    all_wpis = list(set(all_wpis))

    if 0 in all_wpis:  # The OGV seqids include a dummy 000wpi  CAP336_xxxx_000WPI_NEF_1_OGV_B-W39 - no real data is at 0wpi
        all_wpis.remove(0)

    rgbs = [(255, 0, 0), (255, 38, 0), (255, 77, 0), (255, 115, 0), (255, 153, 0), (255, 229, 0), (242, 255, 0),
            (204, 255, 0), (166, 255, 0), (128, 255, 0), (89, 255, 0), (51, 255, 0), (12, 255, 0), (0, 255, 25),
            (0, 255, 64), (0, 255, 102), (0, 255, 140), (0, 255, 178), (0, 255, 217), (0, 255, 255), (0, 217, 255),
            (0, 179, 255), (0, 140, 255), (0, 102, 255), (0, 64, 255)]

    all_wpis.sort()
    print("All wpis: ", all_wpis)
    lst_len = len(all_wpis) - 1  # because the first one will always be zero index. first colour. RED
    wpi_step = {}
    i = 0
    for wpi in all_wpis:
        wpi_step[wpi] = i
        i += 1
    print("There are {} items in this list".format(len(all_wpis)))
    step_size = (len(rgbs) -1) / lst_len
    print("which means each one takes: {}, of a step through the list.".format(step_size))
    wpi_rgb_lookup = {}
    for wpi in all_wpis:
        print("seqs with {}wpi".format(wpi))
        print("are step number: {}".format(wpi_step[wpi]))
        print("which works out to be {} through the list of 25".format((wpi_step[wpi] * step_size)))
        this_wpi_rgb = rgbs[round(wpi_step[wpi] * step_size)]
        print("which is rgb: {}".format(this_wpi_rgb))
        wpi_rgb_lookup[wpi] = this_wpi_rgb


    dendro_cmd_text = '''
        open file='{}';
        set window width=1920 height=1080 ;
        set drawer=CircularPhylogram;
        zoom what=expand;
        set radiallabels=true;
        set ladderize=right;
        set sparselabels=false;
        '''.format(intree_fn)

    # time_colours = {"004WPI": "255 38 0",
    #                 "053WPI": "12 255 0",
    #                 "069WPI": "0 255 25",
    #                 "106WPI": "0 255 140",
    #                 "132WPI": "0 255 178",
    #                 "158WPI": "0 255 255",
    #                 "237WPI": "0 64 255",
    #                 }

    # for leaf in leaf_names:
    #     if "OGV" in leaf:
    #         this_freq = 50
    #         this_colour = "255 61 240"
    #         this_shape = "rectangle"
    #     elif "NGS" in leaf:
    #         this_freq = int(leaf.split("_")[-1])
    #         this_freq = int(math.log(this_freq) * 10)
    #         this_shape = "oval"
    #         this_colour = "255 255 255"
    #         for k in time_colours.keys():
    #             if k in leaf:
    #                 this_colour = time_colours[k]
    #     elif "CONSENSUS_C_ENV_2004LANL" in leaf:
    #         this_freq = 20
    #         this_colour = "0 0 0"
    #         this_shape = "oval"
    #
    #     dendro_cmd_text = dendro_cmd_text + '''
    # find searchtext='{}' target=Nodes wholewords=true;
    # set labelcolor={} 255;
    # set nodesize={};
    # set nodeshape={};
    # set font=arial-italic-8;
    # set fillcolor={} 150;
    # deselect all;
    # '''.format(leaf, this_colour, this_freq, this_shape, this_colour)
    dendro_cmd_text += "apply-all-begin "
    ogv_text = ""
    for leaf in leaf_names:
        if "OGV" in leaf:
            this_freq = 20
            this_colour = "255 61 240"
            this_shape = "rectangle"
            ogv_text = ogv_text + '''
            find searchtext='{}' target=Nodes wholewords=true;
            set labelcolor={} 255;
            set nodesize={};
            set nodeshape={};
            set font=arial-bold-16;
            set fillcolor={} 255;
            deselect all;
            '''.format(leaf, this_colour, this_freq, this_shape, this_colour)
        elif "NGS" in leaf:
            this_colour = "255 255 255"
            this_wpi = int(leaf.split("_")[2].upper().replace("WPI", ""))
            this_colour = wpi_rgb_lookup[this_wpi]
            this_colour = "{} {} {}".format(this_colour[0], this_colour[1], this_colour[2])
            # for k in time_colours.keys():
            #     if k in leaf:
            #         this_colour = time_colours[k]
            dendro_cmd_text = dendro_cmd_text + '''
            find searchtext='{}' target=Nodes wholewords=true;
            set labelcolor={} 255;
            set font=arial-italic-8;
            deselect all;
            '''.format(leaf, this_colour)
    dendro_cmd_text += ogv_text


    # for clr, seqid_lst in self.coloured_dictionary.items():
    #     for seqid in seqid_lst:
    #         dendro_cmd_text = dendro_cmd_text + '''
    #         find searchtext={} target=Nodes wholewords=true;
    #         set labelcolor={};
    #         deselect all;
    #         set sparselabels=false;'''.format(seqid, clr)
    dendro_cmd_text += "apply-all-end;"
    dendro_cmd_text = dendro_cmd_text + '''
        set sparselabels=false;
        exportimage file='{}' format=PNG replace=true;
        set drawer=RectangularPhylogram;
        exportimage file='{}' format=PNG replace=true;
        save format=NeXML file={}
        quit;'''.format(out_fn, out_fn_linear, nexus_fn)

    # write it to file
    dendro_cmd_fn = os.path.join(wd, "dendro_command_file.txt")
    with open(dendro_cmd_fn, "w") as fw:
        fw.write(dendro_cmd_text)

    warn_error_fn = os.path.join(wd, "warnings_errors.txt")
    cmd = "{} --commandFile {} 2>&1 | tee -a {} ".format(dendro_cmd, dendro_cmd_fn, warn_error_fn)
    subprocess.call(cmd, shell=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='some program description')
    parser.add_argument('-in', '--intree', type=str,
                        help='Newick format tree file', required=True)

    args = parser.parse_args()
    intree = args.intree

    main(intree)
