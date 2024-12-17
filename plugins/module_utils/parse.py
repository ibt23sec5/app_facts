#!/usr/bin/python

import re
import os
import sys
import abc
import xml
import json
import glob
import configparser

import yaml
import xmltodict

from packages import get_files

class FactorParserError(Exception):
    pass


class ParserSyntaxError(FactorParserError):
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
        try:
            unpacked = (line.split(self.delimiter) for line in self.lines if self.delimiter in line)
            return {k.strip(): v.strip() for (k, v) in unpacked}
        except Exception as exc: # TODO - too general
            raise ParserSyntaxError(exc)

class ConfIni(RawConfigBase):
    name = "conf.ini"
    extensions = ["conf", "ini"]
    def parse(self):
        result = {}
        config = configparser.ConfigParser(strict=False, interpolation=None)
        try:
            config.read_string(self.text)
            return { s: dict(config.items(s)) for s in config.sections() }
        except configparser.Error as exc:
            raise ParserSyntaxError(exc)


class ConfJson(RawConfigBase):
    name = "json"
    extensions = ["json"]
    def parse(self):
        try:
            return json.loads(self.text)
        except json.JSONDecodeError as exc:
            raise ParserSyntaxError(exc)

class ConfXml(RawConfigBase):
    name = "xml"
    extensions = ["xml"]
    def parse(self):
        try:
            return xmltodict.parse(self.text)
        except xml.parsers.expat.ExpatError as exc:
            raise ParserSyntaxError(exc)

class ConfYaml(RawConfigBase):
    name = "yaml"
    extensions = ["yml", "yaml"]
    def parse(self):
        try:
            return yaml.safe_load(self.text)
        except yaml.parser.ParserError as exc:
            raise ParserSyntaxError(exc)

# Stores all subclasses of `RawConfigBase` class in this module
parsers = {c.name: c for c in sys.modules[__name__].__dict__.values() if isinstance(c, type) and issubclass(c, RawConfigBase) and c.__name__ != "RawConfigBase"}

def get_parser_by_ext(ext):
    for parser in parsers.values():
        if ext.lower() in parser.extensions:
            return parser

def get_parser_from_hints(path, hints):
    for pattern, name in hints.items():
        if path in glob.glob(pattern):
            try:
                parser_class = parsers[name]
            except KeyError:
                raise ParserNotFound(f"Parser <{name}> not defined")
            return parser_class


def parse(text, name):
    try:
        parser_class = parsers[name]
    except KeyError:
        raise ParserNotFound(f"Parser <{name}> not defined")
    return parser_class(text).parse()



# def test(path, parser_name):
#     with open(path) as f:
#         result = parse(f.read(), parser_name)
#         print(json.dumps(result))
#
# # test("/etc/tpm2-tss/fapi-profiles/P_ECCP256SHA256.json", "json")

hints = {"/etc/abrt/plugins/*": "java.properties",
         "/etc/yum.repos.d/*.repo": "conf.ini",
         "/etc/xdg/autostart/*.desktop": "conf.ini",
         "/etc/systemd/system/*.target": "conf.ini",
         # "/etc/systemd/system/*.wants": "conf.ini",
         "/etc/systemd/system/*.service": "conf.ini",
         }

errors = []

def log(text):
    errors.append(text)


include = [r"^/etc*"]
exclude = [r"/etc/bash_completion.d/*"]
result = {}
for name, paths in get_files(None, include, exclude):
    for path in paths:
        if not os.access(path, os.R_OK):
            log(f"Unable read path<{path}>")
            continue
        # Try to determine the parser by pre-defined hint
        parser = get_parser_from_hints(path, hints)
        if not parser:
            # Try to determine the parser by extension
            _, ext = os.path.splitext(path)
            if ext.startswith("."):
                ext = ext[1:]

                parser = get_parser_by_ext(ext)
                if not parser:
                    log(f"Unable to find a matching parser for path<{path}>")
                    continue
            else:
                log(f"Unexisting extension, unable to determine matching parser for path<{path}>")
                continue
        with open(path) as f:
            content = f.read()
        try:
            data = parser(content).parse()
            # print(name, path, data)
            if data:
                if name not in result:
                    result[name] = {path: data}
                else:
                    result[name][path] = data

        except ParserSyntaxError as exc:
            log(f"Unable to parse config file '{path}': {exc}")


result["errors"] = errors
print(json.dumps(result))
