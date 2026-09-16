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

""" Thin modem specific project creation system module """

from __future__ import print_function
import sys
sys.dont_write_bytecode = True

from pylib.common import *
import os
import os.path
import glob
import shutil

import pylib.log
log = pylib.log.get()

import pylib.config

__all__ = ["CreateProject"]

MUTO = "mtk/release/tools/muto"
OPENWRT_ROOT = "openwrt"
OPENWRT_TARGET_CONFIG = os.path.join(OPENWRT_ROOT, ".config")
SUPPORTED_ARCHS = ("arm", "aarch64")

class CreateProject(object):
    def __init__(self, opts):
        self.data = dict()

        for k in opts:
            self.data[k] = opts[k].strip()

        self.data["SYSMOD"] = "thin-modem"
        self.data["BASE_PROJECT_NAME"] = \
                os.path.basename(self.baseProjectPath())
        self.data["TARGET_PROJECT_NAME"] = \
                os.path.basename(self.targetProjectPath())

        # make defconfig if OPENWRT_TARGET_CONFIG does not exist
        self.makeDefconfig(self.baseProject())
        kconfig = pylib.config.loadKernelConfig(OPENWRT_TARGET_CONFIG)

        # make sure subtarget matches
        if kconfig["CONFIG_TARGET_SUBTARGET"] != self.baseProject():
            die("ERROR: base project name \"{}\" does not match "
                    "CONFIG_TARGET_SUBTARGET \"{}\" in {}. Please make sure "
                    ".config is created from base project first.".format(
                        self.baseProject(), kconfig["CONFIG_TARGET_SUBTARGET"],
                        OPENWRT_TARGET_CONFIG))

        # base arch
        self.data["BASE_ARCH"] = kconfig["CONFIG_ARCH"]
        if self.baseArch() == "aarch64":
            self.data["BASE_ARCH"] = "arm64"
            # Target arch aligns with base arch. Creating target project whose
            # arch differs from base project is not supported.
            self.data["TARGET_ARCH"] = self.data["BASE_ARCH"]

        # Platforms of base and target is identical
        self.data["BASE_PLATFORM"] = kconfig["CONFIG_TARGET_BOARD"]
        self.data["TARGET_PLATFORM"] = kconfig["CONFIG_TARGET_BOARD"]

        # is internal
        self.data["BASE_IS_INTERNAL"] = self.isInternal(self.baseProjectPath())
        self.data["TARGET_IS_INTERNAL"] = self.isInternal(self.targetProjectPath())

        # for backward compatibility
        self.data["CREATE_PLATFORM"] = 0

    def sysmod(self):
        return self.data["SYSMOD"]

    def baseArch(self):
        return self.data["BASE_ARCH"]

    def targetArch(self):
        return self.data["TARGET_ARCH"]

    def baseProject(self):
        return self.data["BASE_PROJECT_NAME"]

    def targetProject(self):
        return self.data["TARGET_PROJECT_NAME"]

    def baseProjectPath(self):
        return self.data["BASE_PROJECT_PATH"]

    def targetProjectPath(self):
        return self.data["TARGET_PROJECT_PATH"]

    def envcfgFile(self):
        return self.data["ENVCFG_FILE"]

    def manifest(self):
        return self.data["MANIFEST"]

    def makeDefconfig(self, subtarget):
        op = "create-project-sysmod.{}.CreateProject.makeDefconfig".format(
                self.data["SYSMOD"])
        if os.path.exists(OPENWRT_TARGET_CONFIG):
            log.info("{}: {} exists. No-op.".format(op, OPENWRT_TARGET_CONFIG))
            return

        # Locate the subtarget under openwrt/target/linux/*
        pPath = os.path.join(OPENWRT_ROOT, "target", "linux", "*", subtarget)
        pDir = glob.glob(pPath)

        if len(pDir) > 1:
            die("{}: found multiple subtargets: {}".format(op, pDir))
        if len(pDir) == 0:
            die("{}: cannot find subtarget {} with glob pattern {}".format(
                op, pPath))

        pDir = pDir[0]

        # make distclean first
        command = "make -C {} distclean".format(OPENWRT_ROOT)
        _, err, ret = cmd(command, o=sys.stdout, e=sys.stderr)
        if ret != 0:
            die("command \"{}\" failed: {}".format(command, err))

        # Copy the target.config
        shutil.copyfile(os.path.join(pDir, "target.config"),
                OPENWRT_TARGET_CONFIG)

        # make defconfig
        command = "make -C {} defconfig".format(OPENWRT_ROOT)
        _, err, ret = cmd(command, o=sys.stdout, e=sys.stderr)
        if ret != 0:
            die("command \"{}\" failed: {}".format(command, err))

    def isInternal(self, path):
        """ If the given path belongs to MTK internal. To align with shell
            script usage, return 1 for true and 0 for false.
        """

        op = "create-project-sysmod.{}.CreateProject.isInternal".format(
                self.data["SYSMOD"])

        if not os.path.exists(MUTO):
            log.info("Utility {} does not exist. Not internal".format(MUTO))
            return 0

        # Obtain the repo the target path belongs to, and fetch its release
        # policy
        command = "{} release-policy -kv-output -manifest {} {}".format(
                MUTO, self.manifest(), path)
        out, err, ret = cmd(command)
        if ret != 0:
            die("command \"{}\" failed: {}".format(command, err))

        rp = out.split("=")[1].strip()
        log.debug("{}: release policy of {} is \"{}\"".format(op, path, rp))

        if rp != "RELEASE_EVERYTHING":
            return 1

        return 0

    def addAttrs(self, attrs):
        """ add the dict attrs to internal data map """
        for k, v in attrs:
            if k in self.data:
                log.info("Update existing data {} from {} to {}".format(
                    k, self.data[k], v))
            self.data[k] = v

    def writeCfg(self):
        """ Dump the config dict to file """

        op = "create-project-sysmod.{}.CreateProject.writeCfg".format(
                self.data["SYSMOD"])
        with open(self.envcfgFile(), "w") as f:
            keys = self.data.keys()
            keys = sorted(keys)

            for k in keys:
                f.write("{}={}\n".format(k, self.data[k]))

        log.info("{}: config file {} is successfully created".format(
            op, self.envcfgFile()))
