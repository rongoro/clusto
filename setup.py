#!/usr/bin/env python
import glob
import os
import sys

from setuptools import setup, find_packages

srcdir = os.path.join(os.path.dirname(sys.argv[0]), 'src')

setup(name = "clusto",
      version = "0.5.30",
      packages = find_packages('src'),
      author = "Ron Gorodetzky",
      author_email = "ron@digg.com",
      description = "Clusto, cluster management and inventory system",
      install_requires = ['sqlalchemy>=0.5.0',
                          'IPython',
                          'PyYAML',
                          'python-memcached',
                          'mako',
                          'boto'
                          ],
      zip_safe=False,
      package_dir = {'':'src'},
      #scripts=glob.glob(os.path.join(srcdir, 'scripts', 'clusto')),
      scripts=[os.path.join(srcdir, 'scripts', 'clusto'),
               os.path.join(srcdir, 'scripts', 'clusto-allocate'),
               os.path.join(srcdir, 'scripts', 'clusto-attr'),
               os.path.join(srcdir, 'scripts', 'clusto-console'),
               os.path.join(srcdir, 'scripts', 'clusto-dhcpd'),
               os.path.join(srcdir, 'scripts', 'clusto-fai'),
               os.path.join(srcdir, 'scripts', 'clusto-kvm'),
               os.path.join(srcdir, 'scripts', 'clusto-httpd'),
               os.path.join(srcdir, 'scripts', 'clusto-info'),
               os.path.join(srcdir, 'scripts', 'clusto-list-pool'),
               os.path.join(srcdir, 'scripts', 'clusto-pool'),
               os.path.join(srcdir, 'scripts', 'clusto-puppet-node'),
               os.path.join(srcdir, 'scripts', 'clusto-puppet-node2'),
               os.path.join(srcdir, 'scripts', 'clusto-hadoop-node'),
               os.path.join(srcdir, 'scripts', 'clusto-reboot'),
               os.path.join(srcdir, 'scripts', 'clusto-shell'),
               os.path.join(srcdir, 'scripts', 'clusto-snmptrapd'),
               os.path.join(srcdir, 'scripts', 'clusto-tree'),
               os.path.join(srcdir, 'scripts', 'clusto-update-info'),
               os.path.join(srcdir, 'scripts', 'clusto-vm'),
               os.path.join(srcdir, 'scripts', 'clusto-deallocate'),
               os.path.join(srcdir, 'scripts', 'clusto-update-db'),
               ],
      test_suite = "clusto.test.alltests.gettests",
      dependency_links=['http://www.secdev.org/projects/scapy/']
      )


