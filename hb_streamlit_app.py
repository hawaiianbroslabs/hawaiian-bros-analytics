import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

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
def load_data_from_sheets():
    """Load data from Google Sheets using the correct sheet ID"""
    try:
        # Extract the actual sheet ID (the part we need)
        sheet_id = "1lkI-SBV6wNQGd2CxkoZk36xlWz6CaRt8"
        
        # Use the exact gid values from Matt's Google Sheet
        base_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid="
        
        data = {}
        
        # Exact tab IDs from the Google Sheet
        sheet_configs = [
            ("fact_table", "1820400707"),
            ("locations", "775063354"), 
            ("items", "844699807"),
            ("sales_metrics", "1570627213"),
            ("beverage_incidence", "42742573"),
            ("dessert_incidence", "1530013637"),
            ("entree_size_mix", "1655205958"),
            ("summary", "625117969")
        ]
        
        for sheet_name, gid in sheet_configs:
            try:
                url = f"{base_url}{gid}"
                df = pd.read_csv(url)
                
                if len(df) > 0:  # Only keep sheets with data
                    data[sheet_name] = df
                    st.sidebar.success(f"✅ Loaded {sheet_name}: {len(df)} rows")
                
            except Exception as e:
                st.sidebar.warning(f"⚠️ Could not load {sheet_name}: {str(e)[:50]}...")
        
        # If we got some data, return it
        if data:
            return data
        else:
            st.error("No sheets could be loaded. Check Google Sheets permissions.")
            return {}
        
    except Exception as e:
        st.error(f"Failed to load data: {str(e)}")
        return {}

def create_sample_data():
    """Create sample data if Google Sheets fails to load"""
    st.warning("Using sample data - Google Sheets connection failed")
    
    # Create sample location performance data
    locations = [
        "HB0001_Belton MO", "HB0013_Allen TX", "HB0014_Fort Worth TX Alliance", 
        "HB0017_Fort Worth TX Hulen", "HB0041_Live Oak TX", "HB0016_Denton TX",
        "HB0022_Dallas TX", "HB0036_Houston TX", "HB0015_Hurst TX"
    ]
    
    sample_data = []
    for i, location in enumerate(locations):
        sample_data.append({
            'location_id': location,
            'Net Sales': np.random.uniform(35000, 75000),
            'Transactions': np.random.uniform(1500, 3500),
            'average_check': np.random.uniform(19.50, 24.50),
            'beverage_incidence': np.random.uniform(0.65, 0.85),
            'dessert_incidence': np.random.uniform(0.12, 0.28)
        })
    
    return {'location_performance': pd.DataFrame(sample_data)}

def calculate_metrics(data):
    """Calculate key operational metrics from the loaded data"""
    
    if 'sales_metrics' in data:
        sales_df = data['sales_metrics']
        system_avg_check = sales_df['average_check'].mean() if 'average_check' in sales_df.columns else 21.50
    else:
        system_avg_check = 21.50
    
    if 'beverage_incidence' in data:
        bev_df = data['beverage_incidence']
        system_bev_inc = bev_df['beverage_incidence'].mean() if 'beverage_incidence' in bev_df.columns else 0.75
    else:
        system_bev_inc = 0.75
    
    if 'dessert_incidence' in data:
        dessert_df = data['dessert_incidence']
        system_dessert_inc = dessert_df['dessert_incidence'].mean() if 'dessert_incidence' in dessert_df.columns else 0.18
    else:
        system_dessert_inc = 0.18
    
    return {
        'system_avg_check': system_avg_check,
        'system_bev_incidence': system_bev_inc,
        'system_dessert_incidence': system_dessert_inc
    }

def get_location_performance(data, location_id=None):
    """Get performance metrics for locations"""
    
    # Try different data sources
    if 'location_performance' in data:
        df = data['location_performance']
    elif 'sales_metrics' in data:
        df = data['sales_metrics']
    else:
        # Use sample data
        return create_sample_data()['location_performance']
    
    if location_id and location_id != 'All Locations':
        df = df[df['location_id'].str.contains(location_id, na=False)]
    
    return df

def create_metrics_dashboard(data, selected_location):
    """Create the main metrics dashboard"""
    
    system_metrics = calculate_metrics(data)
    location_perf = get_location_performance(data, selected_location)
    
    if len(location_perf) == 0:
        st.error("No data found for selected location")
        return
    
    # Create metric cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if selected_location == 'All Locations':
            avg_check = system_metrics.get('system_avg_check', 21.50)
            st.metric(
                "System Average Check", 
                f"${avg_check:.2f}",
                help="Average check across all locations"
            )
        else:
            location_avg = location_perf['average_check'].iloc[0] if len(location_perf) > 0 else 21.50
            system_avg = system_metrics.get('system_avg_check', 21.50)
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
                bev_inc = system_metrics.get('system_bev_incidence', 0.75)
                st.metric(
                    "System Beverage Incidence",
                    f"{bev_inc:.1%}",
                    help="Beverage items divided by entrée items"
                )
            else:
                location_bev = location_perf['beverage_incidence'].iloc[0] if len(location_perf) > 0 else 0.75
                system_bev = system_metrics.get('system_bev_incidence', 0.75)
                delta = ((location_bev - system_bev) / system_bev * 100) if system_bev > 0 else 0
                st.metric(
                    "Beverage Incidence",
                    f"{location_bev:.1%}",
                    f"{delta:+.1f}% vs system",
                    help="Beverage items divided by entrée items"
                )
        else:
            st.metric("Beverage Incidence", "75.2%", "Sample data")
    
    with col3:
        if 'dessert_incidence' in location_perf.columns:
            if selected_location == 'All Locations':
                dessert_inc = system_metrics.get('system_dessert_incidence', 0.18)
                st.metric(
                    "System Dessert Incidence", 
                    f"{dessert_inc:.1%}",
                    help="Dessert items divided by transactions"
                )
            else:
                location_dessert = location_perf['dessert_incidence'].iloc[0] if len(location_perf) > 0 else 0.18
                system_dessert = system_metrics.get('system_dessert_incidence', 0.18)
                delta = ((location_dessert - system_dessert) / system_dessert * 100) if system_dessert > 0 else 0
                st.metric(
                    "Dessert Incidence",
                    f"{location_dessert:.1%}",
                    f"{delta:+.1f}% vs system",
                    help="Dessert items divided by transactions"
                )
        else:
            st.metric("Dessert Incidence", "18.4%", "Sample data")
    
    with col4:
        if len(location_perf) > 0:
            total_sales = location_perf['Net Sales'].sum() if 'Net Sales' in location_perf.columns else 0
            total_transactions = location_perf['Transactions'].sum() if 'Transactions' in location_perf.columns else 0
            st.metric(
                "Total Sales",
                f"${total_sales:,.0f}",
                help=f"{total_transactions:,} transactions" if total_transactions > 0 else "Sample data"
            )

def create_location_comparison_chart(data):
    """Create a comparison chart of all locations"""
    
    location_perf = get_location_performance(data)
    
    if len(location_perf) == 0:
        st.warning("No location data available")
        return
    
    # Sort by average check
    location_perf = location_perf.sort_values('average_check', ascending=False)
    
    fig = px.bar(
        location_perf.head(15),
        x='location_id',
        y='average_check',
        title="Average Check by Location (Top 15)",
        color='average_check',
        color_continuous_scale=['#D0D1D8', '#00A8BF', '#007784']
    )
    
    fig.update_layout(
        title_font_color=GULFSTREAM_TEAL,
        title_font_size=20,
        showlegend=False,
        height=500,
        xaxis_tickangle=45
    )
    
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
    
    # Data connection section
    st.sidebar.markdown("### Data Connection")
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    # Load data
    with st.spinner("Loading data..."):
        data = load_data_from_sheets()
    
    # If no real data, use sample data
    if not data:
        data = create_sample_data()
    
    # Location selector
    st.sidebar.markdown("### Location Filter")
    
    # Get available locations
    location_perf = get_location_performance(data)
    if len(location_perf) > 0 and 'location_id' in location_perf.columns:
        locations = ['All Locations'] + sorted(location_perf['location_id'].unique().tolist())
    else:
        locations = ['All Locations', 'HB0013_Allen TX', 'HB0014_Fort Worth TX Alliance', 'HB0017_Fort Worth TX Hulen']
    
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
    
    # Main content
    if query_type == "🎯 Location Deep Dive":
        st.header(f"Deep Dive: {selected_location}")
        create_metrics_dashboard(data, selected_location)
    
    elif query_type == "📊 Location Comparison":
        st.header("Location Performance Comparison")
        create_location_comparison_chart(data)
        
        # Top performers table
        st.subheader("Top Performers")
        location_perf = get_location_performance(data)
        if len(location_perf) > 0:
            display_df = location_perf.head(10).copy()
            
            # Format for display
            if 'average_check' in display_df.columns:
                display_df['Average Check'] = display_df['average_check'].apply(lambda x: f"${x:.2f}")
            if 'Net Sales' in display_df.columns:
                display_df['Net Sales'] = display_df['Net Sales'].apply(lambda x: f"${x:,.0f}")
            if 'beverage_incidence' in display_df.columns:
                display_df['Beverage Incidence'] = display_df['beverage_incidence'].apply(lambda x: f"{x:.1%}")
            
            # Select columns to show
            cols_to_show = ['location_id']
            if 'Average Check' in display_df.columns:
                cols_to_show.append('Average Check')
            if 'Net Sales' in display_df.columns:
                cols_to_show.append('Net Sales')
            if 'Beverage Incidence' in display_df.columns:
                cols_to_show.append('Beverage Incidence')
            
            st.dataframe(display_df[cols_to_show], use_container_width=True)
    
    elif query_type == "🥤 Beverage Performance":
        st.header("Beverage Performance Analysis")
        
        location_perf = get_location_performance(data)
        if len(location_perf) > 0 and 'beverage_incidence' in location_perf.columns:
            # Scatter plot
            fig = px.scatter(
                location_perf,
                x='beverage_incidence',
                y='average_check',
                hover_data=['location_id'],
                title="Average Check vs Beverage Incidence",
                color='average_check',
                color_continuous_scale=['#D0D1D8', '#00A8BF', '#007784']
            )
            
            fig.update_layout(
                title_font_color=GULFSTREAM_TEAL,
                height=500
            )
            fig.update_xaxes(tickformat='.1%')
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Beverage incidence data not available")
    
    elif query_type == "📈 Operational Metrics":
        st.header("Operational Metrics Overview")
        create_metrics_dashboard(data, 'All Locations')
        
        location_perf = get_location_performance(data)
        
        if len(location_perf) > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.histogram(
                    location_perf,
                    x='average_check',
                    title="Average Check Distribution",
                    nbins=15
                )
                fig.update_traces(marker_color=AQUARIUM_TEAL)
                fig.update_layout(title_font_color=GULFSTREAM_TEAL, height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                if 'beverage_incidence' in location_perf.columns:
                    fig = px.histogram(
                        location_perf,
                        x='beverage_incidence',
                        title="Beverage Incidence Distribution",
                        nbins=15
                    )
                    fig.update_traces(marker_color=OBSTINATE_ORANGE)
                    fig.update_layout(title_font_color=GULFSTREAM_TEAL, height=400)
                    fig.update_xaxes(tickformat='.1%')
                    st.plotly_chart(fig, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "🏝️ **Hawaiian Bros Analytics Hub** | "
        f"Data status: {'Real data' if data and 'location_performance' not in data else 'Sample data'} | "
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

if __name__ == "__main__":
    main()
