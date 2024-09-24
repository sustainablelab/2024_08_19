#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
"""Unit test FRect

Run tests
---------
- Vim shortcut (from this buffer): ;<Space>
- Vim shortcut (from any buffer in libs folder): ;mt -- See ./libs/Makefile
- Vim shortcut (from any buffer in parent folder): ;mt -- See ./Makefile
- Cmdline (from this folder): python -m unittest
- Cmdline (from parent folder): python -m unittest discover -s libs
"""

from frect import FRect
import unittest


class TestFRect_attributes(unittest.TestCase):
    def setUp(self):
        self.rect = FRect((10,10), (1,1))
    def test_center(self):
        self.assertEqual(self.rect.center, (10,10))
    def test_topleft(self):
        self.assertEqual(self.rect.topleft, (9.5,10.5))
    def test_topright(self):
        self.assertEqual(self.rect.topright, (10.5,10.5))
    def test_bottomright(self):
        self.assertEqual(self.rect.bottomright, (10.5,9.5))
    def test_bottomleft(self):
        self.assertEqual(self.rect.bottomleft, (9.5,9.5))

class TestFRect_move_by_assignment(unittest.TestCase):
    def setUp(self):
        self.rect = FRect((10,10), (1,1))
        # Check setup
        self.assertEqual(self.rect.topleft, (9.5,10.5))
    def test_move_center_to_topleft(self):
        # Move by assignment to FRect.center
        self.rect.center = self.rect.topleft
        # Test that this move works
        self.assertEqual(self.rect.center, (9.5,10.5))
        self.assertEqual(self.rect.topleft, (9,11))
    def test_move_topleft_to_center(self):
        # Move by assignment to FRect.topleft
        self.assertEqual(self.rect.center, (10,10))
        self.rect.topleft = self.rect.center
        # Test that this move works
        self.assertEqual(self.rect.topleft, (10,10))
        self.assertEqual(self.rect.center, (10.5,9.5))
    def test_move_center_to_topright(self):
        # Move by assignment to FRect.center
        self.rect.center = self.rect.topright
        # Test that this move works
        self.assertEqual(self.rect.center, (10.5,10.5))
        self.assertEqual(self.rect.topright, (11,11))
    def test_move_topright_to_center(self):
        # Move by assignment to FRect.topright
        self.rect.topright = self.rect.center
        # Test that this move works
        self.assertEqual(self.rect.topright, (10,10))
        self.assertEqual(self.rect.center, (9.5,9.5))
    def test_move_center_to_bottomright(self):
        # Move by assignment to FRect.center
        self.rect.center = self.rect.bottomright
        # Test that this move works
        self.assertEqual(self.rect.center, (10.5,9.5))
        self.assertEqual(self.rect.bottomright, (11,9))
    def test_move_bottomright_to_center(self):
        # Move by assignment to FRect.bottomright
        self.rect.bottomright = self.rect.center
        # Test that this move works
        self.assertEqual(self.rect.bottomright, (10,10))
        self.assertEqual(self.rect.center, (9.5,10.5))
    def test_move_center_to_bottomleft(self):
        # Move by assignment to FRect.center
        self.rect.center = self.rect.bottomleft
        # Test that this move works
        self.assertEqual(self.rect.center, (9.5,9.5))
        self.assertEqual(self.rect.bottomleft, (9,9))
    def test_move_bottomleft_to_center(self):
        # Move by assignment to FRect.bottomleft
        self.rect.bottomleft = self.rect.center
        # Test that this move works
        self.assertEqual(self.rect.bottomleft, (10,10))
        self.assertEqual(self.rect.center, (10.5,10.5))

if __name__ == '__main__':
    unittest.main()
