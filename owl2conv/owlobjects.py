"""
.. module:: owlobjects

owlobjects
******

:Description: owlobjects

    Classes for different owl objects

:Authors:
    bejar

:Version: 

:Date:  08/05/2020
"""
from rdflib import RDFS, RDF, OWL, XSD, URIRef, Literal, BNode

__author__ = 'bejar'

datatypes = {XSD.string: 'STRING',
             XSD.integer: 'INTEGER',
             XSD.int: 'INTEGER',
             XSD.float: 'FLOAT',
             XSD.double: 'FLOAT'}


class owlobject:
    def __init__(self, uriref):
        """
        Initialize the class
        """
        self.uriref = uriref
        self.name = self.chop(uriref)
        self.attributes = {RDFS.comment: '', RDFS.label: ''}

    def get_attributes_from_graph(self, graph):
        for predicate in self.attributes:
            v = graph.value(self.uriref, predicate)
            self.attributes[predicate] = v if v is not None else ''

    def chop(self, uriref):
        if '#' in uriref:
            return uriref.toPython().split("#")[-1]
        elif '/' in uriref:
            return uriref.toPython().split("/")[-1]
        else:
            return uriref


class owlclass(owlobject):
    """
    Class for representing the data for an OWL class
    """

    def __init__(self, uriref):
        """
        Initialize the class
        """
        super(owlclass, self).__init__(uriref)
        self.properties = {}
        self.parent = None

    def get_properties_from_graph(self, graph):
        # Get all properties that have this class as domain
        props = graph.subjects(RDFS.domain, self.uriref)
        # Properties with domain equal to the class URI
        for p in props:
            pr = owlprop(p)
            pr.get_attributes_from_graph(graph)
            self.properties[pr.name] = pr

        # Properties that are in the union of a domain
        props = graph.subject_objects(RDFS.domain)
        for s, o in props:
            if type(o) == BNode:
                d = graph.objects(o, OWL.unionOf)
                if d is not None:
                    uof = self._get_union(next(d), graph)
                    if len(uof) != 0:
                        if self.uriref in uof:
                            pr = owlprop(s)
                            if pr.name not in self.properties:
                                pr.get_attributes_from_graph(graph)
                                self.properties[pr.name] = pr

    def _get_union(self, uri, graph):
        """
        Get elements that compose a unionGf
        Follow the links of the list
        :param graph:
        :return:
        """
        dom = []
        rest = uri
        while rest != RDF.nil:
            first = [v for v in graph.objects(rest, RDF.first)][0]
            dom.append(first)
            rest = [v for v in graph.objects(rest, RDF.rest)][0]
        return dom

    def __repr__(self):
        s = f'N= {self.name} '
        for a in self.attributes:
            s += f'{self.chop(a)} = {self.attributes[a]}'

        for p in self.properties:
            s += f'\n PR= {p.__repr__()} '

        return s

    def toCLIPS(self):
        """
        Generates a representation of the class using COOL CLIPS language
        :return:
        """
        comment = self.attributes[RDFS.comment].strip("\n").strip(" ").strip("\n")
        s = f'(defclass {self.name} "{comment}"\n' if comment != '' else f'(defclass {self.name}\n'
        if self.parent is None:
            s += '    (is-a USER)\n'
        else:
            s += f'    (is-a {self.parent.name})\n'
        s += '    (role concrete)\n    (pattern-match reactive)\n'
        for p in self.properties:
            s += '    ' + self.properties[p].toCLIPS()

        s += ')\n'
        return s


class owlprop(owlobject):
    """
    class for OWL properties
    """

    def __init__(self, uriref):
        """
        Initialize the class
        """
        super(owlprop, self).__init__(uriref)
        self.attributes[RDF.type] = ''
        self.attributes[RDFS.range] = ''

    def __repr__(self):
        s = f'N= {self.name} '
        for a in self.attributes:
            s += f'{self.chop(a)} = {self.chop(self.attributes[a])} '
        return s

    def toCLIPS(self):
        comment = self.attributes[RDFS.comment].strip("\n").strip(" ").strip("\n")
        s = f'(multislot {self.name}'
        if self.attributes[RDF.type] in [OWL.DatatypeProperty, OWL.FunctionalProperty]:
            if self.attributes[RDFS.range] in datatypes:
                s += f' (type {datatypes[self.attributes[RDFS.range]]})'
            else:
                s += ' (type SYMBOL)'
        else:
            s += ' (type INSTANCE)'
        return f';;; {comment}\n    ' + s + ')\n' if (comment != '') else s + ')\n'


class owlinstance(owlobject):

    def __init__(self, uriref):
        """
        Initialize the class
        """
        super(owlinstance, self).__init__(uriref)
        self.iclass = None
        self.properties = {}

    def get_info_from_graph(self, graph, cdict):
        """
        Extract from the graph the properties for the instance and record the information from the class of the instance
        :param graph:
        :param cdict:
        :return:
        """

        iclass = graph.objects(self.uriref, RDF.type)
        # Selects the class for the instance skiping OWL.NamedIndividual
        for c in iclass:
            if c != OWL.NamedIndividual:
                self.iclass = self.chop(c)

        # If individual has no class something is wrong
        if self.iclass is None:
            raise NameError(f"Instance [{self.name}] is not assigned to a class")

        jclass = cdict[self.iclass]
        for p in jclass.properties:
            prop = jclass.properties[p]
            val = [v for v in graph.objects(self.uriref, prop.uriref)]
            if len(val) != 0:
                self.properties[prop.name] = (val[0], prop.attributes[RDFS.range])

    def toCLIPS(self):
        """
        Generate the CLIPS representation for an instacd
        :return:
        """
        level = '    '
        comment = self.attributes[RDFS.comment].strip("\n").strip(" ").strip("\n")

        s = f"({self.name} of {self.chop(self.iclass)}"
        pr = '\n'
        for p in self.properties:
            val = self.properties[p][0]
            if isinstance(val, URIRef):
                pr += f'{level}{level} ({self.chop(p)} [{self.chop(val)}])\n'
            if isinstance(val, Literal):
                pr += f'{level}{level} ({self.chop(p)} "{val}")\n'

        return f'{level};;; {comment}\n    ' + s + pr + f'{level})\n' if (
                    comment != '') else level + s + pr + f'{level})\n'
