#!/usr/bin/env python
#
# Copyright Statement:
#
# This software/firmware and related documentation ("MediaTek Software") are
# protected under relevant copyright laws. The information contained herein is
# confidential and proprietary to MediaTek Inc. and/or its licensors. Without
# the prior written permission of MediaTek inc. and/or its licensors, any
# reproduction, modification, use or disclosure of MediaTek Software, and
# information contained herein, in whole or in part, shall be strictly
# prohibited.
#
# MediaTek Inc. (C) 2020. All rights reserved.
#
# BY OPENING THIS FILE, RECEIVER HEREBY UNEQUIVOCALLY ACKNOWLEDGES AND AGREES
# THAT THE SOFTWARE/FIRMWARE AND ITS DOCUMENTATIONS ("MEDIATEK SOFTWARE")
# RECEIVED FROM MEDIATEK AND/OR ITS REPRESENTATIVES ARE PROVIDED TO RECEIVER
# ON AN "AS-IS" BASIS ONLY. MEDIATEK EXPRESSLY DISCLAIMS ANY AND ALL
# WARRANTIES, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE OR
# NONINFRINGEMENT. NEITHER DOES MEDIATEK PROVIDE ANY WARRANTY WHATSOEVER WITH
# RESPECT TO THE SOFTWARE OF ANY THIRD PARTY WHICH MAY BE USED BY,
# INCORPORATED IN, OR SUPPLIED WITH THE MEDIATEK SOFTWARE, AND RECEIVER AGREES
# TO LOOK ONLY TO SUCH THIRD PARTY FOR ANY WARRANTY CLAIM RELATING THERETO.
# RECEIVER EXPRESSLY ACKNOWLEDGES THAT IT IS RECEIVER'S SOLE RESPONSIBILITY TO
# OBTAIN FROM ANY THIRD PARTY ALL PROPER LICENSES CONTAINED IN MEDIATEK
# SOFTWARE. MEDIATEK SHALL ALSO NOT BE RESPONSIBLE FOR ANY MEDIATEK SOFTWARE
# RELEASES MADE TO RECEIVER'S SPECIFICATION OR TO CONFORM TO A PARTICULAR
# STANDARD OR OPEN FORUM. RECEIVER'S SOLE AND EXCLUSIVE REMEDY AND MEDIATEK'S
# ENTIRE AND CUMULATIVE LIABILITY WITH RESPECT TO THE MEDIATEK SOFTWARE
# RELEASED HEREUNDER WILL BE, AT MEDIATEK'S OPTION, TO REVISE OR REPLACE THE
# MEDIATEK SOFTWARE AT ISSUE, OR REFUND ANY SOFTWARE LICENSE FEES OR SERVICE
# CHARGE PAID BY RECEIVER TO MEDIATEK FOR SUCH MEDIATEK SOFTWARE AT ISSUE.
#
# The following software/firmware and/or related documentation ("MediaTek
# Software") have been modified by MediaTek Inc. All revisions are subject to
# any receiver's applicable license agreements with MediaTek Inc.

""" Entry script for creating projects based on MTK-release ones
"""

from __future__ import print_function
import sys
sys.dont_write_bytecode = True

from pylib.common import *
import os
import os.path
import argparse
import subprocess
import logging
import pkgutil
import importlib
import re
import xml.dom.minidom
import distutils.spawn
import hashlib

import pylib.log
log = pylib.log.get()

import pylib.manifest

DEFAULT_MANIFEST = ".repo/manifest.xml"
DEFAULT_ENVCFG_FILE= os.path.join(os.getcwd(), "create-project.cfg")
SYSMOD_DIRNAME = "create-project-sysmod"
REQUIRED_UTILITIES = ["rsync"]
EXECUTABLE_FILENAME = ".create-project" # name of executable in each repo
DEFAULT_CR = "ALPS05048943"
REQUIRED_VARS = (
"BASE_ARCH",
"BASE_IS_INTERNAL",
"BASE_PLATFORM",
"BASE_PROJECT_NAME",
"BASE_PROJECT_PATH",
"ENVCFG_FILE",
"MANIFEST",
"SYSMOD",
"TARGET_ARCH",
"TARGET_IS_INTERNAL",
"TARGET_PLATFORM",
"TARGET_PROJECT_NAME",
"TARGET_PROJECT_PATH",
)

def main():
    op = "main"

    p = argparse.ArgumentParser(prog="create-project.py", add_help=True,
            description="Create a new project based on an existing one",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("base", metavar="BASE_PATH", help="The path of the existing "
            "project to clone from. The path starts from the root of all "
            "repositories. For example in OpenWrt it's "
            "openwrt/target/linux/foo/base, and in Android device/foo/base")
    p.add_argument("target", metavar="TARGET_PATH", help="The path of the new "
            "project to be created. The path starts from the root of all "
            "repositories. For example in OpenWrt it's "
            "openwrt/target/linux/foo/target, and in Android device/foo/target")
    p.add_argument("--clean", action="store_true", default=False,
            dest="clean", help="Clean up untracked files in each repo that "
            "supports project creation. Note that this option can only "
            "clean up dirty contents. If the changes were added into git "
            "commits this option will not reset them.")
    p.add_argument("--reset", action="store_true", default=False,
            dest="reset", help="Reset git history to remote revision and "
            "remove untracked files in repos that support project "
            "creation, along with their nested repos. Be sure no pending "
            "commits or untracked files exist there.")
    p.add_argument("--manifest", type=str, default=DEFAULT_MANIFEST,
            dest="manifest", metavar="MANIFEST_XML",
            help="The path of manifest file, used to fetch the full repo list.")
    p.add_argument("--envcfg-file", type=str, default=DEFAULT_ENVCFG_FILE,
            dest="envCfgFile", metavar="ENVCFG_FILE",
            help="Create the environment config file in the assigned path.")
    p.add_argument("--sysmod", type=str, default="", dest="sysMod",
            metavar="SYSMOD_NAME", help="Load the specified Python module "
            "to generated environment config file. The module implements "
            "the APIs to fetch required variables from the code base or build "
            "system. The provided name need not end with .py, and must be "
            "placed under the directory {}. If there is only one module "
            "available this option can be ignored.".format(
                SYSMOD_DIRNAME))
    p.add_argument("--cr", type=str, default=DEFAULT_CR,
            dest="cr", metavar="CR_ID",
            help="MTK CR used in git commit message")
    p.add_argument("--no-cr", action="store_true", default=False,
            dest="noCR", help="Do not include MTK CR ID in git commit "
            "message")
    p.add_argument("--change-id", type=str, default="",
            dest="changeID", metavar="CHANGE_ID",
            help="Gerrit change ID used in git commit message. If empty, a "
            "whole new change ID is created.")
    p.add_argument("--cfg-only", action="store_true", default=False,
            dest="cfgOnly", help="Create env config file without triggering "
            "repo-specific operations")
    p.add_argument("--dont-commit", action="store_true", default=False,
            dest="dontCommit", help="Do not create git commits after all "
            "project creation operations are done.")
    p.add_argument("--print-exec-repos", action="store_true", default=False,
            dest="printExecRepos", help="Print repos that will execute project "
            "creation operations.")
    p.add_argument("--attrs", type=str, default="",
            dest="attrs", metavar="FOO=BAR,...",
            help="A list of KEY=VALUE strings, separated by comma. It will be "
            "converted into environment variables and added in the generated "
            "configuration file.")
    # p.add_argument("--log-level", type=str, default="DEBUG",
    #         dest="loglvl", metavar="LOG_LEVEL", help="log level")
    args = vars (p.parse_args())

    # Ensure we are in the top directory of the codebase and manifest exists
    if not os.path.exists(DEFAULT_MANIFEST):
        gg("{}: default manifest {} does not exist".format(op,
            DEFAULT_MANIFEST))

    if not os.path.isdir("mtk") or not os.path.isdir("openwrt"):
        gg("{}: either mtk/ or openwrt/ directory does not exist. Please "
            "make sure your working directory is the top of codebase".format(
                op))

    # test utility availbility
    for prog in REQUIRED_UTILITIES:
        if distutils.spawn.find_executable(prog) == "":
            gg("{}: required utility \"{}\" is missing".format(op, prog))

    # Look for repos with EXECUTABLE_FILENAME
    mf = pylib.manifest.Manifest()
    mf.parse(args["manifest"])

    execRepos = list()
    for repoPath in mf.projects:
        p = os.path.join(repoPath, EXECUTABLE_FILENAME)
        if os.path.isfile(p):
            # Make sure the executable can be executed
            if not os.access(p, os.X_OK):
                gg("{}: {} has no execute permission".format(op, p))

            execRepos.append(repoPath)

    execRepos = sorted(execRepos)

    # print-exec-repos operation
    if args["printExecRepos"]:
        print("\n".join(execRepos))
        return 0

    log.debug("{}: {} repo path(s) containing {}:".format(op, len(execRepos),
            EXECUTABLE_FILENAME))
    for i in execRepos:
        log.debug("  * {}".format(i))

    # clean operation
    if args["clean"]:
        cleanRepos(mf, execRepos)
        return 0

    # reset operation
    if args["reset"]:
        resetRepos(mf, execRepos, mf.revision)
        return 0

    basePath = args["base"]
    baseProject = os.path.basename(basePath)
    if not os.path.exists(basePath):
        gg("{} does not exist".format(basePath))

    targetPath = args["target"]
    targetProject = os.path.basename(targetPath)
    if os.path.exists(targetPath):
        gg("{} already exists".format(targetPath))

    # Load sysmod
    sysmodDirPath = os.path.join(os.path.dirname(sys.argv[0]), SYSMOD_DIRNAME)
    sysmods = [ name for _, name, _ in pkgutil.iter_modules([sysmodDirPath]) ]
    mod = None

    if args["sysMod"] != "":
        mod = args["sysMod"]
    else:
        if len(sysmods) > 1:
            gg("Multiple sysmods found. --sysmod option is mandatory.")
        mod = sysmods[0]

    sysmod = importlib.import_module("{}.{}".format(SYSMOD_DIRNAME, mod))
    log.info("Imported {}".format(sysmod.__name__))

    opts = dict()
    opts["BASE_PROJECT_PATH"] = basePath
    opts["TARGET_PROJECT_PATH"] = targetPath
    opts["MANIFEST"] = args["manifest"]
    opts["ENVCFG_FILE"] = args["envCfgFile"]

    cp = sysmod.CreateProject(opts)

    if args["attrs"] != "":
        v = args["attrs"].split(",")
        attrMap = dict()
        for i in v:
            key = v.split("=", 1)[0]
            val = v.split("=", 1)[1]
            attrMap[key] = val

        cp.addAttrs(attrs)

    cp.writeCfg()

    # Verify that all required keys are available
    cfgs = pylib.config.loadKVPairs(args["envCfgFile"])
    # log.debug("Created config: {}".format(cfgs))

    missingVars = list()
    for i in REQUIRED_VARS:
        if not i in cfgs:
            missingVars.append(i)

    if len(missingVars) != 0:
        gg("{}: config file {} misses the following required keys: {}".format(
            op, args["envCfgFile"], missingVars))

    log.debug("{} env configs:".format(op))
    for i in cfgs:
        log.debug("  * {}={}".format(i, cfgs[i]))

    if args["cfgOnly"]:
        return 0

    # Execute repo-specific operations
    rootDir = os.getcwd()

    for i in execRepos:
        os.chdir(i)
        log.info("{}: entering directory {}".format(op, i))

        cfgPath = args["envCfgFile"]
        if cfgPath[0] != '/':
            cfgPath = os.path.join(rootDir, args["envCfgFile"])

        command = "./{} {}".format(EXECUTABLE_FILENAME, cfgPath)
        r, e, ret = cmd(command)
        if ret != 0:
            gg("{}: command \"{}\" failed with return code {}: {}".format(
                i, command, ret, e))

        log.info("{}: output of {}:\n{}".format(op, i, r))
        log.info("{}: leaving directory {}".format(op, i))
        os.chdir(rootDir)

    if args["dontCommit"]:
        log.info("\n\n{}\n    Job's done\n{}".format("*" * 80, "*" * 80))
        return 0

    msg = gitCommitMessage(args, cp.data)
    log.debug("{}: git commit message:\n\n{}\n{}\n{}\n".format(
        op, "#" * 40, msg, "#" * 40))

    if not gitUpload(mf, execRepos, msg):
        return 1

    log.info("\n\n{}\n    Job's done\n{}".format("*" * 80, "*" * 80))
    return 0

def cleanRepos(mf, repos):
    """ Revert modified files and remove untracked files in given repos, including nested repos """
    allRepos = list()

    # collect nested repos too
    for r in repos:
    #    for root, dirs, files in os.walk(r):
    #        if ".git" in dirs:
    #            allRepos.append(root)
        for p in mf.projects:
            if r == p or p.startswith(r + "/"):
                allRepos.append(p)

    pwd = os.getcwd()
    for i in allRepos:
        if not os.path.exists(i):
            continue

        os.chdir(i)
        log.info("Cleaning {} ...".format(i))

        # check for untracked files
        command = "git ls-files --others --exclude-standard"
        r, e, ret = cmd(command)
        if ret != 0:
            gg("{}: command \"{}\" failed with return code {}: {}".format(
                i, command, ret, e))

        if r != "":
            command = "git clean -f -d"
            log.info("{}: untracked contents found. Execute {}".format(i, command))
            r, e, ret = cmd(command)
            if ret != 0:
                gg("{}: command \"{}\" failed with return code {}: {}".format(
                    i, command, ret, e))
        else:
            log.info("{}: no untracked contents found. No-op".format(i))

        # check for modified
        command = "git ls-files -m"
        r, e, ret = cmd(command)
        if ret != 0:
            gg("{}: command \"{}\" failed with return code {}: {}".format(
                i, command, ret, e))

        if r != "":
            command = "git checkout -- ."
            log.info("{}: modified contents found. Execute {}".format(i, command))
            o, e, ret = cmd(command)
            if ret != 0:
                gg("{}: command \"{}\" failed with return code {}: {}".format(
                    i, command, ret, e))
        else:
            log.info("{}: no modified contents found. No-op".format(i))

        log.info("Cleaned up {}".format(i))

        os.chdir(pwd)

    return True

def resetRepos(mf, repos, revision):
    """ Reset git history to remote revision and remove untracked files in
    given repos, including nested ones """
    allRepos = list()

    # collect nested repos too
    for r in repos:
        for p in mf.projects:
            if r == p or p.startswith(r + "/"):
                allRepos.append(p)

    pwd = os.getcwd()
    for i in allRepos:
        if not os.path.exists(i):
            continue

        os.chdir(i)
        log.info("Restting {} ...".format(i))

        # check for untracked files
        command = "git ls-files --others --exclude-standard"
        r, e, ret = cmd(command)
        if ret != 0:
            gg("{}: command \"{}\" failed with return code {}: {}".format(
                i, command, ret, e))

        if r != "":
            command = "git clean -f -d"
            log.info("{}: untracked contents found. Execute {}".format(i, command))
            r, e, ret = cmd(command)
            if ret != 0:
                gg("{}: command \"{}\" failed with return code {}: {}".format(
                    i, command, ret, e))
        else:
            log.info("{}: no untracked contents found. No-op".format(i))

        # Reset to remote
        command = "git reset --hard m/{}".format(revision)
        r, e, ret = cmd(command)
        if ret != 0:
            gg("{}: command \"{}\" failed with return code {}: {}".format(
                i, command, ret, e))

        log.info("Done resetting {}".format(i))

        os.chdir(pwd)

    return True

def gitCommitMessage(args, opts):
    """ Forge git commit message from system args and project creation
    config opts
    """
    op = "gitCommitMessage"

    header = "create subtarget {}".format(opts["TARGET_PROJECT_NAME"])
    if not args["noCR"]:
        header = "[{}] {}".format(args["cr"], header)

    body = "Created from {}".format(opts["BASE_PROJECT_NAME"])

    footer = ""
    changeID = args["changeID"]
    if changeID == "":
        changeID = genChangeID()
    footer = "Change-Id: {}".format(changeID)

    if not args["noCR"]:
        footer = "{}\nCR-Id: {}".format(footer, args["cr"])

    feature = "Configuration"
    footer = "{}\nFeature: Configuration".format(footer)

    msg = "{}\n\n{}\n\n{}".format(header, body, footer)

    return msg

def genChangeID():
    op = "genChangeID"

    fd = open("/dev/urandom", "rb")
    buf = fd.read(64)
    if len(buf) != 64:
        gg("{}: unable to get random data".format(op))

    return "I" + hashlib.sha1(buf).hexdigest()

def gitUpload(mf, repos, msg):
    op = "gitUpload"

    allRepos = list()

    # collect nested repos too
    for r in repos:
        for p in mf.projects:
            if r == p or p.startswith(r + "/"):
                allRepos.append(p)

    log.debug("{}: allRepos={}".format(op, "\n".join(allRepos)))

    pwd = os.getcwd()
    for i in allRepos:
        os.chdir(pwd)
        log.info("{}: processing {} ...".format(op, i))

        if not os.path.exists(i):
            log.info("{}: {}: repo does not exist. Ignored.".format(op, i))
            continue

        os.chdir(i)

        # No-op if no changes found
        gotChanges = False
        commands = ("git ls-files --others --exclude-standard",
                "git ls-files -m")
        for c in commands:
            r, e, ret = cmd(c)
            if ret != 0:
                log.error("{}: {}: command \"{}\" failed with return code "
                        "{}: {}".format(op, i, c, ret, e))
                return False

            if r != "":
                gotChanges = True
                break

        if not gotChanges:
            log.info("{}: {}: no changes found. No-op.".format(op, i))
            continue

        commands = ("git add -A",
                "git commit --signoff -m \"{}\"".format(msg),
                "git push {} HEAD:refs/for/{}".format(mf.remote, mf.revision))

        for c in commands:
            #log.debug("{}: {}: command: {}".format(op, i, c))
            r, e, ret = cmd(c)
            if ret != 0:
                log.error("{}: {}: command \"{}\" failed with return code "
                        "{}: {}".format(op, i, c, ret, e))
                return False


    os.chdir(pwd)

    return True

if "__main__"==__name__:
    ret = main()
    sys.exit(ret)
