# Copyright 2021 the rdiff-backup project
#
# This file is part of rdiff-backup.
#
# rdiff-backup is free software; you can redistribute it and/or modify
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# rdiff-backup is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with rdiff-backup; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA

"""
A built-in rdiff-backup action plug-in to regress a failed back-up from a
back-up repository.
"""

from rdiffbackup import actions
from rdiffbackup.locations import repository
from rdiffbackup.singletons import consts


class RegressAction(actions.BaseAction):
    """
    Regress a backup repository, i.e. remove the last (failed) incremental
    backup and reverse to the last known good mirror.
    """

    name = "regress"
    security = "backup"
    parent_parsers = [
        actions.COMPRESSION_PARSER,
        actions.TIMESTAMP_PARSER,
        actions.USER_GROUP_PARSER,
    ]

    @classmethod
    def add_action_subparser(cls, sub_handler):
        subparser = super().add_action_subparser(sub_handler)
        subparser.add_argument(
            "locations",
            metavar="[[USER@]SERVER::]PATH",
            nargs=1,
            help="location of repository to check and possibly regress",
        )
        return subparser

    def connect(self):
        conn_value = super().connect()
        if conn_value.is_connection_ok():
            self.repo = repository.Repo(
                self.connected_locations[0],
                self.values,
                must_be_writable=True,
                must_exist=True,
            )
        return conn_value

    def check(self):
        # we try to identify as many potential errors as possible before we
        # return, so we gather all potential issues and return only the final
        # result
        ret_code = super().check()

        # we verify that the source repository is correct
        ret_code |= self.repo.check()

        return ret_code

    def setup(self):
        # in setup we return as soon as we detect an issue to avoid changing
        # too much
        ret_code = super().setup()
        if ret_code & consts.RET_CODE_ERR:
            return ret_code

        ret_code = self.repo.setup()
        if ret_code & consts.RET_CODE_ERR:
            return ret_code

        return ret_code

    def run(self):
        """
        Check the given repository and regress it if necessary
        """
        ret_code = super().run()
        if ret_code & consts.RET_CODE_ERR:
            return ret_code

        ret_code |= self._operate_regress(noticeable=True, force=self.values["force"])

        return ret_code


def get_plugin_class():
    return RegressAction
