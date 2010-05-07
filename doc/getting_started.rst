##################################
  Getting Started
##################################

:Release: |version|
:Date: |today|

Installation
------------

From debian package
~~~~~~~~~~~~~~~~~~~
Add the following to your /etc/apt/sources.list::

 deb http://mirrors.digg.com/digg digg-public-lenny main contrib non-free

Update the index and install clusto::

 # aptitude update
 # aptitude install clusto

Building an rpm package
~~~~~~~~~~~~~~~~~~~~~~~
You may need to install rpmdevtools beforehand, or run the rpmbuild as root::

 $ cd rpm/
 $ ./make_tarball.sh
 $ rpmbuild -ta clusto-$VERSION.tar.gz

From source
~~~~~~~~~~~
::

 $ git clone git://github.com/digg/clusto.git
 $ cd clusto
 $ python setup.py build

As root::

 # python setup.py install
 # mkdir /etc/clusto /var/lib/clusto
 # cp conf/* /etc/clusto/
 # cp contrib/* /var/lib/clusto/

You may need to install additional python libraries for certain features of clusto to function properly.

- SQLAlchemy: http://www.sqlalchemy.org/
- setuptools: http://peak.telecommunity.com/
- scapy: http://www.secdev.org/projects/scapy/doc/
- ipython: http://ipython.scipy.org/moin/
- IPy: http://c0re.23.nu/c0de/IPy/
- MySQLdb: http://sourceforge.net/projects/mysql-python/
- libvirt: http://libvirt.org/
- simplejson: http://code.google.com/p/simplejson/

Configuration
-------------

Clusto is built on top of SQLAlchemy and therefore should work with any backend database available to that library. For the same of simplicity, the following documentation assumes you are using a MySQL backend.

Create a MySQL database
~~~~~~~~~~~~~~~~~~~~~~~
::

 # aptitude install mysql-server
 # mysql -u root
 mysql> CREATE DATABASE clusto;
 mysql> GRANT ALL PRIVILEGES ON clusto.* TO 'clustouser'@'localhost' IDENTIFIED BY 'clustopass';
 mysql> FLUSH PRIVILEGES;

/etc/clusto/clusto.conf
~~~~~~~~~~~~~~~~~~~~~~~
::

 [clusto]
 dsn = mysql://clustouser:clustopass@127.0.0.1/clusto

Creating tables
~~~~~~~~~~~~~~~
Using clusto-shell::

 init_clusto()
