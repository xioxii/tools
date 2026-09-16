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

r""" Config related functions or classes """
import re

from pylib.common import *

import pylib.log
log = pylib.log.get()

__all__ = ["loadKernelConfig", "loadKVPairs"]

def loadKernelConfig(fname):
    """ Load kernel-config styled config file into a dict """
    op = "pylib.config.loadKernelConfig"

    kconfig = dict()
    with open(fname, "r") as f:
        for line in f:
            line = line.strip()

            if len(line) == 0:
                continue

            if line.startswith("CONFIG_"):
                key = line.split("=", 1)[0]
                val = line.split("=", 1)[1]
                if val.startswith('"') and val.endswith('"'):
                    val = val[1:len(val) - 1]
                elif not val in ('y', 'm') and not re.match("[a-fA-FxX0-9]", val):
                    die("illegal entry {}: value is neither 'y' nor 'm'".format(
                        line))

                kconfig[key] = val
            elif line.startswith("# CONFIG_"):
                if line.endswith(" is not set"):
                    key = line[len("# "):-len(" is not set")]
                    val = 'n'
                    kconfig[key] = val
                else:
                    die("illegal entry {}: value does not end with "
                            "' is not set'".format(line))
            else:
                continue

    if False:
        log.debug("kconfig:\n")
        for k in kconfig:
            log.debug("{}={}".format(k, kconfig[k]))

    return kconfig

def loadKVPairs(fname):
    """ Load common key=value styled config file into a dict. Raises error if
        any key duplicates. """
    op = "pylib.config.loadKVPairs"

    cfgs = dict()
    with open(fname, "r") as f:
        for line in f:
            line = line.strip()

            if len(line) == 0:
                continue

            if line[0] == '#':
                continue

            key = line.split("=", 1)[0]
            val = line.split("=", 1)[1]

            if key in cfgs:
                die("{}: key {} redefined. Original value: {}, new value: "
                        "{}".format(op, key, cfgs[key], val))

            cfgs[key] = val

    if False:
        log.debug("{}:\n".format(op))
        for k in kconfig:
            log.debug("{}={}".format(k, kconfig[k]))

    return cfgs
