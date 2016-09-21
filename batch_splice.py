import sys
import os
import subprocess as sp

class FileGroup:
    def __init__(self, cha, subreg, audio):
        self.cha_file = cha
        self.subreg_csv = subreg
        self.audio_file = audio

    def __repr__(self):
        return "{}\n{}\n{}\n\n".format(self.cha_file, self.subreg_csv, self.audio_file)

def find_all_file_groups(start_dir):
    curr_index = 0
    curr_file = ""

    file_groups = []

    for root, dirs, files in os.walk(start_dir):
        for file in files:
            curr_file = file
            if file_already_in_groups(file, file_groups):
                continue

            # curr_file is the subregion csv
            if not curr_file.endswith(".cha") and not curr_file.endswith(".wav"):
                cha_path = None
                audio_path = None
                for file in files:
                    if file[0:5] == curr_file[0:5] and file.endswith(".cha"):
                        cha_path = os.path.join(root, file)

                    if file[0:5] == curr_file[0:5] and file.endswith(".wav"):
                        audio_path = os.path.join(root, file)
                curr_file = os.path.join(root, curr_file)
                group = FileGroup(cha_path, curr_file, audio_path)
                file_groups.append(group)
                continue

            # curr_file is the audio file
            if not curr_file.endswith(".cha") and not curr_file.endswith(".csv"):
                cha_path = None
                csv_path = None
                for file in files:
                    if file[0:5] == curr_file[0:5] and file.endswith(".cha"):
                        cha_path = os.path.join(root, file)

                    if file[0:5] == curr_file[0:5] and file.endswith(".csv"):
                        csv_path = os.path.join(root, file)

                curr_file = os.path.join(root, curr_file)
                group = FileGroup(cha_path, csv_path, curr_file)
                file_groups.append(group)
                continue

            # curr_file is the cha file
            if not curr_file.endswith(".wav") and not curr_file.endswith(".csv"):
                audio_path = None
                csv_path = None
                for file in files:
                    if file[0:5] == curr_file[0:5] and file.endswith(".wav"):
                        audio_path = os.path.join(root, file)

                    if file[0:5] == curr_file[0:5] and file.endswith(".csv"):
                        csv_path = os.path.join(root, file)

                curr_file = os.path.join(root, curr_file)
                group = FileGroup(curr_file, csv_path, audio_path)
                file_groups.append(group)
                continue

    return file_groups

def file_already_in_groups(file, groups):
    for group in groups:
        if file == os.path.basename(group.subreg_csv) or \
            file == os.path.basename(group.cha_file) or\
            file == os.path.basename(group.audio_file):
            return True
    return False

if __name__ == "__main__":

    data_dir = sys.argv[1]
    output_dir = sys.argv[2]

    file_groups = find_all_file_groups(data_dir)

    print file_groups

    with open("fail_list.csv", "wb") as fail_output:
        fail_output.write("problem_files\n")

    for group in file_groups:
        command = ["python", "subrsplice.py", group.cha_file, group.subreg_csv, group.audio_file, output_dir]
        command_string = " ".join(command)

        try:
            sp.check_output(command)
        except sp.CalledProcessError:
            with open("fail_list.csv", "a") as fail_output:
                fail_output.write("{}\n".format(group.subreg_csv))

        # pipe = sp.Popen(command, stdout=FNULL, bufsize=10 ** 8)
        # out, err = pipe.communicate()
