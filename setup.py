#!/usr/bin/env python
import os
import re
import shlex
import sys
from distutils.dep_util import newer
from shutil import which

import jinja2
import setuptools

PO_FILES = 'po/*/messages.po'

class CleanCommand(setuptools.Command):
    """
    Custom clean command to tidy up the project root, because even
        python setup.py clean --all
    doesn't remove build/dist and egg-info directories, which can and have caused
    install problems in the past.
    """
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        os.system('rm -vrf ./build ./dist ./*.pyc ./*.tgz ./*.egg-info')

if sys.version_info < (3, 6, 0):
    sys.exit("Python 3.6.0 is the minimum required version")

PROJECT_ROOT = os.path.dirname(__file__)

with open(os.path.join(PROJECT_ROOT, "README.md"), "r", encoding="utf8") as file:
    doc = {}
    lines = []
    title = "Summary"
    Package_name = ""
    for line in file:
        line = line.strip()
        if line != '':
            if line.startswith("##"):
                if len(lines):
                    if title not in doc:
                        doc[title] = lines
                    else:
                        doc[title] = doc[title] + lines
                title = line.lstrip("#").strip()
                lines = []
            else:
                if not line.startswith('#'):
                    lines.append(line)
                if Package_name == "" and line.startswith('# '):
                    Package_name = line.lstrip("#").strip()
    if len(lines):
        if title not in doc:
            doc[title] = lines
        else:
            doc[title] = doc[title] + lines
    Summary = doc['Summary'][0]
    Long_desc = '\n'.join(doc['Intro'])
    Website = doc['Website'][0].strip()
    Copyright = doc['Copyright'][0].strip()
    s = re.search('^([^\<]*)\<([^\>]*)\>$', doc['Authors'][0])
    if s:
        Author = s.group(1).strip()
        Mail = s.group(2).strip()
        Mail = Mail.replace(" dot ", ".").replace(" at ", "@").replace(" ", "")
    License = doc['License'][0]

_version_re = re.compile(r"VERSION\s*=\s*[\'\"](?P<version>.*)[\'\"]")
with open(os.path.join(PROJECT_ROOT, 'pid_tune', '__init__.py'), "r", encoding="utf8") as f:
    match = _version_re.search(f.read())
    Version = match.group("version") if match is not None else '"unknown"'

def generate_translation_files():
    lang_files = []

    langs = (os.path.splitext(l)[0]
             for l in os.listdir('po')
             if l.endswith('po') and l != "messages.po")

    for lang in langs:
        pofile = os.path.join("po", "%s.po" % lang)
        modir = os.path.join("bootinfo", "share", "locale", lang, "LC_MESSAGES")
        mofile = os.path.join(modir, "bootinfo.mo")
        if not os.path.exists(modir):
            os.makedirs(modir)

        lang_files.append(('share/locale/%s/LC_MESSAGES' % lang, [mofile]))

        if newer(pofile, mofile):
            print("Generating %s" % mofile)
            os.system("msgfmt %s -o %s" % (pofile, mofile))

    return lang_files

def generate_doc_file():
    # apply templating to all documentation files
    macros = {
        'package': Package_name,
        'version': Version,
        'man_section': '1',
        'short_desc': Summary,
        'long_desc': Long_desc,
        'website': Website,
        'copyright': Copyright,
        'author': Author,
        'mail': Mail,
        'doc_title' : Package_name.strip() + ' Documentation',
    }

    for root, dirs, files in os.walk("docs"):
        for file in files:
            if file.endswith(".jinja"):
                with open(os.path.join(root, file), 'r') as file_:
                    template = jinja2.Template(file_.read())
                    string = template.render(macros)
                    with open(os.path.join(root, os.path.splitext(file)[0]), "w") as ofile_:
                        ofile_.write(string)
    if not which("asciidoctor"):
        print("asciidoctor could not be located")
        raise (SystemExit)
    for root, dirs, files in os.walk("doc"):
        for file in files:
            if file.endswith(".man.adoc"):
                os.subprocess.run(shlex.split("asciidoctor -b manpage %s" % os.path.join(root, file)))

data_files= [
] + generate_translation_files()

setuptools.setup(
    name=Package_name,
    version=Version,
    python_requires=">=3.6.0",
    description=Summary,
    long_description=Long_desc,
    long_description_content_type="text/markdown",
    platforms = ['Linux'],
    url=Website,
    author=Author,
    author_email=Mail,
    license=License,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: System :: Systems Administration",
        "Topic :: System :: Operating System",
        "Topic :: Utilities"
    ],
    message_extractors = {
        'pid_tune' : [
            ('**.py', 'python', None)
        ]
    },
    entry_points={
        'console_scripts': [
            'pid_tune = pid_tune.pid_tune:main'
        ]
    },
    packages=setuptools.find_packages(),
    data_files = data_files,
    include_package_data=True,
)

