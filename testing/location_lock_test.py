"""
Test the handling of locking with api version >= 201
"""

import os
import shutil
import unittest

import commontest as comtst

from rdiff_backup import rpath
from rdiffbackup.locations import _repo_shadow
from rdiffbackup.singletons import specifics

TEST_BASE_DIR = comtst.get_test_base_dir(__file__)


class LocationLockTest(unittest.TestCase):
    """
    Test that rdiff-backup properly handles locking
    """

    def setUp(self):
        self.base_dir = os.path.join(TEST_BASE_DIR, b"location_lock")
        self.base_rp = rpath.RPath(specifics.local_connection, self.base_dir)
        self.lockfile = self.base_rp.append("lock")
        comtst.re_init_rpath_dir(self.base_rp)
        self.success = False

    def test_location_lock_exclusive(self):
        """
        verify that exclusive locking mechanisms do work properly
        """
        self.assertFalse(
            _repo_shadow.RepoShadow._is_locked(self.lockfile, exclusive=True)
        )
        self.assertTrue(_repo_shadow.RepoShadow._lock(self.lockfile, exclusive=True))
        # we tweak another process
        fd1 = _repo_shadow.RepoShadow._lockfd
        _repo_shadow.RepoShadow._lockfd = None
        self.assertTrue(
            _repo_shadow.RepoShadow._is_locked(self.lockfile, exclusive=False)
        )
        self.assertTrue(
            _repo_shadow.RepoShadow._is_locked(self.lockfile, exclusive=True)
        )
        self.assertFalse(_repo_shadow.RepoShadow._lock(self.lockfile, exclusive=False))
        self.assertIsNone(_repo_shadow.RepoShadow._lockfd)
        _repo_shadow.RepoShadow._lockfd = fd1
        self.assertIsNone(
            _repo_shadow.RepoShadow._unlock(self.lockfile, exclusive=True)
        )
        self.assertIsNone(_repo_shadow.RepoShadow._lockfd)
        self.assertFalse(
            _repo_shadow.RepoShadow._is_locked(self.lockfile, exclusive=False)
        )
        self.success = True

    def test_location_lock_shared(self):
        """
        verify that shared locking (read-only) is possible
        """
        # make sure the lockfile doesn't exist
        self.lockfile.setdata()
        if self.lockfile.lstat():
            self.lockfile.delete()
        self.assertFalse(
            _repo_shadow.RepoShadow._is_locked(self.lockfile, exclusive=False)
        )
        self.lockfile.touch()
        self.assertTrue(_repo_shadow.RepoShadow._lock(self.lockfile, exclusive=False))
        # we tweak another process
        fd1 = _repo_shadow.RepoShadow._lockfd
        _repo_shadow.RepoShadow._lockfd = None
        self.assertFalse(
            _repo_shadow.RepoShadow._is_locked(self.lockfile, exclusive=False)
        )
        self.assertTrue(
            _repo_shadow.RepoShadow._is_locked(self.lockfile, exclusive=True)
        )
        self.assertFalse(_repo_shadow.RepoShadow._lock(self.lockfile, exclusive=True))
        self.assertIsNone(_repo_shadow.RepoShadow._lockfd)
        self.assertTrue(_repo_shadow.RepoShadow._lock(self.lockfile, exclusive=False))
        self.assertIsNone(
            _repo_shadow.RepoShadow._unlock(self.lockfile, exclusive=False)
        )
        _repo_shadow.RepoShadow._lockfd = fd1
        self.assertIsNone(
            _repo_shadow.RepoShadow._unlock(self.lockfile, exclusive=False)
        )
        self.assertIsNone(_repo_shadow.RepoShadow._lockfd)
        self.assertFalse(
            _repo_shadow.RepoShadow._is_locked(self.lockfile, exclusive=False)
        )
        self.success = True

    def tearDown(self):
        # we clean-up only if the test was successful
        if self.success:
            shutil.rmtree(self.base_dir)


if __name__ == "__main__":
    unittest.main()
