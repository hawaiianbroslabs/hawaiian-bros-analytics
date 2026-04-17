import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

# Page config with Hawaiian Bros branding
st.set_page_config(
    page_title="Hawaiian Bros Analytics Hub",
    page_icon="🏝️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hawaiian Bros color palette
AQUARIUM_TEAL = "#00A8BF"
GULFSTREAM_TEAL = "#007784"
OBSTINATE_ORANGE = "#F46241"
REPOSE_GRAY = "#D0D1D8"

# Custom CSS for Hawaiian Bros styling
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }
    
    .stSelectbox > div > div > div {
        background-color: rgba(255, 255, 255, 0.9);
    }
    
    h1 {
        background: linear-gradient(135deg, #00A8BF 0%, #007784 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        margin-bottom: 0.5rem !important;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data_from_sheets(sheet_url):
    """Load data from Google Sheets using the public CSV export URLs"""
    try:
        # Extract the sheet ID from the URL
        sheet_id = sheet_url.split('/d/')[1].split('/')[0]
        
        # Define sheet names and their corresponding GIDs (we'll try common ones)
        sheets_to_load = {
            'fact_table': '0',  # Usually the first sheet
            'locations': '1',
            'sales_metrics': '2', 
            'beverage_incidence': '3',
            'dessert_incidence': '4'
        }
        
        data = {}
        
        for sheet_name, gid in sheets_to_load.items():
            try:
                # Construct CSV export URL
                csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
                df = pd.read_csv(csv_url)
                data[sheet_name] = df
                st.sidebar.success(f"✅ Loaded {sheet_name}: {len(df)} rows")
            except Exception as e:
                st.sidebar.warning(f"⚠️ Could not load {sheet_name}: {str(e)}")
        
        return data
        
    except Exception as e:
        st.error(f"Failed to load data from Google Sheets: {str(e)}")
        return {}

@st.cache_data
def calculate_metrics(data):
    """Calculate key operational metrics from the loaded data"""
    
    if 'sales_metrics' not in data or 'beverage_incidence' not in data:
        return {}
    
    sales_df = data['sales_metrics']
    bev_df = data['beverage_incidence'] 
    dessert_df = data.get('dessert_incidence', pd.DataFrame())
    
    # System-wide averages
    system_avg_check = sales_df['average_check'].mean() if 'average_check' in sales_df.columns else 0
    system_bev_inc = bev_df['beverage_incidence'].mean() if 'beverage_incidence' in bev_df.columns else 0
    system_dessert_inc = dessert_df['dessert_incidence'].mean() if len(dessert_df) > 0 and 'dessert_incidence' in dessert_df.columns else 0
    
    return {
        'system_avg_check': system_avg_check,
        'system_bev_incidence': system_bev_inc,
        'system_dessert_incidence': system_dessert_inc
    }

def get_location_performance(data, location_id=None):
    """Get performance metrics for a specific location or all locations"""
    
    if 'sales_metrics' not in data:
        return pd.DataFrame()
    
    sales_df = data['sales_metrics']
    
    if location_id and location_id != 'All Locations':
        sales_df = sales_df[sales_df['location_id'] == location_id]
    
    # Group by location for summary
    location_summary = sales_df.groupby('location_id').agg({
        'Net Sales': 'sum',
        'Transactions': 'sum', 
        'average_check': 'mean'
    }).round(2)
    
    # Add beverage and dessert incidence if available
    if 'beverage_incidence' in data:
        bev_summary = data['beverage_incidence'].groupby('location_id')['beverage_incidence'].mean()
        location_summary = location_summary.join(bev_summary, how='left')
    
    if 'dessert_incidence' in data:
        dessert_summary = data['dessert_incidence'].groupby('location_id')['dessert_incidence'].mean()
        location_summary = location_summary.join(dessert_summary, how='left')
    
    return location_summary.reset_index()

def create_metrics_dashboard(data, selected_location):
    """Create the main metrics dashboard"""
    
    # Calculate system metrics
    system_metrics = calculate_metrics(data)
    
    # Get location performance
    location_perf = get_location_performance(data, selected_location)
    
    if len(location_perf) == 0:
        st.error("No data found for selected location")
        return
    
    # Create metric cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if selected_location == 'All Locations':
            avg_check = system_metrics.get('system_avg_check', 0)
            st.metric(
                "System Average Check", 
                f"${avg_check:.2f}",
                help="Average check across all locations"
            )
        else:
            location_avg = location_perf['average_check'].iloc[0] if len(location_perf) > 0 else 0
            system_avg = system_metrics.get('system_avg_check', 0)
            delta = ((location_avg - system_avg) / system_avg * 100) if system_avg > 0 else 0
            st.metric(
                "Average Check",
                f"${location_avg:.2f}",
                f"{delta:+.1f}% vs system",
                help="Flash adjusted sales divided by transactions"
            )
    
    with col2:
        if 'beverage_incidence' in location_perf.columns:
            if selected_location == 'All Locations':
                bev_inc = system_metrics.get('system_bev_incidence', 0)
                st.metric(
                    "System Beverage Incidence",
                    f"{bev_inc:.1%}",
                    help="Beverage items divided by entrée items"
                )
            else:
                location_bev = location_perf['beverage_incidence'].iloc[0] if len(location_perf) > 0 else 0
                system_bev = system_metrics.get('system_bev_incidence', 0)
                delta = ((location_bev - system_bev) / system_bev * 100) if system_bev > 0 else 0
                st.metric(
                    "Beverage Incidence",
                    f"{location_bev:.1%}",
                    f"{delta:+.1f}% vs system",
                    help="Beverage items divided by entrée items"
                )
    
    with col3:
        if 'dessert_incidence' in location_perf.columns:
            if selected_location == 'All Locations':
                dessert_inc = system_metrics.get('system_dessert_incidence', 0)
                st.metric(
                    "System Dessert Incidence", 
                    f"{dessert_inc:.1%}",
                    help="Dessert items divided by transactions"
                )
            else:
                location_dessert = location_perf['dessert_incidence'].iloc[0] if len(location_perf) > 0 else 0
                system_dessert = system_metrics.get('system_dessert_incidence', 0)
                delta = ((location_dessert - system_dessert) / system_dessert * 100) if system_dessert > 0 else 0
                st.metric(
                    "Dessert Incidence",
                    f"{location_dessert:.1%}",
                    f"{delta:+.1f}% vs system",
                    help="Dessert items divided by transactions"
                )
    
    with col4:
        if len(location_perf) > 0:
            total_sales = location_perf['Net Sales'].sum()
            total_transactions = location_perf['Transactions'].sum()
            st.metric(
                "Total Sales",
                f"${total_sales:,.0f}",
                help=f"{total_transactions:,} transactions"
            )

def create_location_comparison_chart(data):
    """Create a comparison chart of all locations"""
    
    location_perf = get_location_performance(data)
    
    if len(location_perf) == 0:
        st.warning("No location data available for comparison")
        return
    
    # Sort by average check for better visualization
    location_perf = location_perf.sort_values('average_check', ascending=False)
    
    # Create bar chart
    fig = px.bar(
        location_perf.head(20),  # Top 20 locations
        x='location_id',
        y='average_check',
        title="Average Check by Location (Top 20)",
        color='average_check',
        color_continuous_scale=['#D0D1D8', '#00A8BF', '#007784'],
        labels={'average_check': 'Average Check ($)', 'location_id': 'Location'}
    )
    
    fig.update_layout(
        title_font_color=GULFSTREAM_TEAL,
        title_font_size=20,
        showlegend=False,
        height=500,
        xaxis_tickangle=45
    )
    
    st.plotly_chart(fig, use_container_width=True)

def create_beverage_incidence_scatter(data):
    """Create scatter plot of average check vs beverage incidence"""
    
    location_perf = get_location_performance(data)
    
    if len(location_perf) == 0 or 'beverage_incidence' not in location_perf.columns:
        st.warning("No data available for beverage incidence analysis")
        return
    
    # Remove any rows with missing data
    plot_data = location_perf.dropna(subset=['average_check', 'beverage_incidence'])
    
    fig = px.scatter(
        plot_data,
        x='beverage_incidence',
        y='average_check',
        hover_data=['location_id', 'Net Sales'],
        title="Average Check vs Beverage Incidence",
        labels={
            'beverage_incidence': 'Beverage Incidence (%)',
            'average_check': 'Average Check ($)',
            'location_id': 'Location'
        },
        color='average_check',
        color_continuous_scale=['#D0D1D8', '#00A8BF', '#007784']
    )
    
    fig.update_layout(
        title_font_color=GULFSTREAM_TEAL,
        title_font_size=20,
        height=500
    )
    
    # Format x-axis as percentage
    fig.update_xaxes(tickformat='.1%')
    
    st.plotly_chart(fig, use_container_width=True)

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown("# Hawaiian Bros Analytics Hub")
    st.markdown("*Real-time insights into sales performance, channel mix, and operational metrics*")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.title("🏝️ Hawaiian Bros")
    st.sidebar.markdown("### Analytics Hub")
    
    # Load data
    sheet_url = "https://docs.google.com/spreadsheets/d/1lkI-SBV6wNQGd2CxkoZk36xlWz6CaRt8/edit?usp=sharing&ouid=109658744598016199356&rtpof=true&sd=true"
    
    st.sidebar.markdown("### Data Connection")
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    with st.spinner("Loading data from Google Sheets..."):
        data = load_data_from_sheets(sheet_url)
    
    if not data:
        st.error("Could not load data. Please check the Google Sheets connection.")
        st.stop()
    
    # Location selector
    st.sidebar.markdown("### Location Filter")
    
    # Get available locations
    if 'locations' in data and len(data['locations']) > 0:
        locations = ['All Locations'] + sorted(data['locations']['location_id'].unique().tolist())
    else:
        # Fallback to sales metrics locations
        if 'sales_metrics' in data:
            locations = ['All Locations'] + sorted(data['sales_metrics']['location_id'].unique().tolist())
        else:
            locations = ['All Locations']
    
    selected_location = st.sidebar.selectbox(
        "Choose Location",
        options=locations,
        help="Select a specific location for detailed analysis"
    )
    
    # Query type selector
    st.sidebar.markdown("### Analysis Type")
    query_type = st.sidebar.radio(
        "What would you like to analyze?",
        [
            "🎯 Location Deep Dive",
            "📊 Location Comparison", 
            "🥤 Beverage Performance",
            "📈 Operational Metrics"
        ]
    )
    
    # Main content based on selection
    if query_type == "🎯 Location Deep Dive":
        st.header(f"Deep Dive: {selected_location}")
        create_metrics_dashboard(data, selected_location)
        
        if selected_location != 'All Locations' and 'sales_metrics' in data:
            st.subheader("Weekly Performance Trend")
            
            # Get weekly data for the selected location
            location_weekly = data['sales_metrics'][
                data['sales_metrics']['location_id'] == selected_location
            ].copy()
            
            if len(location_weekly) > 0:
                fig = px.line(
                    location_weekly,
                    x='week_num',
                    y='average_check',
                    title=f"Average Check Trend - {selected_location}",
                    labels={'week_num': 'Week', 'average_check': 'Average Check ($)'}
                )
                
                fig.update_traces(line_color=AQUARIUM_TEAL, line_width=3)
                fig.update_layout(
                    title_font_color=GULFSTREAM_TEAL,
                    title_font_size=18,
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    elif query_type == "📊 Location Comparison":
        st.header("Location Performance Comparison")
        create_location_comparison_chart(data)
        
        # Top performers table
        st.subheader("Top Performers")
        location_perf = get_location_performance(data)
        if len(location_perf) > 0:
            top_performers = location_perf.sort_values('average_check', ascending=False).head(10)
            
            # Format for display
            display_df = top_performers.copy()
            display_df['average_check'] = display_df['average_check'].apply(lambda x: f"${x:.2f}")
            display_df['Net Sales'] = display_df['Net Sales'].apply(lambda x: f"${x:,.0f}")
            display_df['Transactions'] = display_df['Transactions'].apply(lambda x: f"{x:,.0f}")
            
            if 'beverage_incidence' in display_df.columns:
                display_df['beverage_incidence'] = display_df['beverage_incidence'].apply(lambda x: f"{x:.1%}" if pd.notna(x) else "N/A")
            
            st.dataframe(display_df, use_container_width=True)
    
    elif query_type == "🥤 Beverage Performance":
        st.header("Beverage Incidence Analysis") 
        create_beverage_incidence_scatter(data)
        
        # Beverage leaders
        st.subheader("Beverage Incidence Leaders")
        location_perf = get_location_performance(data)
        if len(location_perf) > 0 and 'beverage_incidence' in location_perf.columns:
            bev_leaders = location_perf.dropna(subset=['beverage_incidence']).sort_values('beverage_incidence', ascending=False).head(10)
            
            display_df = bev_leaders[['location_id', 'beverage_incidence', 'average_check']].copy()
            display_df['beverage_incidence'] = display_df['beverage_incidence'].apply(lambda x: f"{x:.1%}")
            display_df['average_check'] = display_df['average_check'].apply(lambda x: f"${x:.2f}")
            
            st.dataframe(display_df, use_container_width=True)
    
    elif query_type == "📈 Operational Metrics":
        st.header("Operational Metrics Overview")
        create_metrics_dashboard(data, 'All Locations')
        
        # Metrics distribution
        col1, col2 = st.columns(2)
        
        location_perf = get_location_performance(data)
        
        with col1:
            if len(location_perf) > 0:
                fig = px.histogram(
                    location_perf,
                    x='average_check',
                    title="Average Check Distribution",
                    nbins=20,
                    labels={'average_check': 'Average Check ($)'}
                )
                fig.update_traces(marker_color=AQUARIUM_TEAL)
                fig.update_layout(title_font_color=GULFSTREAM_TEAL, height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if 'beverage_incidence' in location_perf.columns:
                valid_bev_data = location_perf.dropna(subset=['beverage_incidence'])
                if len(valid_bev_data) > 0:
                    fig = px.histogram(
                        valid_bev_data,
                        x='beverage_incidence',
                        title="Beverage Incidence Distribution", 
                        nbins=20,
                        labels={'beverage_incidence': 'Beverage Incidence (%)'}
                    )
                    fig.update_traces(marker_color=OBSTINATE_ORANGE)
                    fig.update_layout(title_font_color=GULFSTREAM_TEAL, height=400)
                    fig.update_xaxes(tickformat='.1%')
                    st.plotly_chart(fig, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "🏝️ **Hawaiian Bros Analytics Hub** | Built with real operational data | "
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

if __name__ == "__main__":
    main()
