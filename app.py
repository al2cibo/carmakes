import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc

app = Dash(__name__)
server = app.server

# Load data
df = pd.read_csv('data.csv')
df['Year'] = pd.to_datetime(df['Year'], format='%Y')

# Custom CSS
custom_css = '''
body {
    font-family: Arial, sans-serif;
    background-color: #f0f2f6;
}
.container {
    background-color: white;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
.chart-title {
    font-size: 28px;
    font-weight: bold;
    text-align: center;
    margin-bottom: 30px;
}
.dropdown-container {
    margin-bottom: 20px;
}
.dropdown-label {
    font-weight: bold;
    margin-bottom: 5px;
}
.dropdown {
    width: 100%;
    margin-bottom: 10px;
}
'''

def create_car_ratings_plot(df, selected_make='All', selected_model='All'):
    df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')
    
    palette = ['#003e8a', '#0049a3', '#0060d6', '#006cf0', '#0a78ff', '#3d94ff', '#70b0ff', '#a3cdff', 
               '#6e6e6e', '#7a7a7a', '#878787', '#949494', '#c7c7c7', '#d4d4d4', '#e0e0e0']

    fig = go.Figure()

    for i, (name, group) in enumerate(df.groupby(['Make', 'Model'])):
        marker_sizes = group['Rating'].fillna(5).mul(3)
        
        visible = True
        showlegend = True
        if selected_make != 'All':
            if name[0] != selected_make:
                visible = 'legendonly'
                showlegend = False
        
        fig.add_trace(
            go.Scatter(
                x=group['Year'],
                y=group['Rating'],
                mode='lines+markers',
                name=f"{name[0]} - {name[1]}",
                line=dict(color=palette[i % len(palette)], width=2),
                marker=dict(
                    size=marker_sizes,
                    color=palette[i % len(palette)],
                    line=dict(width=1, color='white')
                ),
                hovertemplate='%{text}<extra></extra>',
                text=[f"{name[0]} - {name[1]}: {rating:.1f}" for rating in group['Rating']],
                visible=visible,
                showlegend=showlegend
            )
        )

    # Update title with additional info if brand or model is selected
    if selected_make != 'All':
        brand_data = df[df['Make'] == selected_make]
        avg_rating = brand_data['Rating'].mean()
        
        if selected_model != 'All':
            model_data = brand_data[brand_data['Model'] == selected_model]
            avg_rating = model_data['Rating'].mean()
            title = (f"{selected_make} {selected_model} Ratings Evolution<br>"
                     f"Average Rating: {avg_rating:.2f}")
        else:
            model_averages = brand_data.groupby('Model')['Rating'].mean()
            if len(model_averages) > 1:
                best_model = model_averages.idxmax()
                worst_model = model_averages.idxmin()
                title = (f"{selected_make} Ratings Evolution<br>"
                         f"Average: {avg_rating:.2f} | "
                         f"Best: {best_model} ({model_averages[best_model]:.1f}) | "
                         f"Worst: {worst_model} ({model_averages[worst_model]:.1f})")
            else:
                title = (f"{selected_make} Ratings Evolution<br>"
                         f"Average Rating: {avg_rating:.2f}")
    else:
        title = 'Car Ratings Evolution Over Time'

    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=24),
            x=0.5,
            y=0.95,
            xanchor='center',
            yanchor='top'
        ),
        xaxis_title='Year',
        yaxis_title='Rating',
        yaxis=dict(range=[5, 10]),
        hovermode='x unified',
        legend_title='Make - Model',
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Arial, sans-serif"),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Arial"
        ),
        height=700,
        width=1400
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="#eee",
        zeroline=False,
        dtick="M12",
        tickformat="%Y"
    )
    fig.update_yaxes(showgrid=False, zeroline=False)

    return fig

# Create Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define layout
app.layout = html.Div([
    html.Div(custom_css, style={'display': 'none'}),  # Add custom CSS
    dbc.Container([
        html.H1("Car Ratings Evolution", className="chart-title"),
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Label('Make:', className="dropdown-label"),
                    dcc.Dropdown(
                        id='make-dropdown',
                        options=[{'label': make, 'value': make} for make in ['All'] + sorted(df['Make'].unique())],
                        value='All',
                        className="dropdown"
                    ),
                    html.Label('Model:', className="dropdown-label"),
                    dcc.Dropdown(id='model-dropdown', className="dropdown")
                ], className="dropdown-container")
            ], width=2),
            dbc.Col([
                dcc.Graph(id='car-ratings-plot')
            ], width=10)
        ])
    ], fluid=True, className="container")
])

@app.callback(
    Output('model-dropdown', 'options'),
    Output('model-dropdown', 'value'),
    Input('make-dropdown', 'value')
)
def update_model_dropdown(selected_make):
    if selected_make == 'All':
        models = ['All'] + sorted(df['Model'].unique())
    else:
        models = ['All'] + sorted(df[df['Make'] == selected_make]['Model'].unique())
    return [{'label': model, 'value': model} for model in models], 'All'

@app.callback(
    Output('car-ratings-plot', 'figure'),
    Input('make-dropdown', 'value'),
    Input('model-dropdown', 'value')
)
def update_figure(selected_make, selected_model):
    fig = create_car_ratings_plot(df, selected_make, selected_model)
    
    # Update visibility based on selected model
    if selected_model != 'All':
        for trace in fig.data:
            if selected_model not in trace.name:
                trace.visible = 'legendonly'
    
    return fig

if __name__ == '__main__':
    app.run_server()
