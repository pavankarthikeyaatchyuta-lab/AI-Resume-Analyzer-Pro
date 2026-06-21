import plotly.graph_objects as go


def create_score_chart(scores, chart_type):
    labels = list(scores.keys())
    values = list(scores.values())
    colors = ["#67e8f9", "#8b5cf6", "#f59e0b"]

    if chart_type == "Vertical Bar":
        fig = go.Figure([go.Bar(x=labels, y=values, marker=dict(color=colors), text=values, textposition="outside")])
        fig.update_yaxes(range=[0, 100], gridcolor="rgba(148,163,184,0.16)")
    elif chart_type == "Horizontal Bar":
        fig = go.Figure(
            [go.Bar(y=labels, x=values, orientation="h", marker=dict(color=colors), text=values, textposition="outside")]
        )
        fig.update_xaxes(range=[0, 100], gridcolor="rgba(148,163,184,0.16)")
    elif chart_type == "Pie Chart":
        fig = go.Figure([go.Pie(labels=labels, values=values, marker=dict(colors=colors), hole=0.52)])
    else:
        fig = go.Figure(
            [
                go.Scatterpolar(
                    r=values + values[:1],
                    theta=labels + labels[:1],
                    fill="toself",
                    fillcolor="rgba(103, 232, 249, 0.18)",
                    line=dict(color="#67e8f9", width=3),
                )
            ]
        )
        fig.update_polars(radialaxis=dict(range=[0, 100], visible=True, gridcolor="rgba(148,163,184,0.16)"))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e5eefc"),
        margin=dict(l=20, r=20, t=25, b=20),
        showlegend=False,
    )
    return fig


def create_gauge_chart(scores):
    fig = go.Figure()
    domains = [(0.00, 0.30), (0.35, 0.65), (0.70, 1.00)]
    colors = ["#67e8f9", "#8b5cf6", "#f59e0b"]

    for index, (label, value) in enumerate(scores.items()):
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=value,
                title={"text": label, "font": {"size": 17, "color": "#e5eefc"}},
                domain={"x": [domains[index][0], domains[index][1]], "y": [0, 1]},
                gauge={
                    "axis": {"range": [0, 100], "tickcolor": "#94a3b8"},
                    "bar": {"color": colors[index]},
                    "bgcolor": "rgba(15,23,42,0.92)",
                    "borderwidth": 1,
                    "bordercolor": "rgba(148,163,184,0.24)",
                },
            )
        )

    fig.update_layout(
        height=320,
        margin=dict(l=20, r=20, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e5eefc"),
    )
    return fig
