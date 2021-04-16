import logging
from uuid import uuid4
from py2neo.bulk import create_nodes, merge_nodes

from graphio.objects.helper import chunks, create_single_index, create_composite_index
from graphio import defaults
from graphio.objects.relationshipset import RelationshipSet

log = logging.getLogger(__name__)


class NodeSet:
    """
    Container for a set of Nodes with the same labels and the same properties that define uniqueness.
    """

    def __init__(self, labels, merge_keys=None, batch_size=None):
        """

        :param labels: The labels for the nodes in this NodeSet.
        :type labels: list[str]
        :param merge_keys: The properties that define uniqueness of the nodes in this NodeSet.
        :type merge_keys: list[str]
        :param batch_size: Batch size for Neo4j operations.
        :type batch_size: int
        """
        self.labels = labels
        self.merge_keys = merge_keys

        self.combined = '_'.join(sorted(self.labels)) + '_' + '_'.join(sorted(self.merge_keys))
        self.uuid = str(uuid4())

        if batch_size:
            self.batch_size = batch_size
        else:
            self.batch_size = defaults.BATCHSIZE

        self.nodes = []

    def __str__(self):
        return f"<NodeSet ({self.labels}; {self.merge_keys})>"

    def add_node(self, properties):
        """
        Create a node in this NodeSet.

        :param properties: Node properties.
        :type properties: dict
        """
        self.nodes.append(properties)

    def add_nodes(self, list_of_properties):
        for properties in list_of_properties:
            self.add_node(properties)

    def add_unique(self, properties):
        """
        Add a node to this NodeSet only if a node with the same `merge_keys` does not exist yet.

        Note: Right now this function iterates all nodes in the NodeSet. This is of course slow for large
        numbers of nodes. A better solution would be to create an 'index' as is done for RelationshipSet.

        :param properties: Node properties.
        :type properties: dict
        """

        compare_values = frozenset([properties[key] for key in self.merge_keys])

        for other_node_properties in self.node_properties():
            this_values = frozenset([other_node_properties[key] for key in self.merge_keys])
            if this_values == compare_values:
                return None

        # add node if not found
        self.add_node(properties)

    def to_dict(self):
        """
        Create dictionary defining the nodeset.
        """
        return {"labels":self.labels, "merge_keys":self.merge_keys, "nodes":self.nodes}

    @classmethod
    def from_dict(cls,nodeset_dict, batch_size=None):
        ns = cls(labels=nodeset_dict["labels"],merge_keys=nodeset_dict["merge_keys"])
        ns.add_nodes(nodeset_dict["nodes"])
        return ns

    def create(self, graph, batch_size=None):
        """
        Create all nodes from NodeSet.
        """
        log.debug('Create NodeSet')
        if not batch_size:
            batch_size = self.batch_size
        log.debug('Batch Size: {}'.format(batch_size))

        i = 1
        for batch in chunks(self.nodes, size=batch_size):

            log.debug('Batch {}'.format(i))

            create_nodes(graph, batch, labels=self.labels)

            i += 1

    def merge(self, graph, merge_properties=None, batch_size=None):
        """
        Merge nodes from NodeSet on merge properties.

        :param merge_properties: The merge properties.
        """
        log.debug('Merge NodeSet on {}'.format(merge_properties))

        if not batch_size:
            batch_size = self.batch_size

        if not merge_properties:
            merge_properties = self.merge_keys

        log.debug('Batch Size: {}'.format(batch_size))

        i = 1
        for batch in chunks(self.node_properties(), size=batch_size):

            log.debug('Batch {}'.format(i))
            merge_nodes(graph, batch, (tuple(self.labels), *merge_properties))

            i += 1

    def map_to_1(self, graph, target_labels, target_properties, rel_type=None):
        """
        Create relationships from all nodes in this NodeSet to 1 target node.

        :param graph: The py2neo Graph
        :param other_node: The target node.
        :param rel_type: Relationship Type
        """

        if not rel_type:
            rel_type = 'FROM_SET'

        rels = RelationshipSet(rel_type, self.labels, target_labels, self.merge_keys, target_properties)

        for node in self.nodes:
            # get properties for merge_keys
            node_properties = {}
            for k in self.merge_keys:
                node_properties[k] = node[k]

            rels.add_relationship(node_properties, target_properties, {})

        rels.create(graph)

    def node_properties(self):
        """
        Yield properties of the nodes in this set. Used for create function.
        """
        for n in self.nodes:
            yield dict(n)

    def all_properties_in_nodeset(self):
        """
        Return a set of all property keys in this NodeSet

        :return: A set of unique property keys of a NodeSet
        """
        all_props = set()

        # collect properties
        for props in self.node_properties():
            for k in props:
                all_props.add(k)

        return all_props

    def create_index(self, graph):
        """
        Create indices for all label/merge ky combinations as well as a composite index if multiple merge keys exist.

        In Neo4j 3.x recreation of an index did not raise an error. In Neo4j 4 you cannot create an existing index.

        Index creation syntax changed from Neo4j 3.5 to 4. So far the old syntax is still supported. All py2neo
        functions (v4.4) work on both versions.
        """
        if self.merge_keys:
            for label in self.labels:
                # create individual indexes
                for prop in self.merge_keys:
                    create_single_index(graph, label, prop)

                # composite indexes
                if len(self.merge_keys) > 1:
                    create_composite_index(graph, label, self.merge_keys)
