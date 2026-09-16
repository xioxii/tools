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

r""" Repo Manfiest management """
from pylib.common import *
import os.path
import re
import xml.dom.minidom

DefaultManifestXML = ".repo/manifest.xml"
ManifestDir = ".repo/manifests"

import pylib.log
log = pylib.log.get()

class Manifest(object):
    """
    Manifest XML parser. Use it as a Singleton.
    """
    def __init__(self):
        self.projects = dict() # {repo_name: ManifestProject }
        self.remote = ""
        self.revision = ""

    class ManifestProject(object):
        def __init__(self):
            self.name = ""
            self.path = ""
            self.revision = ""
            self.groups = []
            self.copyfiles = set()
            self.linkfiles = set()

    """ Parse a XML context """
    def parse(self, f):
        try:
            root = xml.dom.minidom.parse(f)

            for manifest in root.childNodes:
                if manifest.nodeName == "manifest":
                    break
            else:
                raise XMLParseException("No <manifest> defined")

            for node in manifest.childNodes:
                if node.nodeName == "project":
                    self.parseProject(node)
                elif node.nodeName == "default":
                    # <default remote="mediatek" revision="gem-trunk-1907" sync-j="4"/>

                    self.remote = self.reqatt(node, "remote")
                    self.revision = self.reqatt(node, "revision")
                elif node.nodeName == 'include':
                    name = self.reqatt(node, 'name')
                    fp = os.path.join(os.path.dirname(f), name)
                    self.parse(fp)

        except (OSError, xml.parsers.expat.ExpatError) as e:
            raise XMLParseException(e)

    def parseProject(self, node):
        m = self.ManifestProject()
        m.name = self.reqatt(node, "name")
        m.path = node.getAttribute("path")
        if not m.path:
            m.path = m.name

        if m.path in self.projects:
            return

        m.rev = node.getAttribute("revision")

        g = node.getAttribute("groups")
        if g:
            m.groups = [x for x in re.split(r'[,\s]+', g) if x]

        for n in node.childNodes:
            if n.nodeName == "copyfile":
                log.debug("Manifest: found copyfile, node path={}".format(
                    m.path))
                dst = self.reqatt(n, "dest")
                src = self.reqatt(n, "src")
                m.copyfiles.add((src, dst))
            elif n.nodeName == "linkfile":
                log.debug("Manifest: found linkfile, node path={}".format(
                    m.path))
                dst = self.reqatt(n, "dest")
                src = self.reqatt(n, "src")
                m.linkfiles.add((src, dst))

        self.projects[m.path] = m

    def reqatt(self, node, attname):
        """ reads a required attribute from the node. """
        v = node.getAttribute(attname)
        if not v:
            raise XMLParseException("no {} in <{}>".format(attname,
                node.nodeName))
        return v
