import plotly.graph_objects as go
import asdf
import os
import numpy as np

def plot_angular_coverage(coronagraph_list):
    fig = go.Figure()
    this_metric = "angular_coverage"

    for this_coronagraph in coronagraph_list:
        this_plot_file = os.path.join(this_coronagraph, this_metric + ".asdf")
        print(this_plot_file)
        this_file = os.path.join(os.path.abspath("./data/"), this_plot_file)
        af = asdf.open(this_file)
        print(af.tree)
        fig.add_trace(go.Line(x=af.tree['r'], y=af.tree['coverage'],name=this_coronagraph))

    fig.update_layout(xaxis_title="Angular separation ()") # \u03bb is lambda
    fig.update_layout(yaxis_title="Angular coverage [fraction]")
    fig.update_layout(title=f"Angular Separation Comparison")
    fig.update_xaxes(range=[0, 32])
    fig.update_yaxes(range=[0, 1.05])
    fig.show() 

    return fig

def plot_contrast_curve(coronagraph_list):
    fig = go.Figure()
    this_metric = "contrast_curve"
    
    for this_coronagraph in coronagraph_list:
        this_plot_file = os.path.join(this_coronagraph, this_metric + ".asdf")
        print(this_plot_file)
        this_file = os.path.join(os.path.abspath("./data/"), this_plot_file)
        af = asdf.open(this_file)
        print(af.tree)
        fig.add_trace(go.Line(x=af.tree['r'], y=af.tree['y'],name=this_coronagraph))

    fig.update_layout(yaxis_type="log")
    fig.update_layout(xaxis_title="Angular separation (\u03bb / D)") # \u03bb is lambda
    fig.update_layout(yaxis_title="Contrast (log scale)")
    fig.update_layout(title=f"Contrast Curve Comparison")
    fig.update_xaxes(range=[0, 32])
    fig.update_yaxes(range=[np.log10(5e-12), np.log10(2e-8)], showexponent='all', exponentformat='E')
    fig.show()

    return fig