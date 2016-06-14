import csv
import os
import sys
import re
import datetime
import subprocess as sp

from collections import deque


interval_regx = re.compile("(\025\d+_\d+\025)")

class Subregion(object):
    def __init__(self, number, onset, onset_ms, offset, offset_ms, diff, special):
        self.number = number
        self.onset = onset
        self.onset_ms = onset_ms
        self.end = offset
        self.offset_ms = offset_ms
        self.time_diff = diff
        self.diff = 0
        self.orig_audio_path = ""
        self.output_path = ""
        self.special = special


def read_subregions(path):
    subregions = []
    with open(path, "rU") as input:
        reader = csv.reader(input)
        reader.next()
        for row in reader:
            interval = ms_to_hhmmss([int(row[1]), int(row[2])])
            region = Subregion(row[0], interval[0], int(row[1]),
                               interval[1], int(row[2]), interval[2],
                               row[3])
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

    last_interval_read = None
    last_interval_written = None

    num_regions  = len(subregions)
    curr_subreg_num = 1

    begin_region_written = False
    end_region_written = False

    curr_subregion_diff = 0

    output_interval_tail = 0

    with open(cha_file, "rU") as original:
        with open(output, "wb") as new_cha:
            for index, line in enumerate(original):
                if line.startswith("@") and (not header_finished) or (index < 9):
                    new_cha.write(line)
                else:
                    header_finished = True
                    int_regx_result = interval_regx.search(line)
                    interval = ""
                    split_interval = None

                    # line with interval on it
                    if int_regx_result:
                        interval = int_regx_result.group(1)
                        split_interval = interval.replace("\x15", "", 2).split("_")
                        split_interval = map(int, split_interval)

                        print split_interval
                        last_interval_read = split_interval


                        curr_subregion_diff = curr_region.onset_ms - output_interval_tail


                        # interval is inside the range of the subregion
                        if region_inside_region(curr_region, split_interval):
                            print "print inside region"
                            if not begin_region_written: # at the beginning

                                if not curr_region.special:
                                    new_cha.write("%com:\tregion {} of {} starts. (coded subregion) original timestamp start: {}\n".\
                                            format(curr_region.number,
                                                   num_regions,
                                                   curr_region.onset_ms))
                                else:
                                    new_cha.write("%com:\tregion {} of {} starts. (extra region) original timestamp start: {}\n". \
                                                  format(curr_region.number,
                                                         num_regions,
                                                         curr_region.onset_ms))

                                begin_region_written = True

                            update_result = update_line(line, interval, split_interval, curr_subregion_diff)
                            new_cha.write(update_result[0])

                        elif interval_at_region_offset(split_interval, curr_region):
                            update_result = update_line(line, interval, split_interval, curr_subregion_diff)
                            new_cha.write(update_result[0])

                            if not curr_region.special:
                                new_cha.write("%com:\tregion {} of {} ends. (coded subregion) original timestamp end: {}\n". \
                                              format(curr_region.number,
                                                     num_regions,
                                                     curr_region.offset_ms))
                            else:
                                new_cha.write("%com:\tregion {} of {} ends. (extra region) original timestamp end: {}\n". \
                                              format(curr_region.number,
                                                     num_regions,
                                                     curr_region.offset_ms))

                            output_interval_tail = update_result[1][1]

                            if region_deque:
                                curr_region = region_deque.popleft()
                            begin_region_written = False
                            curr_subreg_num += 1


                    # non tiered region inside subregion
                    elif region_inside_region(curr_region, last_interval_read):
                        new_cha.write(line)

def update_line(line, old_interval, old_interval_int, diff):

    new_onset = old_interval_int[0] - diff
    new_offset = old_interval_int[1] - diff

    new_interval = "\x15{}_{}\x15".format(new_onset, new_offset)
    line = line.replace(old_interval, new_interval)
    return (line, [new_onset, new_offset])

def interval_at_region_offset(interval, subregion):
    if interval[1] == subregion.offset_ms:
        return True
    return False

def region_inside_interval(comp_interval, last_interval, curr_subregion):
    split_comp = comp_interval.split("_")
    split_comp = map(int, split_comp)

    split_last = last_interval.split("_")
    split_last = map(int, split_last)


def region_inside_region(subregion, cha_timestamp):
    if (subregion.onset_ms <= int(cha_timestamp[0])) and \
            (subregion.offset_ms > int(cha_timestamp[1])):
        return True
    return False

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

