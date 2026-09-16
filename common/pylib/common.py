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

r""" Generic and common functions or classes """
import subprocess
import sys

import pylib.log
log = pylib.log.get()

__all__ = ["cmd", "die", "gg"]

# Execute a command and return stdout, stderr and error number.
def cmd(command, o=subprocess.PIPE, e=subprocess.PIPE):
    """ Create an external process to execute command """

    log.info('cmd({})'.format(command))
    # Assign executable to /bin/bash instead of default /bin/sh due to
    # Android Q's limitation. Some shell scripts fail with /bin/sh.
    res = subprocess.Popen(command, stdout=o, stderr=e, shell=True,
            executable="/bin/bash")
    out, err = res.communicate()
    #if err:
    #    log.warning("cmd: command \"{}\" returned {}: {}".format(
    #                command, res.returncode, err))
    #log.debug('cmd({}) stdout: {}, stderr: {}, return code: {}'.format(
    #    command, out, err, res.returncode))

    return out, err, res.returncode

def die(msg):
    """ Raise exception with provided message, mainly to be used in threads."""
    raise ValueError(msg)

def gg(msg):
    """ Print msg to stderr and bail out the program with sys.exit().

    #######################################################################
    #                            W A R N I N G                            #
    #                                                                     #
    # DO NOT USE THIS IN THREADED PROCESSES, because it uses sys.exit()   #
    #######################################################################

    If in doubt whether die() or gg() can be used, use die().
    """
    log.fatal("\n\n{}\nERROR: {}\n{}".format("*" * 80, msg, "*" * 80))
    sys.exit(-1)
