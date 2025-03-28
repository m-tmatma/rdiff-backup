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
This module/package contains the default command line parsers which can be
used by action plugins. It also defines a BaseAction class from which such
plugins can inheritate default behaviors.
"""

import argparse
import os
import platform
import sys
import tempfile
import yaml
from rdiff_backup import Security, SetConnections, Time
from rdiffbackup.singletons import consts, log, specifics
from rdiffbackup.utils import argopts

# The default regexp for not compressing those files
DEFAULT_NOT_COMPRESSED_REGEXP = (
    "(?i).*\\.("
    "7z|aac|arj|asc|avi|bik|bz|bz2|deb|docx|flac|flv|gif|gpg|gz|jp2|jpeg|jpg|"
    "jsonlz4|lharc|lz4|lzh|lzma|lzo|m4a|m4v|mdf|mkv|mov|mozlz4|mp3|mp4|mpeg|"
    "mpg|oga|ogg|ogm|ogv|opus|pgp|pk3|png|rar|rm|rpm|rz|shn|tgz|tzst|vob|webm|"
    "webp|wma|wmv|xlsx|xz|z|zip|zoo|zst"
    ")$"
)

# === DEFINE COMMON PARSER ===


COMMON_PARSER = argparse.ArgumentParser(
    add_help=False, description="[parent] common options to all actions"
)
COMMON_PARSER.add_argument(
    "--api-version",
    type=int,
    help="[opt] integer to set the API version forcefully used",
)
COMMON_PARSER.add_argument(
    "--current-time",
    type=int,
    help="[opt] fake the current time in seconds (for testing)",
)
COMMON_PARSER.add_argument(
    "--force",
    action="store_true",
    help="[opt] force action (caution, the result might be dangerous)",
)
COMMON_PARSER.add_argument(
    "--fsync",
    default=True,
    action=argparse.BooleanOptionalAction,
    help="[opt] do (or not) often sync the file system (_not_ doing it is faster but can be dangerous)",
)
COMMON_PARSER.add_argument(
    "--null-separator",
    action="store_true",
    help="[opt] use null instead of newline in input and output files",
)
COMMON_PARSER.add_argument(
    "--chars-to-quote",
    type=str,
    metavar="CHARS",
    help="[opt] string of characters to quote for safe storing",
)
COMMON_PARSER.add_argument(
    "--parsable-output",
    action="store_true",
    help="[opt] output in computer parsable format",
)
COMMON_PARSER.add_argument(
    "--remote-schema",
    type=str,
    help="[opt] alternative command to call remotely rdiff-backup",
)
COMMON_PARSER.add_argument(
    "--remote-tempdir",
    type=str,
    metavar="DIR_PATH",
    help="[opt] use path as temporary directory on the remote side",
)
COMMON_PARSER.add_argument(
    "--ssh-compression",
    default=True,
    action=argparse.BooleanOptionalAction,
    help="[opt] use SSH without compression with default remote-schema",
)
COMMON_PARSER.add_argument(
    "--tempdir",
    type=str,
    metavar="DIR_PATH",
    help="[opt] use given path as temporary directory",
)
COMMON_PARSER.add_argument(
    "--terminal-verbosity",
    type=int,
    choices=range(0, 10),
    help="[opt] verbosity on the terminal, default given by --verbosity",
)
COMMON_PARSER.add_argument(
    "--use-compatible-timestamps",
    action="store_true",
    help="[opt] use hyphen '-' instead of colon ':' to represent time",
)
COMMON_PARSER.add_argument(
    "-v",
    "--verbosity",
    type=int,
    choices=range(0, 10),
    default=int(os.getenv("RDIFF_BACKUP_VERBOSITY", "3")),
    help="[opt] overall verbosity on terminal and in logfiles (default is 3)",
)


# === DEFINE PARENT PARSERS ===


SELECTION_PARSER = argparse.ArgumentParser(
    add_help=False, description="[parent] options related to file selection"
)
SELECTION_PARSER.add_argument(
    "--SELECT",
    action=argopts.SelectAction,
    metavar="GLOB",
    help="[sub] SELECT files according to glob pattern",
)
SELECTION_PARSER.add_argument(
    "--SELECT-device-files",
    action=argopts.SelectAction,
    type=bool,
    default=True,
    help="[sub] SELECT device files",
)
SELECTION_PARSER.add_argument(
    "--SELECT-fifos",
    action=argopts.SelectAction,
    type=bool,
    default=True,
    help="[sub] SELECT fifo files",
)
SELECTION_PARSER.add_argument(
    "--SELECT-filelist",
    action=argopts.SelectAction,
    metavar="LIST_FILE",
    help="[sub] SELECT files according to list in given file",
)
SELECTION_PARSER.add_argument(
    "--SELECT-filelist-stdin",
    action=argopts.SelectAction,
    type=bool,
    help="[sub] SELECT files according to list from standard input",
)
SELECTION_PARSER.add_argument(
    "--SELECT-symbolic-links",
    action=argopts.SelectAction,
    type=bool,
    default=True,
    help="[sub] SELECT symbolic links",
)
SELECTION_PARSER.add_argument(
    "--SELECT-sockets",
    action=argopts.SelectAction,
    type=bool,
    default=True,
    help="[sub] SELECT socket files",
)
SELECTION_PARSER.add_argument(
    "--SELECT-globbing-filelist",
    action=argopts.SelectAction,
    metavar="GLOBS_FILE",
    help="[sub] SELECT files according to glob list in given file",
)
SELECTION_PARSER.add_argument(
    "--SELECT-globbing-filelist-stdin",
    action=argopts.SelectAction,
    type=bool,
    help="[sub] SELECT files according to glob list from standard input",
)
SELECTION_PARSER.add_argument(
    "--SELECT-other-filesystems",
    action=argopts.SelectAction,
    type=bool,
    default=True,
    help="[sub] SELECT files from other file systems than the source one",
)
SELECTION_PARSER.add_argument(
    "--SELECT-regexp",
    action=argopts.SelectAction,
    metavar="REGEXP",
    help="[sub] SELECT files according to regexp pattern",
)
SELECTION_PARSER.add_argument(
    "--SELECT-if-present",
    action=argopts.SelectAction,
    metavar="FILENAME",
    help="[sub] SELECT directory if it contains the given file",
)
SELECTION_PARSER.add_argument(
    "--SELECT-special-files",
    action=argopts.SelectAction,
    type=bool,
    default=True,
    help="[sub] SELECT all device, fifo, socket files, and symbolic links",
)
SELECTION_PARSER.add_argument(
    "--max-file-size",
    action=argopts.SelectAction,
    metavar="SIZE",
    type=int,
    help="[sub] exclude files larger than given size in bytes",
)
SELECTION_PARSER.add_argument(
    "--min-file-size",
    action=argopts.SelectAction,
    metavar="SIZE",
    type=int,
    help="[sub] exclude files smaller than given size in bytes",
)

FILESYSTEM_PARSER = argparse.ArgumentParser(
    add_help=False, description="[parent] options related to file system capabilities"
)
FILESYSTEM_PARSER.add_argument(
    "--acls",
    default=True,
    action=argparse.BooleanOptionalAction,
    help="[sub] handle (or not) Access Control Lists",
)
FILESYSTEM_PARSER.add_argument(
    "--carbonfile",
    default=True,
    action=argparse.BooleanOptionalAction,
    help="[sub] handle (or not) carbon files on MacOS X",
)
FILESYSTEM_PARSER.add_argument(
    "--compare-inode",
    default=True,
    action=argparse.BooleanOptionalAction,
    help="[sub] compare (or not) inodes to decide if hard-linked files have changed",
)
FILESYSTEM_PARSER.add_argument(
    "--eas",
    default=True,
    action=argparse.BooleanOptionalAction,
    help="[sub] handle (or not) Extended Attributes",
)
FILESYSTEM_PARSER.add_argument(
    "--hard-links",
    default=True,
    action=argparse.BooleanOptionalAction,
    help="[sub] preserve (or not) hard links.",
)
FILESYSTEM_PARSER.add_argument(
    "--resource-forks",
    default=True,
    action=argparse.BooleanOptionalAction,
    help="[sub] preserve (or not) resource forks on MacOS X.",
)
FILESYSTEM_PARSER.add_argument(
    "--never-drop-acls",
    action="store_true",
    help="[sub] exit with error instead of dropping acls or acl entries.",
)

CREATION_PARSER = argparse.ArgumentParser(
    add_help=False, description="[parent] options related to creation of directories"
)
CREATION_PARSER.add_argument(
    "--create-full-path",
    action="store_true",
    help="[sub] create full necessary path to backup repository",
)

COMPRESSION_PARSER = argparse.ArgumentParser(
    add_help=False, description="[parent] options related to compression"
)
COMPRESSION_PARSER.add_argument(
    "--compression",
    default=True,
    action=argparse.BooleanOptionalAction,
    help="[sub] compress (or not) snapshot and diff files",
)
COMPRESSION_PARSER.add_argument(
    "--not-compressed-regexp",
    metavar="REGEXP",
    default=DEFAULT_NOT_COMPRESSED_REGEXP,
    help="[sub] regexp to select files not being compressed "
    "(default is '{}')".format(DEFAULT_NOT_COMPRESSED_REGEXP),
)

RESTRICT_PARSER = argparse.ArgumentParser(
    add_help=False,
    description="[parent] options related to restricting access to server",
)
RESTRICT_PARSER.add_argument(
    "--restrict-path",
    type=str,
    metavar="DIR_PATH",
    help="[sub] restrict remote access to given path",
)
RESTRICT_PARSER.add_argument(
    "--restrict-mode",
    type=str,
    choices=["read-write", "read-only", "update-only"],
    default="read-write",
    help="[sub] restriction mode for directory (default is 'read-write')",
)

STATISTICS_PARSER = argparse.ArgumentParser(
    add_help=False, description="[parent] options related to backup statistics"
)
STATISTICS_PARSER.add_argument(
    "--file-statistics",
    default=True,
    action=argparse.BooleanOptionalAction,
    help="[sub] do (or not) generate statistics file during backup",
)
STATISTICS_PARSER.add_argument(
    "--print-statistics",
    default=False,
    action=argparse.BooleanOptionalAction,
    help="[sub] print (or not) statistics after a successful backup",
)

TIMESTAMP_PARSER = argparse.ArgumentParser(
    add_help=False, description="[parent] options related to regress timestamps"
)
TIMESTAMP_PARSER.add_argument(
    "--allow-duplicate-timestamps",
    action="store_true",
    help="[sub] ignore duplicate metadata while checking repository",
)

USER_GROUP_PARSER = argparse.ArgumentParser(
    add_help=False, description="[parent] options related to user and group mapping"
)
USER_GROUP_PARSER.add_argument(
    "--group-mapping-file",
    type=argparse.FileType("r"),
    metavar="MAP_FILE",
    help="[sub] map groups according to file",
)
USER_GROUP_PARSER.add_argument(
    "--preserve-numerical-ids",
    action="store_true",
    help="[sub] preserve user and group IDs instead of names",
)
USER_GROUP_PARSER.add_argument(
    "--user-mapping-file",
    type=argparse.FileType("r"),
    metavar="MAP_FILE",
    help="[sub] map users according to file",
)

GENERIC_PARSERS = [COMMON_PARSER]


class BaseAction:
    """
    Base rdiff-backup Action, and is to be used as base class for all these actions.
    """

    # name of the action as a string
    name = None

    # type of action for security purposes, one of backup, restore, validate
    # or server (or None if client/server isn't relevant)
    security = None

    # version of the action
    __version__ = "0.0.0"

    # list of parent parsers as defined above
    parent_parsers = []

    # connection status
    conn_status = consts.RET_CODE_OK

    @classmethod
    def get_name(cls):
        """
        Return the name of the Action class.

        Children classes only need to define the class member 'name'.
        """
        return cls.name

    @classmethod
    def get_desc(cls):
        """
        Return the human readable name of the Action class.

        Children classes only need to define the class member 'name',
        this function returns the capitalized version to satisfy the plugin
        interface.
        """
        return cls.name.capitalize()

    @classmethod
    def get_version(cls):
        """
        Return the version of the Action class.

        Children classes only need to define the class member '__version__'.
        """
        return cls.__version__

    @classmethod
    def get_security_class(cls):
        """
        Return the security class of the Action class.

        Children classes only need to define the class member 'security',
        with one of the values 'backup', 'restore', 'server' or 'validate'.
        """
        return cls.security

    @classmethod
    def add_action_subparser(cls, sub_handler):
        """
        Define a parser for the sub-options of the action.

        Given a subparsers handle as returned by argparse.add_subparsers,
        creates the subparser corresponding to the current Action class
        (as inherited).
        Most Action classes will need to extend this function with their
        own subparsers. Though they can use the class member
        'parent_parsers' to list which parent parsers defined in this module
        they want to inherit from, so that they only need to add the very
        specific options to this subparser.
        Returns the computed subparser.
        """
        subparser = sub_handler.add_parser(
            cls.name, parents=cls.parent_parsers, description=cls.__doc__
        )
        subparser.set_defaults(action=cls.name)

        return subparser

    @classmethod
    def _get_subparsers(cls, parser, sub_dest, *sub_names):
        """
        Helper for action plug-ins needing themselves sub-actions.

        This method can be used to add 2nd level subparsers to the action
        subparser (named here parser). sub_dest would typically be the name
        of the action, and sub_names are the names for the sub-subparsers.
        Returns the computed subparsers as dictionary with the sub_names as
        keys, so that arguments can be added to those subparsers as values.
        """
        if sys.version_info.major >= 3 and sys.version_info.minor >= 7:
            sub_handler = parser.add_subparsers(
                title="possible {dest}s".format(dest=sub_dest),
                required=True,
                dest=sub_dest,
            )
        else:  # required didn't exist in Python 3.6
            sub_handler = parser.add_subparsers(
                title="possible {dest}s".format(dest=sub_dest), dest=sub_dest
            )

        subparsers = {}
        for sub_name in sub_names:
            subparsers[sub_name] = sub_handler.add_parser(sub_name)
            subparsers[sub_name].set_defaults(**{sub_dest: sub_name})
        return subparsers

    def __init__(self, values):
        """
        Instantiate an action plug-in class.

        values is a Namespace as returned by argparse.
        """
        self.values = values
        if self.values["remote_schema"]:
            self.remote_schema = os.fsencode(self.values["remote_schema"])
        else:
            self.remote_schema = None
        if self.values["remote_tempdir"]:
            self.remote_tempdir = os.fsencode(self.values["remote_tempdir"])
        else:
            self.remote_tempdir = None

    def __enter__(self):
        """
        Context manager interface to enter with-as context.

        Returns self to be used 'as' value.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager interface to exit with-as context.

        Returns False to propagate potential exception, else True.
        """
        log.Log("Cleaning up", log.INFO)
        if hasattr(self, "repo"):
            self.repo.exit()
        if self.security != "server":
            SetConnections.CloseConnections()

        return False

    def debug_values(self, explicit=True):
        """
        Debug output method
        """
        print(
            yaml.safe_dump(self.values, explicit_start=explicit, explicit_end=explicit)
        )

    def pre_check(self):
        """
        Validate that the values given look correct.

        This method isn't meant to try to access any file system and even less
        a remote location, it is really only meant to validate the values
        beyond what argparse can do.
        Return 0 if everything looked good, else an error code.

        Try to check everything before returning and not force the user to fix
        their entries step by step.
        """
        ret_code = 0
        if self.values["action"] != self.name:
            log.Log(
                "Action value '{av}' doesn't fit name of action class "
                "'{ac}'.".format(av=self.values["action"], ac=self.name),
                log.ERROR,
            )
            ret_code |= consts.RET_CODE_ERR
        if self.values["tempdir"] and not os.path.isdir(self.values["tempdir"]):
            log.Log(
                "Temporary directory '{td}' doesn't exist.".format(
                    td=self.values["tempdir"]
                ),
                log.ERROR,
            )
            ret_code |= consts.RET_CODE_ERR
        if (
            self.security is None
            and "locations" in self.values
            and self.values["locations"]
        ):
            log.Log(
                "Action '{ac}' must have a security class to handle "
                "locations".format(ac=self.name),
                log.ERROR,
            )
            ret_code |= consts.RET_CODE_ERR
        return ret_code

    def connect(self):
        """
        Connect to potentially provided locations arguments, remote or local.

        Returns self, to be used as context manager.
        """

        if self.values.get("locations"):
            # TODO encapsulate the following lines into one
            # connections/connections_mgr construct, so that the action doesn't
            # need to care about cmdpairs and Security (which would become a
            # feature of the connection).
            cmdpairs = SetConnections.get_cmd_pairs(
                self.values["locations"],
                remote_schema=self.remote_schema,
                ssh_compression=self.values["ssh_compression"],
                remote_tempdir=self.remote_tempdir,
                term_verbosity=log.Log.term_verbosity,
            )
            Security.initialize(self.get_security_class(), cmdpairs)
            self.connected_locations = list(
                map(SetConnections.get_connected_rpath, cmdpairs)
            )

            # if a connection is None, it's an error
            for conn, loc in zip(self.connected_locations, self.values["locations"]):
                if conn is None:
                    log.Log(
                        "Location '{lo}' couldn't be connected.".format(lo=loc),
                        log.ERROR,
                    )
                    self.conn_status = consts.RET_CODE_ERR
        else:
            Security.initialize(self.get_security_class(), [])
            self.connected_locations = []

        return self

    def check(self):
        """
        Checks that all connections are looking fine.

        Whatever can be checked without changing anything to the environment.
        Return 0 if everything looked good, else an error code.
        """
        return self.conn_status

    def setup(self):
        """
        Prepare the execution of the action.

        Return 0 if everything looked good, else an error code.
        """
        # we can define "now" as being the current time,
        # unless the user defined a fixed a current time.
        Time.set_current_time(self.values["current_time"])

        if self.values["tempdir"]:
            # At least until Python 3.10, the module tempfile doesn't work
            # properly,
            # especially under Windows, if tempdir is stored as bytes.
            # See https://github.com/python/cpython/pull/20442
            tempfile.tempdir = self.values["tempdir"]
        # Set default change ownership flag, umask, relay regexps
        os.umask(0o77)
        for conn in specifics.connections:
            conn.robust.install_signal_handlers()

        return consts.RET_CODE_OK

    def run(self):
        """
        Execute the given action.

        Return 0 if everything looked good, else an error code.
        """
        return consts.RET_CODE_OK

    def is_connection_ok(self):
        """
        Return True if connection is OK, False else
        """
        return not self.conn_status & consts.RET_CODE_ERR

    def _operate_regress(self, try_regress=True, noticeable=False, force=False):
        """
        Check the given repository and regress it if necessary

        Parameter force enforces a regress even if the repo doesn't need it.
        """
        if noticeable:
            regress_verbosity = log.NOTE
        else:
            regress_verbosity = log.INFO

        if self.repo.needs_regress():
            if not try_regress:
                return consts.RET_CODE_ERR
            log.Log(
                "Previous backup seems to have failed, regressing " "destination now",
                log.WARNING,
            )
            return self.repo.regress() | consts.RET_CODE_WARN
        elif force:
            if self.repo.force_regress():
                log.Log(
                    "Given repository doesn't need to be regressed, "
                    "but enforcing regression",
                    log.WARNING,
                )
                return self.repo.regress()
            else:
                log.Log(
                    "Given repository doesn't need and can't be "
                    "regressed even if forced",
                    log.WARNING,
                )
                return consts.RET_CODE_WARN
        else:
            log.Log("Given repository doesn't need to be regressed", regress_verbosity)
            return consts.RET_CODE_OK

    @classmethod
    def get_runtime_info(cls, parsed=None):
        """
        Return a structure containing all relevant runtime information about
        the executable, Python and the operating system.
        Beware that additional information might be added at any time.
        """
        return {
            "exec": {
                "version": specifics.version,
                "api_version": specifics.api_version,
                "argv": sys.argv,
                "parsed": parsed,
            },
            "python": {
                "name": sys.implementation.name,
                "executable": sys.executable,
                "version": platform.python_version(),
            },
            "system": {
                "platform": platform.platform(),
                "fs_encoding": sys.getfilesystemencoding(),
            },
        }


def get_plugin_class():
    """
    Pre-defined function returning the Action class of the current module.

    This function is called by the Actions manager after it has identified
    a fitting action plug-in module.
    """
    return BaseAction
