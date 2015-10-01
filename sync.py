#!/usr/bin/env python3

import sys, os, json, hashlib, datetime, time, shutil


def create_path(root, filename):
    return os.path.normpath(os.path.join(root, filename))


def write(data, path):

    file = open(path, "w")
    if len(data) > 0:
        str_out = json.dumps(data)
        file.write(str_out)
    file.close()


def read_file(filepath):
    data = {}
    if os.path.isfile(filepath):
        if os.path.getsize(filepath) > 0:
            file = open(filepath, "r")
            str_in = file.read()
            file.close()
            data = json.loads(str_in)
    return data


def read_string(filename):
    file = open(filename, "r")
    str_in = file.read()
    return str_in


def update_sync(root, dirs, files):
    os.chdir(root)
    file_dic = {}
    sync_file_path = create_path(os.getcwd(), ".sync")

    file_dic = read_file(sync_file_path)
    for file_name in file_dic.keys():
        if file_dic[file_name][0][1] != "deleted" and file_name not in files:
            current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
            file_dic[file_name].insert(0, [current_time, "deleted"])

    for file_name in files:
        if file_name == ".sync":
            continue

        file_str = read_string(file_name)
        digest = hashlib.sha256(file_str.encode("utf-8")).hexdigest()
        path = create_path(os.getcwd(), file_name)

        cur_mod_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(path)))
        if file_name in file_dic:
            if file_dic[file_name][0][1] == digest:
                if file_dic[file_name][0][0] != cur_mod_time:
                    os.utime(path,
                             (os.path.getatime(path), time.strptime(file_dic[file_name][0][0], "%Y-%m-%d %H:%M:%S")))

            else:
                file_dic[file_name].insert(0, [cur_mod_time, digest])
        else:
            file_dic[file_name] = list([[cur_mod_time, digest]])

    write(file_dic, ".sync")

    return


def merge(root, dirs, files, dir1, dir2):
    os.chdir(root)
    abs_path1 = root
    abs_path2 = create_path(dir2, os.path.relpath(abs_path1, dir1))


    if not os.path.isdir(abs_path1):
        os.mkdir(abs_path1)
    
    if not os.path.isdir(abs_path2):
        os.mkdir(abs_path2)
    
    sync_file_path1 = create_path(abs_path1, ".sync")
    sync_file_path2 = create_path(abs_path2, ".sync")
    sync_dic1 = read_file(sync_file_path1)
    sync_dic2 = read_file(sync_file_path2)

    for file_name in sync_dic1.keys():
        digest1 = sync_dic1[file_name][0][1]
        change_time1 = time.strptime(sync_dic1[file_name][0][0], "%Y-%m-%d %H:%M:%S")

        if file_name not in sync_dic2.keys():
            if digest1 != "deleted":
                shutil.copy2(create_path(abs_path1, file_name), abs_path2)
                sync_dic2[file_name] = list([sync_dic1[file_name][0]])
            else:
                pass
        else:
            digest2 = sync_dic2[file_name][0][1]
            change_time2 = time.strptime(sync_dic2[file_name][0][0], "%Y-%m-%d %H:%M:%S")

            if digest1 == "deleted":
                if digest2 == "deleted":
                    pass
                else:
                    file_is_new = False
                    for key_value_pair in sync_dic2[file_name]:
                        if key_value_pair == sync_dic1[file_name][0]:
                            file_is_new = True
                            break
                    if file_is_new == True:
                        shutil.copy2(create_path(abs_path2, file_name), abs_path1)
                        sync_dic1[file_name].insert(0, list(sync_dic2[file_name][0]))
                    else:
                        os.remove(create_path(abs_path2, file_name))

                        sync_dic2[file_name].insert(0, list(sync_dic1[file_name][0]))
            else:
                if digest2 == "deleted":
                    file_is_new = False
                    for key_value_pair in sync_dic1[file_name]:
                        if key_value_pair == sync_dic2[file_name][0]:
                            file_is_new = True
                            break
                    if file_is_new == True:
                        shutil.copy2(create_path(abs_path1, file_name), abs_path2)
                        sync_dic2[file_name].insert(0, list(sync_dic1[file_name][0]))
                    else:
                        os.remove(create_path(abs_path1, file_name))
                        sync_dic1[file_name].insert(0, list(sync_dic2[file_name][0]))
                else:
                    if digest1 == digest2:
                        if change_time1 > change_time2:
                            sync_dic2[file_name][0][0] = sync_dic1[file_name][0][0]
                        if change_time1 <= change_time2:
                            sync_dic1[file_name][0][0] = sync_dic2[file_name][0][0]
                    else:
                        if change_time1 > change_time2:
                            sync_dic2[file_name].insert(0, list(sync_dic1[file_name][0]))
                            shutil.copy2(create_path(abs_path1, file_name), abs_path2)
                        if change_time1 <= change_time2:
                            sync_dic1[file_name].insert(0, list(sync_dic2[file_name][0]))
                            shutil.copy2(create_path(abs_path2, file_name), abs_path1)

    write(sync_dic1, sync_file_path1)
    write(sync_dic2, sync_file_path2)


def main():
    dir1 = os.path.abspath(sys.argv[1])
    dir2 = os.path.abspath(sys.argv[2])

    if not os.path.isdir(dir1) and not os.path.isdir(dir2):
        raise Exception("cannot create directories")
    if not os.path.isdir(dir1):
        os.mkdir(dir1)
    if not os.path.isdir(dir2):
        os.mkdir(dir2)

    for root, dirs, files in os.walk(dir1, topdown=True):
        update_sync(root, dirs, files)

    for root, dirs, files in os.walk(dir2, topdown=True):
        update_sync(root, dirs, files)

    for root, dirs, files in os.walk(dir1, topdown=True):
        merge(root, dirs, files, dir1, dir2)

    for root, dirs, files in os.walk(dir2, topdown=True):
        merge(root, dirs, files, dir2, dir1)


main()
