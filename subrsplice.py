import csv
import os
import sys
import re
import datetime
import subprocess as sp

from collections import deque


interval_regx = re.compile("(\025\d+_\d+)")

class Subregion(object):
    def __init__(self, onset, onset_ms, offset, offset_ms, diff):
        self.onset = onset
        self.onset_ms =onset_ms
        self.end = offset
        self.offset_ms = offset_ms
        self.time_diff = diff
        self.diff = 0
        self.orig_audio_path = ""
        self.output_path = ""


def read_subregions(path):
    subregions = []
    with open(path, "rU") as input:
        reader = csv.reader(input)
        reader.next()
        for row in reader:
            interval = ms_to_hhmmss([int(row[1]), int(row[2])])
            region = Subregion(interval[0], int(row[1]),
                               interval[1], int(row[2]),
                               interval[2])
            region.diff = int(row[2]) - int(row[1])
            region.orig_audio_path = audio_file
            out_path = os.path.join(output_path, "{}.wav".format(row[0]))
            region.output_path = out_path
            subregions.append(region)

    return subregions

def slice_audio_file(subregions):
    for region in subregions:
        command = ["ffmpeg",
                   "-ss",
                   str(region.onset),
                   "-t",
                   str(region.time_diff),
                   "-i",
                   region.orig_audio_path,
                   region.output_path,
                   "-y"]

        command_string = " ".join(command)
        print command_string

        pipe = sp.Popen(command, stdout=sp.PIPE, bufsize=10 ** 8)
        out, err = pipe.communicate()

def concat_subregions(subregions):

    filename = os.path.basename(subregions[0].orig_audio_path)[0:5]
    filename = "{}_subregion_concat.wav".format(filename)
    with open("concat_list.txt", "wb") as output:
        for region in subregions:
            output.write("file \'{}\'\n".format(region.output_path))

    output = os.path.join(output_path, filename)
    command = ["ffmpeg",
               "-f",
               "concat",
               "-i",
               "concat_list.txt",
               "-c",
               "copy",
               output,
               "-y"]

    command_string = " ".join(command)
    print command_string

    pipe = sp.Popen(command, stdout=sp.PIPE, bufsize=10 ** 8)
    out, err = pipe.communicate()

    # cleanup
    os.remove("concat_list.txt")
    for region in subregions:
        os.remove(region.output_path)

def ms_to_hhmmss(interval):
    x_start = datetime.timedelta(milliseconds=interval[0])
    x_end = datetime.timedelta(milliseconds=interval[1])

    x_diff = datetime.timedelta(milliseconds=interval[1] - interval[0])

    start = ""
    if interval[0] == 0:
        start = "0" + x_start.__str__()[:11] + ".000"
    else:

        start = "0" + x_start.__str__()[:11]
        if start[3] == ":":
            start = start[1:]
    end = "0" + x_end.__str__()[:11]
    if end[3] == ":":
        end = end[1:]

    return [start, end, x_diff]


def create_new_cha(subregions):
    filename = os.path.basename(subregions[0].orig_audio_path)[0:5]
    filename = "{}_subregion_concat.cha".format(filename)
    output = os.path.join(output_path, filename)

    region_deque = deque(subregions)
    curr_region = region_deque.popleft()

    total_time = region_time_sum(subregions)

    header_finished = False
    with open(cha_file, "rU") as original:
        with open(output, "wb") as new_cha:
            for index, line in enumerate(original):
                if line.startswith("@") and (not header_finished) or (index < 9):
                    new_cha.write(line)
                else:
                    header_finished = True
                    int_regx_result = interval_regx.search(line)
                    interval = ""
                    if int_regx_result:
                        interval = int_regx_result.group(1)
                        split_interval


def region_time_sum(subregions):
    """
    Returns the total time of the subregions
    :param subregions:
    :return: time sum of regions
    """

    time = 0
    for region in subregions:
        time += region.diff
    return time


if __name__ == "__main__":
    cha_file = sys.argv[1]
    subregions_file = sys.argv[2]
    audio_file = sys.argv[3]
    output_path = sys.argv[4]

    subregions = read_subregions(subregions_file)

    slice_audio_file(subregions)
    concat_subregions(subregions)

    create_new_cha(subregions)

