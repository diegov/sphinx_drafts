=============
Sphinx Drafts
=============

A `sphinx
<http://sphinx.pocoo.org/>`_ extension to add draft warnings to sphinx documents. 

Installation
############

.. code-block:: sh

   sudo python setup.py install

Usage
#####

The extension introduces a new directive, called *draft*, taking one argument which can be either 'yes' or 'check'. 

Examples
==========

.. code-block:: rst

   .. draft:: yes

or

.. code-block:: rst

   .. draft:: check

Behaviour
=========

When the argument is 'yes', the document will be considered a draft, and a warning will be shown. 

When the argument is 'check', the document will be considered a draft, and a warning will be shown, if at least one of these conditions is true:

* There is another draft directive in the same document with its argument set to 'yes'
* The document links to another document that is considered a draft

If neither of these conditions are met the directive will have no effect on the document. 

The check logic is applied recursively (stopping on circular references.)

You can add the directive anywhere you like in the document, and as many times as you like. 

Configuration
=============

There aren't any settings currently, so all you need is for the extension module to be properly installed (or in the PYTHONPATH), and you need to add extension to the sphinx configuration. To do that, add 'sphinx_drafts' to the list of extensions in the *conf.py* file of your sphinx project. Eg.:

.. code-block:: python

   # Add any Sphinx extension module names here, as strings. They can be extensions
   # coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
   extensions = ['sphinx_drafts', 'sphinx.ext.graphviz', 'sphinx.ext.autodoc']
 
TODO
#####

* Add configuration options for warning text
* Fix doctree absolute path issues
* Internationalisation
