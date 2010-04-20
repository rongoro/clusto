##################################
  Setup
##################################

:Release: |version|
:Date: |today|

Installation
------------

From debian package
~~~~~~~~~~~~~~~~~~~
As root::

 # aptitude install clusto

From source
~~~~~~~~~~~
::

 $ git clone /path/to/clusto.git
 $ cd clusto
 $ python setup.py build

As root::

 # python setup.py install

Configuration
-------------

Create a MySQL database
~~~~~~~~~~~~~~~~~~~~~~~
::

 # aptitude install mysql-server
 # mysql -u root
 mysql> CREATE DATABASE clusto;
 mysql> GRANT ALL PRIVILEGES ON clusto.* TO 'clustouser'@'localhost' IDENTIFIED BY 'clustopass';
 mysql> FLUSH PRIVILEGES;

clusto.conf
~~~~~~~~~~~
::

 [clusto]
 dsn = mysql://username:password@127.0.0.1/clusto
