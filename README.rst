pymodaq_plugins_template
########################

.. the following must be adapted to your developed package, links to pypi, github  description...

.. image:: https://img.shields.io/pypi/v/pymodaq_plugins_template.svg
   :target: https://pypi.org/project/pymodaq_plugins_template/
   :alt: Latest Version

.. image:: https://readthedocs.org/projects/pymodaq/badge/?version=latest
   :target: https://pymodaq.readthedocs.io/en/stable/?badge=latest
   :alt: Documentation Status

.. image:: https://github.com/PyMoDAQ/pymodaq_plugins_template/workflows/Upload%20Python%20Package/badge.svg
   :target: https://github.com/PyMoDAQ/pymodaq_plugins_template
   :alt: Publication Status

.. image:: https://github.com/PyMoDAQ/pymodaq_plugins_template/actions/workflows/Test.yml/badge.svg
    :target: https://github.com/PyMoDAQ/pymodaq_plugins_template/actions/workflows/Test.yml


Use this template to create a repository on your account and start the development of your own PyMoDAQ plugin!


Authors
=======

* Matthieu Guer  (m.guer@hw.ac.uk)



Instruments
===========

Below is the list of instruments included in this plugin

Actuators
+++++++++

* **MRM**: control of MRM-002 motorized rotation mount from Sinoptix / Xinuo photonics


Installation instructions
=========================

Tested on:
* PyMoDAQ 5.1.x
* Windows 11

* Use the configuration tool from Xinuo the first time to configure the motor. 
* Use the controller tool from Xinuo to figure out the COM port corresponding to the motor.
* You don't need any additionnal programm or dll to use this plugin.
