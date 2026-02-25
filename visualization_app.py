import streamlit as st
import plotly.graph_objects as go
from graphviz import Digraph
import plotly.express as px


# Updated Data Structure
data_object = {
    "name": "High Risk Actioned Patients",
    "value": 204,
    "children": [
        {
            "name": "Patients Completed journey",
            "value": 151,
            "children": [
                {
                    "name": "Patients Confirmed Diagnosis",
                    "value": 128,
                    "children": [
                        {"name": "Awaiting Rx", "value": 12},
                        {"name": "Patients Diagnosed on Target Therapy", "value": 116}
                    ]
                },
                {"name": "Patients Ruled Out", "value": 23, "children": []}
            ]
        },
        {"name": "Patients Still in journey", "value": 53, "children": []}
    ]
}


# Helper Function for Treemap and Sunburst (Flatten Tree)
def flatten_hierarchy(node, path=[]):
    flat_data = []
    current_path = path + [node["name"]]
    flat_data.append({
        "path": " > ".join(current_path),
        "value": node.get("value", 0)
    })
    for child in node.get("children", []):
        flat_data.extend(flatten_hierarchy(child, current_path))
    return flat_data


import plotly.colors as pc

# Generate Sankey Diagram
def generate_sankey(data):
    labels, sources, targets, values = [], [], [], []
    colors = []
    base_color = pc.sequential.Blues  # Use a sequential color palette

    def traverse(node, parent_idx=None, level=0):
        idx = len(labels)
        labels.append(f"{node['name']} ({node['value']})")
        current_color = base_color[min(level, len(base_color) - 1)]  # Pick color based on level
        
        if parent_idx is not None:
            sources.append(parent_idx)
            targets.append(idx)
            values.append(node.get("value", 0))
            colors.append(current_color)
        
        for child in node.get("children", []):
            traverse(child, idx, level + 1)

    traverse(data)

    fig = go.Figure(go.Sankey(
        node=dict(
            label=labels,
            pad=20,  # Space between nodes
            thickness=20,  # Thickness of the nodes
            color="rgba(173, 216, 230, 0.8)"  # Light blue for nodes
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=colors  # Gradual coloring for streams
        )
    ))

    # Adjust figure size and add softer aesthetics
    fig.update_layout(
        title_text="Sankey Diagram",
        font_size=12,
        width=1200,
        height=600,
        plot_bgcolor="white",  # Softer background
    )
    st.plotly_chart(fig)

import plotly.express as px
import networkx as nx
from scipy.cluster.hierarchy import dendrogram, linkage
import numpy as np

# Icicle Chart
def generate_icicle(data):
    flat_data = flatten_hierarchy(data)
    fig = px.icicle(flat_data, path=["path"], values="value")
    st.plotly_chart(fig)

# Partition Chart (Horizontal Icicle)
def generate_partition(data):
    flat_data = flatten_hierarchy(data)
    fig = px.icicle(flat_data, path=["path"], values="value", orientation="h")
    st.plotly_chart(fig)

# Dendrogram
def generate_dendrogram(data):
    labels, sources, targets = [], [], []

    def traverse(node, parent_idx=None):
        idx = len(labels)
        labels.append(node["name"])
        if parent_idx is not None:
            sources.append(parent_idx)
            targets.append(idx)
        for child in node.get("children", []):
            traverse(child, idx)

    traverse(data)
    adjacency_matrix = np.zeros((len(labels), len(labels)))
    for src, tgt in zip(sources, targets):
        adjacency_matrix[src, tgt] = 1

    Z = linkage(adjacency_matrix, method="ward")
    dendrogram_data = dendrogram(Z, labels=labels, orientation="top")
    st.pyplot()

# Radial Tree
def generate_radial_tree(data):
    G = nx.DiGraph()

    def traverse(node):
        G.add_node(node["name"])
        for child in node.get("children", []):
            G.add_edge(node["name"], child["name"])
            traverse(child)

    traverse(data)
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_size=500, font_size=10)
    st.pyplot()

# Heatmap
def generate_heatmap(data):
    flat_data = flatten_hierarchy(data)
    value_matrix = np.array([item["value"] for item in flat_data])
    fig = px.imshow(value_matrix, labels={"color": "Value"})
    st.plotly_chart(fig)



# Generate Flowchart
def generate_flowchart(data):
    dot = Digraph()
    
    def add_nodes(node):
        dot.node(node["name"], f"{node['name']} ({node['value']})")
        for child in node.get("children", []):
            dot.edge(node["name"], child["name"])
            add_nodes(child)

    add_nodes(data)
    st.graphviz_chart(dot)


# Generate Treemap
def generate_treemap(data):
    flat_data = flatten_hierarchy(data)
    fig = px.treemap(flat_data, path=["path"], values="value")
    st.plotly_chart(fig)


# Generate Sunburst Chart
def generate_sunburst(data):
    flat_data = flatten_hierarchy(data)
    fig = px.sunburst(flat_data, path=["path"], values="value")
    st.plotly_chart(fig)


# Generate Hierarchical Tree
def generate_hierarchical_tree(data):
    dot = Digraph(format="png")
    
    def add_nodes(node):
        label = f"{node['name']} ({node['value']})"
        dot.node(node["name"], label)
        for child in node.get("children", []):
            dot.edge(node["name"], child["name"])
            add_nodes(child)

    add_nodes(data)
    st.graphviz_chart(dot)


# Main Module to Generate All Charts
def main():
    st.title("Hierarchical Data Visualization")
    
    # Select Chart Type
    chart_type = st.sidebar.selectbox(
        "Select Chart Type",
        ["Sankey Diagram", "Flowchart", "Treemap", "Sunburst Chart", 
            "Hierarchical Tree", "Icicle Chart", "Partition Chart", 
            "Dendrogram", "Radial Tree", "Heatmap"]
    )
    
    # Render the selected chart
    if chart_type == "Sankey Diagram":
        st.header("Sankey Diagram")
        generate_sankey(data_object)
    
    elif chart_type == "Flowchart":
        st.header("Flowchart")
        generate_flowchart(data_object)
    
    elif chart_type == "Treemap":
        st.header("Treemap")
        generate_treemap(data_object)
    
    elif chart_type == "Sunburst Chart":
        st.header("Sunburst Chart")
        generate_sunburst(data_object)
    
    elif chart_type == "Hierarchical Tree":
        st.header("Hierarchical Tree")
        generate_hierarchical_tree(data_object)
    
    elif chart_type == "Icicle Chart":
        generate_icicle(data_object)
    elif chart_type == "Partition Chart":
        generate_partition(data_object)
    elif chart_type == "Dendrogram":
        generate_dendrogram(data_object)
    elif chart_type == "Radial Tree":
        generate_radial_tree(data_object)
    elif chart_type == "Heatmap":
        generate_heatmap(data_object)


# Run the Streamlit App
if __name__ == "__main__":
    main()
