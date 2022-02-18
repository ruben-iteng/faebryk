# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import networkx as nx
from faebryk.libs.util import hashable_dict, unique
from faebryk.libs.exceptions import FaebrykException

# 0. netlist = graph

#TODO add name precendence
# t1 is basically a reduced version of the grap
# t1_netlist = [
#     {name, value, properties, real,
#       neighbors={pin: [{&vertex, pin}]},
# ]


# t2 is transposed to list nets instead of vertices
# t2_netlist = [(properties, vertices=[comp=(name, value, properties), pin)])]

class vertex(hashable_dict):
    def __init__(self, node, pin):
        super().__init__({"node": node["name"], "pin": pin})
        self.node = node
        self.pin = pin

def _make_graph(netlist):
    G = nx.Graph()
    edges = [((vertex(node, spin)),
                (vertex(neighbor["vertex"], neighbor["pin"])))
        for node in netlist
        for spin,v_neighbors in node.get("neighbors", {1: []}).items()
        for neighbor in v_neighbors
    ]
    for s_vertex,d_vertex in edges:
        if d_vertex.node not in netlist:
            for c in netlist:
                if c["name"] == d_vertex.node["name"]:
                    print(f"{c} != {d_vertex.node}")
            raise FaebrykException("{} was connected to but not in graph as node".format(
                d_vertex.node["name"]))
    #TODO check if any nodes in netlist are not appearing in Graph

    G.add_edges_from(edges)
    return G


def make_t2_netlist_from_t1(t1_netlist):
    # make undirected graph where nodes=(vertex, pin),
    #   edges=in neighbors relation
    # nets = connected components
    # opt: determine net.prop.name by nodes?

    G = _make_graph(t1_netlist)
    nets = list(nx.connected_components(G))

    # Only keep nets that have more than one real component connected
    nets = [net for net in nets
        if len([vertex for vertex in net if vertex.node["real"]]) > 1]

    def determine_net_name(net):
        #TODO use name precedence instead

        virtual_name = "-".join(
            [
                vertex.node["name"] + ("" if vertex.pin == 1 else f":{vertex.pin}")
                    for vertex in net
                    if not vertex.node["real"]
            ])
        if virtual_name != "":
            return virtual_name

        comp_name = "-".join(vertex.node["name"] for vertex in net)
        if comp_name != "":
            return comp_name

        #TODO implement default policy
        raise NotImplementedError

    t2_netlist = [
        {
            "properties": {
                "name": determine_net_name(net),
            },
            "vertices": [
                {
                    "comp": {k:v for k,v in vertex.node.items() if k not in ["real", "neighbors"]},
                    "pin": vertex.pin
                }
                for vertex in net
                if vertex.node["real"]
            ]
        }
        for net in nets
    ]

    return t2_netlist

def render_graph(t1_netlist, write_to_file: bool):
    import matplotlib.pyplot as plt

    G = _make_graph(t1_netlist)

    nodes = [vertex(node, spin)
        for node in t1_netlist
        for spin in node.get("neighbors", {1: None}).keys()
    ]
    nodes_dict = {node:"{}".format(node.pin)
        for node in nodes}


    netedges = G.edges()

    # Make edges between pins within component
    def _helper(obj):
        return list(obj["neighbors"].keys())

    intra_comp_edges = [
        (vertex(node, spin), vertex(node, dpin))
            for node in t1_netlist
            for spin in _helper(node)
            for dpin in _helper(node)
            if spin != dpin
    ]
    G.add_edges_from(intra_comp_edges)

    import re
    intra_edge_dict = dict(unique({edge:"{}".format(
        re.search(r"\[.*\]",
            edge[0].node["name"]).group()
        )
        for edge in intra_comp_edges
    }.items(), key=lambda edge:edge[0][0].node))

    # Draw
    plt.subplot(121)
    layout = nx.spring_layout(G)
    nx.draw_networkx_nodes(G, pos=layout, node_size=150)
    nx.draw_networkx_edges(G, pos=layout, edgelist=netedges, edge_color="#FF0000")
    nx.draw_networkx_edges(G, pos=layout, edgelist=intra_comp_edges, edge_color="#0000FF")
    nx.draw_networkx_labels(G, pos=layout, labels=nodes_dict)
    nx.draw_networkx_edge_labels(G, pos=layout, edge_labels=intra_edge_dict,
        font_size=10, rotate=False, bbox=dict(fc="blue"), font_color="white")
    if write_to_file == True:
        plt.savefig('./build/render.png', bbox_inches='tight')
    plt.show()
