#!/usr/bin/python

import re
import os
import sys
import abc
import json
from configparser import ConfigParser

import xmltodict

from packages import get_files

class FactorParserError(Exception):
    pass

class ParserNotFound(FactorParserError):
    pass



class RawConfigBase(abc.ABC):
    """
    Base class for config parsers.

    This class puts a basic frame to unify several standard ans custom parsers.
    Initialized by config file content and implements a mandatory method `parse`
    returning structured data.

    """

    @property
    @abc.abstractmethod
    def name(self):
        """ Mandatory and unique name of parser """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def extensions(self):
        """ List of extensions """
        raise NotImplementedError


    def __init__(self, text, delimiter="=", comment="#"):

        self.comment = comment
        self.delimiter = delimiter
        self.text = text
        self.uncommented = self.uncomment(text)
        self.lines = [ln.strip() for ln in self.uncommented.split("\n")]

    def uncomment(self, text):

        return re.sub(re.compile(self.comment + r".*?\n"),"" , text)

    @staticmethod
    def clean_blank(text):
        return re.sub(re.compile(r"[\r\n]+"),"" , text)

    @abc.abstractmethod
    def parse(self):
        raise NotImplementedError



class ConfJavaProperties(RawConfigBase):
    name = "java.properties"
    extensions = ["properties"]
    def parse(self):
        unpacked = (line.split(self.delimiter) for line in self.lines if self.delimiter in line)
        return {k.strip(): v.strip() for (k, v) in unpacked}


class ConfIni(RawConfigBase):
    name = "conf.ini"
    extensions = ["conf", "ini"]
    def parse(self):
        result = {}
        config = ConfigParser(strict=False, interpolation=None)
        config.read_string(self.text)
        return { s: dict(config.items(s)) for s in config.sections() }


class ConfJson(RawConfigBase):
    name = "json"
    extensions = ["json"]
    def parse(self):
        return json.loads(self.text)


class ConfXml(RawConfigBase):
    name = "xml"
    extensions = ["xml"]
    def parse(self):
        return xmltodict.parse(self.text)


# Stores all subclasses of `RawConfigBase` class in this module
parsers = {c.name: c for c in sys.modules[__name__].__dict__.values() if isinstance(c, type) and issubclass(c, RawConfigBase)}


def parse(text, name):
    # print(parsers)
    try:
        parser_class = parsers[name]
    except KeyError:
        raise ParserNotFound(f"Parser <{name}> not defined")
    return parser_class(text).parse()

def test(path, parser_name):
    with open(path) as f:
        result = parse(f.read(), parser_name)
        print(json.dumps(result))

# test("/etc/tpm2-tss/fapi-profiles/P_ECCP256SHA256.json", "json")

include = [r"^/etc*"]
for name, paths in get_files(None, include):
    for path in paths:
        _, ext = os.path.splitext(path)
        if ext.startswith("."):
            ext = ext[1:]
            if ext in parsers:
                print(name, path, ext)

