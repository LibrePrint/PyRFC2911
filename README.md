# PyRFC2911

PyRFC2911 is a python library that can be used for DIY printers.

# Contribution

Get-Jobs function currently does not work, contribution welcome. But it isn't commonly used so it should be fine.

# Installation

Currently only available through git because PyRFC2911 is in alpha.

`pip install git+https://github.com/lizard-64/PyRFC2911`

# How to use

The printer creator, creates 2 classes that inherit 

`rfc2911.adapter.BaseAdapterClass`

and

`rfc2911.adapter.BaseBrandingClass`

And reimplement the functions as described. Then they create a Postscript Printer Definition class, which can be used for CUPS. These classes are used to control the printing device and report its branding.

Detailed documentation coming soon.