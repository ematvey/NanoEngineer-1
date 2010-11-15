NanoInventor
===============

Project for further development of NanoEngineer-1.

Goals
----------

 * Support actual state of the original project.
 * Bring to the NanoEngineer-1 GPU acceleration.

Builds
---------

 * OS X with macports
 * OS X with native frameworks and fresh eggs

Native OS X build
----------

1. SIP
Builds amd64 binaries.
<code>
python configure.py
make
sudo make install
</code>

2. PyQT4
Builds universal binary (only on 10.6 and Qt4.7)
<code>
python configure.py --confirm-license -e QtCore -e QtGui -e QtOpenGL
make
sudo make install
</code>

3. ctypes
already exists on python 2.5

4. PyOpenGL
not necessary easy_install

5. Numeric
<code>
patch -p0 < ../archives/patch-ranf.c
python setup.py build
sudo python setup.py install
</code>
Contacts
----------
Please contact us at: [nanoinv.ru](http://nanoinv.ru)

Original project: [nanoengineer-1.com](http://www.nanoengineer-1.com/content)
