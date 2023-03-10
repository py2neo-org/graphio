from graphio.objects.unstructured_nodeset import UnstructuredNodeSet, Node
from graphio.graph import run_query_return_results


class TestUnstructuredNodeSet:

    def test_unique_node_definitions(self):
        uns = UnstructuredNodeSet()
        uns.add_node(Node(labels=["A"], merge_keys=["a"]))
        uns.add_node(Node(labels=["A"], merge_keys=["b"]))
        uns.add_node(Node(labels=["B", "C"], merge_keys=["a"]))
        uns.add_node(Node(labels=["B"], merge_keys=["b", "c"]))

        assert uns.unique_node_definitions == {(('A',), ('b',)), (('B', 'C'), ('a',)), (('A',), ('a',)),
                                               (('B',), ('b', 'c'))}


class TestUnstructuredNodeSetIndexes:

    def test_create_single_indexes(self, graph, clear_graph):
        labels = ["A"]
        properties = ["a"]
        uns = UnstructuredNodeSet()
        uns.add_node(Node(labels=labels, merge_keys=properties))

        uns.create_index(graph)

        # TODO keep until 4.2 is not supported anymore
        try:
            result = run_query_return_results(graph, "SHOW INDEXES YIELD *")
        except:
            result = run_query_return_results(graph, "CALL db.indexes()")

        for row in result:
            if 'tokenNames' in row:
                assert row['tokenNames'] == labels and row['properties'] == properties \
                       or row['tokenNames'] == labels and row['properties'] == properties

            elif 'labelsOrTypes' in row:
                assert row['labelsOrTypes'] == labels and row['properties'] == properties \
                       or row['labelsOrTypes'] == labels and row['properties'] == properties

    def test_create_composite_indexes(self, graph, clear_graph):
        labels = ["A"]
        properties = ["a", "b"]
        uns = UnstructuredNodeSet()
        uns.add_node(Node(labels=labels, merge_keys=properties))

        uns.create_index(graph)

        # TODO keep until 4.2 is not supported anymore
        try:
            result = run_query_return_results(graph, "SHOW INDEXES YIELD *")
        except:
            result = run_query_return_results(graph, "CALL db.indexes()")

        for row in result:
            if 'tokenNames' in row:
                assert row['tokenNames'] == labels and row['properties'] == properties \
                       or row['tokenNames'] == labels and row['properties'] == properties

            elif 'labelsOrTypes' in row:
                assert row['labelsOrTypes'] == labels and row['properties'] == properties \
                       or row['labelsOrTypes'] == labels and row['properties'] == properties


class TestUnstructuredNodeSetCreate:
    def test_unstructured_nodeset_create(self, graph, clear_graph):
        uns = UnstructuredNodeSet()
        uns.add_node(Node(labels=["A"], merge_keys=["a"], properties={"a": 1}))
        uns.add_node(Node(labels=["A"], merge_keys=["b"], properties={"b": 2}))
        uns.add_node(Node(labels=["B", "C"], merge_keys=["a"], properties={"a": 3}))
        uns.add_node(Node(labels=["B"], merge_keys=["b", "c"], properties={"b": 4, "c": 5}))

        uns.create(graph)

        result = run_query_return_results(graph, "MATCH (n) RETURN n, labels(n) AS labels")

        assert len(result) == 4
        for row in result:
            if 'a' in row['n']:
                if row['n']['a'] == 1:
                    assert row['labels'] == ['A']
            elif 'b' in row['n']:
                if row['n']['b'] == 2:
                    assert row['labels'] == ['A']
                elif row['n']['b'] == 4:
                    assert row['labels'] == ['B']
                    assert row['n']['c'] == 5
            elif 'c' in row['n']:
                assert row['n']['c'] == 5
                assert row['labels'] == ['B']


class TestUnstructuredNodeSetMerge:
    def test_unstructured_nodeset_merge(self, graph, clear_graph):
        uns = UnstructuredNodeSet()
        uns.add_node(Node(labels=["A"], merge_keys=["a"], properties={"a": 1}))
        uns.add_node(Node(labels=["A"], merge_keys=["b"], properties={"b": 2}))
        uns.add_node(Node(labels=["B", "C"], merge_keys=["a"], properties={"a": 3}))
        uns.add_node(Node(labels=["B"], merge_keys=["b", "c"], properties={"b": 4, "c": 5}))

        uns.merge(graph)
        uns.merge(graph)
        uns.merge(graph)

        result = run_query_return_results(graph, "MATCH (n) RETURN n, labels(n) AS labels")

        assert len(result) == 4

        for row in result:
            if 'a' in row['n']:
                if row['n']['a'] == 1:
                    assert row['labels'] == ['A']
            elif 'b' in row['n']:
                if row['n']['b'] == 2:
                    assert row['labels'] == ['A']
                elif row['n']['b'] == 4:
                    assert row['labels'] == ['B']
                    assert row['n']['c'] == 5
            elif 'c' in row['n']:
                assert row['n']['c'] == 5
                assert row['labels'] == ['B']


class TestUnstructuredNodeSetReturnNodeset:
    def test_unstructured_nodeset_return_nodeset(self):
        uns = UnstructuredNodeSet()
        uns.add_node(Node(labels=["A"], merge_keys=["a"], properties={"a": 1}))
        uns.add_node(Node(labels=["A"], merge_keys=["b"], properties={"b": 2}))
        uns.add_node(Node(labels=["B", "C"], merge_keys=["a"], properties={"a": 3}))
        uns.add_node(Node(labels=["B"], merge_keys=["b", "c"], properties={"b": 4, "c": 5}))

        nodesets = uns.nodesets()

        assert ["A"] in [ns.labels for ns in nodesets]
        assert ["B"] in [ns.labels for ns in nodesets]
        assert ["B", "C"] in [ns.labels for ns in nodesets]
