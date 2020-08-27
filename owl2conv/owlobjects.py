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
            pr.get_functional(graph)
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
                                pr.get_functional(graph)
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
    functional = False
    def __init__(self, uriref):
        """
        Initialize the class
        """
        super(owlprop, self).__init__(uriref)
        self.attributes[RDF.type] = ''
        self.attributes[RDFS.range] = ''

    def get_functional(self, graph):
        """
        Checks if the property is defined as funcional (cardinality 1)
        :param graph:
        :return:
        """
        self.functional = (self.uriref, RDF.type, OWL.FunctionalProperty) in graph

    def __repr__(self):
        s = f'N= {self.name} '
        for a in self.attributes:
            s += f'{self.chop(a)} = {self.chop(self.attributes[a])} '
        return s

    def toCLIPS(self):
        comment = self.attributes[RDFS.comment].strip("\n").strip(" ").strip("\n")
        if self.functional:
            s = f'(single-slot {self.name}'
        else:
            s = f'(multislot {self.name}'
        if self.attributes[RDF.type] in [OWL.DatatypeProperty, OWL.FunctionalProperty]:
            if self.attributes[RDFS.range] in datatypes:
                s += f'\n        (type {datatypes[self.attributes[RDFS.range]]})'
            else:
                s += '\n        (type SYMBOL)'
        else:
            s += '\n        (type INSTANCE)'
        s+= '\n        (create-accessor read-write)'
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
        # Selects the class for the instance skipping OWL.NamedIndividual
        for c in iclass:
            if c != OWL.NamedIndividual:
                self.iclass = self.chop(c)

        # If individual has no class something is wrong
        if self.iclass is None:
            raise NameError(f"Instance [{self.name}] is not assigned to a class")

        jclass = cdict[self.iclass]
        lclasses = [jclass]
        while jclass.parent is not None:
            lclasses.append(jclass.parent)
            jclass = jclass.parent

        for jclass in lclasses:
            for p in jclass.properties:
                prop = jclass.properties[p]
                val = [v for v in graph.objects(self.uriref, prop.uriref)]
                if len(val) > 0:
                    self.properties[prop.name] = (val, prop.attributes[RDFS.range])

    def toCLIPS(self):
        """
        Generate the CLIPS representation for an instacd
        :return:
        """
        level = '    '
        comment = self.attributes[RDFS.comment].strip("\n").strip(" ").strip("\n")

        s = f"([{self.name}] of {self.chop(self.iclass)}"
        pr = '\n'
        for p in self.properties:
            lval = self.properties[p][0]
            pr += f'{level}{level} ({self.chop(p)} '
            for val in lval:
                if isinstance(val, URIRef):
                    pr += f' [{self.chop(val)}]'
                if isinstance(val, Literal):
                    if val.datatype in [XSD.integer, XSD.int, XSD.float, XSD.double]:
                        pr += f' {val}'
                    else:
                        pr += f' "{val}"'
            pr += ')\n'

        return f'{level};;; {comment}\n    ' + s + pr + f'{level})\n' if (
                    comment != '') else level + s + pr + f'{level})\n'
