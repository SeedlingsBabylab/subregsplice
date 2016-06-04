import csv
import os
import sys
import datetime
import subprocess as sp

class Subregion(object):
    def __init__(self, onset, offset, diff):
        self.onset = onset
        self.end = offset
        self.time_diff = diff
        self.orig_audio_path = ""
        self.output_path = ""


def read_subregions(path):
    subregions = []
    with open(path, "rU") as input:
        reader = csv.reader(input)
        reader.next()
        for row in reader:
            interval = ms_to_hhmmss([int(row[1]), int(row[2])])
            region = Subregion(interval[0], interval[1], interval[2])
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

if __name__ == "__main__":
    cha_file = sys.argv[1]
    subregions_file = sys.argv[2]
    audio_file = sys.argv[3]
    output_path = sys.argv[4]

    subregions = read_subregions(subregions_file)

    slice_audio_file(subregions)
    concat_subregions(subregions)

