'''copy modem binary files to AP'''
import json
import argparse
import sys
import os
import fnmatch
import shutil

def loadjson(file):
    '''load and return specified json file'''
    data = {}
    with open(file) as json_file:
        data = json.load(json_file)
    return data

def get_file_from_path(path, file_pattern):
    '''find "file_pattern" under path'''
    return fnmatch.filter(os.listdir(path), file_pattern)

def check_path_exist(path):
    '''check path exist or not'''
    if not os.path.exists(path):
        print("path '%s' not exist" %(path))
        sys.exit(-1)

def copy_files(mapping):
    '''based on src/dst, exe copy'''
    for src in mapping:
        if os.path.isdir(src):
            if os.path.exists(mapping[src]):
                shutil.rmtree(mapping[src])
            shutil.copytree(src, mapping[src])
        else:
            shutil.copy(src, mapping[src])

def remove_files(path, files_to_removed):
    '''remove 'files_to_removed' under path'''
    for file_name in files_to_removed:
        target_file = os.path.join(path, file_name)
        print("remove file %s from %s" %(file_name, path))
        os.remove(target_file)

def check_file_status(multiple, files, pattern, path):
    '''check source file status'''
    # if more than one match or not thing match, then report error.
    if multiple is None and len(files) > 1:
        print("more than one file matched pattern '%s' in %s! %s"
              %(pattern, path, files))
        sys.exit(-1)

    # if nothing found, report error
    if len(files) == 0:
        print("nothing matched specified pattern '%s' in %s" %(pattern, path))
        sys.exit(-1)

def prepare_copy_mapping(copy_mapping, files, source_path, prebuilt_modem_path, rename_as_file):
    '''prepare src/dst mapping for copy operation'''
    for file_name in files:
        src_file = os.path.join(source_path, file_name)

        if rename_as_file is not None:
            file_name = rename_as_file

        dst_file = os.path.join(prebuilt_modem_path, file_name)

        copy_mapping[src_file] = dst_file


def main():
    '''main function'''
    param = argparse.ArgumentParser(description="copy modem bin")
    param.add_argument('prebuilt_modem_path', help='folder to store modem bin')
    param.add_argument('md_build_path', help='abs path to md build dir')

    args = vars (param.parse_args())
    prebuilt_modem_path = args['prebuilt_modem_path']
    md_build_path = args['md_build_path']

    ##################
    #  check path exist
    ##################
    check_path_exist(prebuilt_modem_path)
    check_path_exist(md_build_path)

    # load json file
    script_loc = os.path.dirname(__file__)
    targets = loadjson( os.path.join(script_loc, "md_file.json"))

    # store copy commands
    copy_mapping = {}

    for key in targets:
        item = targets[key]

        item_type = item["type"]
        if item_type == "must":

            source_path = os.path.join(md_build_path, item.get("path"))
            files = get_file_from_path(source_path, key)

            # check souce file match expectation or not
            check_file_status(item.get("multiple"), files, key, source_path)

            # create mapping
            prepare_copy_mapping(copy_mapping,
                                   files,
                                   source_path,
                                   prebuilt_modem_path,
                                   item.get("rename"))

            # remove existing files
            if item.get("remove") is not None:
                files_to_removed = get_file_from_path(prebuilt_modem_path, key)
                remove_files(prebuilt_modem_path, files_to_removed)

    copy_files(copy_mapping)

if __name__ == '__main__':
    main()
