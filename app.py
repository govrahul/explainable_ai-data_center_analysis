import os
import streamlit as st
import pandas as pd
import plotly.express as px

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Responsible AI Infrastructure Footprint - Home",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling for sleek dark mode polish
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #f0f2f6; }
    .hero-title { font-size: 2.5rem; font-weight: 800; color: #f0f2f6; margin-bottom: 0px; }
    .hero-subtitle { font-size: 1.2rem; color: #9ca3af; margin-bottom: 2rem; }
    .card { background-color: #1f2937; color: #f9fafb; padding: 1.5rem; border-radius: 0.75rem; border: 1px solid #374151; margin-bottom: 1rem; }
    .card h4, .card p { color: #f9fafb; }
    </style>
""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE MANAGEMENT
# ============================================================
if 'page' not in st.session_state:
    st.session_state.page = 'Home'

page_order = ('Home', 'Context', 'Map', 'Findings', 'Limitations')
page_navigation = (
    ('Home', '1. Overview'),
    ('Context', '2. Context & Controversy'),
    ('Map', '3. Interactive Footprint Map'),
    ('Findings', '4. Findings & Portfolio'),
    ('Limitations', '5. Methodology & Limitations'),
)
if 'max_page_reached' not in st.session_state:
    st.session_state.max_page_reached = page_order.index(st.session_state.page)
if 'exploration_complete' not in st.session_state:
    st.session_state.exploration_complete = st.session_state.page == 'Findings'

def navigate_to(page_name):
    page_index = page_order.index(page_name)
    if page_index > st.session_state.max_page_reached + 1:
        return

    st.session_state.page = page_name
    st.session_state.max_page_reached = max(
        st.session_state.max_page_reached, page_index
    )
    if page_name == 'Findings':
        st.session_state.exploration_complete = True

# ============================================================
# DATA LOADER
# ============================================================
@st.cache_data
def load_data():
    path = 'Data/master_dataset.csv'
    if os.path.exists(path):
        return pd.read_csv(path)
    else:
        st.error(f"Data file not found at {path}. Please ensure the file exists.")
        return pd.DataFrame()

df = load_data()

# ============================================================
# SIDEBAR NAVIGATION & PROGRESS
# ============================================================
with st.sidebar:
    st.title("Navigation")

    for page_name, label in page_navigation:
        page_index = page_order.index(page_name)
        if st.button(
            label,
            key=f"nav_{page_name}",
            use_container_width=True,
            type="primary" if st.session_state.page == page_name else "secondary",
            disabled=(
                not st.session_state.exploration_complete
                and page_index > st.session_state.max_page_reached
            )
        ):
            navigate_to(page_name)
            st.rerun()
            
    st.markdown("---")
    st.markdown("### Project Stack")
    st.markdown("""
        * **Backend:** Python / Pandas 
        * **Geospatial:** Census & eGRID 
        * **Frontend:** Streamlit & Plotly
    """)

# ============================================================
# PAGE 1: HOME PAGE CONTENT
# ============================================================
if st.session_state.page == 'Home':
    st.markdown('### Responsible AI Infrastructure Footprint')
    st.markdown('<p class="hero-subtitle">Evaluating the hidden environmental, water, and socioeconomic trade-offs of generative AI data centers across the United States.</p>', unsafe_allow_html=True)
    
    # Executive KPI Summary Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Facilities", f"{len(df):,}")
    with col2:
        total_mw = df['est_capacity'].sum()
        st.metric("Total IT Capacity (Created and Planned)", f"{total_mw:,.0f} MW")
    with col3:
        total_co2_tons = (
            (df['capacityMw_operational'].fillna(0) * 8760 * 0.85 * df['grid_lbs_co2_per_mwh']) / 2000.0
        ).sum()
        st.metric("Est. Annual CO₂", f"{total_co2_tons:,.0f} Tons")
    with col4:
        st.metric("Census Counties Mapped", f"{df['county_fips'].nunique():,}")
        
    st.markdown("---")
    
    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.markdown("### The Mission")
        st.markdown("""
        The explosive growth of Large Language Models and generative AI infrastructure is straining local power grids, accelerating water consumption in drought-prone regions, and reshaping communities. 
        
        This dashboard bridges facility-level engineering data with **U.S. Census Bureau socioeconomic indicators**, **EPA eGRID carbon intensities**, and **U.S. Drought Monitor risk tiers** to give researchers, policymakers, and communities a clear picture of AI's physical footprint.
        """)
        
        # Placeholder transition for next page (to be unlocked in step 2)
        if st.button("Begin Guided Exploration ➔", type="primary", use_container_width=True):
            navigate_to('Context')
            st.rerun()
            
    with col_r:
        st.markdown("### Key Data Sources")
        st.markdown("""
        * **US Census ACS (2024):** Tract/County socioeconomics
        * **U.S. Drought Monitor:** County-level water stress
        * **EPA eGRID:** Grid emissions factors
        * **Compute Atlas:** Facility coordinates & capacity
        """)

# ============================================================
# PAGE 2: CONTEXT & CONTROVERSY CONTENT
# ============================================================
elif st.session_state.page == 'Context':
    st.markdown("# The Context & Controversy")
    st.markdown("Understanding why data center siting has become one of the most contentious infrastructure debates of the decade.")
    
    tab1, tab2, tab3 = st.tabs(["⚡ Power & Carbon", "💧 Water Stress", "⚖️ Environmental Justice"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### The Energy Wall")
            st.markdown("""
            Large AI data center installations can require **hundreds of megawatts** of electricity, comparable to the power demand of tens of thousands of homes. Actual demand varies with facility size, computing hardware, and cooling requirements. 
            
            Because AI training requires 24/7 continuous baseload power, tech companies are increasingly seeking direct deals with nuclear plants or extending the lifespan of coal and natural gas facilities, directly impacting state carbon reduction goals.
            """)
        with col2:
            st.info("**Key Metric:** Data centers could account for roughly 9%–12% of U.S. electricity consumption by 2030, with projections varying by study and assumptions. A 2026 Lawrence Berkeley National Laboratory report estimates a central scenario of 11.8%.")
            
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### The Hidden Water Footprint")
            st.markdown("""
            Servers generate immense heat, requiring millions of gallons of water daily for evaporative cooling towers. 
            
            When facilities are sited in water-stressed counties (such as parts of Arizona, Texas, or drought-affected agricultural corridors), heavy industrial water usage competes directly with municipal and agricultural needs.
            """)
        with col2:
            st.warning("**Risk Factor:** A substantial share of data center capacity may be located in areas exposed to seasonal drought risk. This can exacerbate local water scarcity, causing larger impacts on the community and environment.")
            
    with tab3:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Socioeconomic Equity")
            st.markdown("""
            Industrial zoning for data centers often clusters near major fiber trunk lines and cheap land—frequently intersecting with lower-income census tracts or communities of color. 
            
            While facilities bring local tax revenue and construction jobs, permanent high-tech operational staffing is low (often 30-50 jobs per facility), raising questions about local distribution of benefits versus environmental burdens.
            """)
        with col2:
            st.success("**Economic Multiplier:** Modeled local job creation averages ~3.0 indirect/induced jobs per direct operational position.")

    st.markdown("---")
    col_back, col_next = st.columns([1, 1])
    with col_back:
        if st.button("⬅ Back to Home"):
            navigate_to('Home')
            st.rerun()
    with col_next:
        if st.button("Explore Interactive Map ➔", type="primary"):
            navigate_to('Map')
            st.rerun()

# ============================================================
# PAGE 3: INTERACTIVE MAP CONTENT
# ============================================================
elif st.session_state.page == 'Map':
    st.markdown("# Interactive Facility Footprint Map")
    st.markdown("Inspect individual data center facilities, filter by state or capacity, and view matched environmental and socioeconomic metrics.")
    
    st.markdown("### Map Filters")
    state_col = 'state_abbr' if 'state_abbr' in df.columns else 'location_state'
    available_states = sorted(df[state_col].dropna().unique().tolist()) if state_col in df.columns else []
    cap_col = 'est_capacity' if 'est_capacity' in df.columns else 'capacityMw_operational'
    max_cap = int(df[cap_col].max()) if cap_col in df.columns and not df[cap_col].dropna().empty else 200

    filter_col_state, filter_col_capacity, filter_col_metric = st.columns([1, 1, 2])
    with filter_col_state:
        selected_state = st.selectbox("Filter by State", ["ALL"] + available_states)
    with filter_col_capacity:
        min_cap = st.slider("Minimum Capacity (MW)", 0, max(max_cap, 10), 0)
    with filter_col_metric:
        metric_options = (
            "Capacity (MW)",
            "Carbon Intensity (lbs CO₂/MWh)",
            "Drought Risk (DSCI)",
            "Median Household Income ($)",
        )
        selected_metric = st.selectbox(
            "Color map by",
            options=list(metric_options),
            key="map_metric"
        )
    
    # Filter dataframe
    filtered_df = df.copy()
    filtered_df[cap_col] = pd.to_numeric(filtered_df[cap_col], errors='coerce').fillna(10.0)
    if selected_state != "ALL" and state_col in filtered_df.columns:
        filtered_df = filtered_df[filtered_df[state_col] == selected_state]
    if cap_col in filtered_df.columns:
        filtered_df = filtered_df[filtered_df[cap_col].fillna(0) >= min_cap]

    col_map, col_card = st.columns([2, 1])

    lat_col = 'location_lat' if 'location_lat' in filtered_df.columns else 'latitude'
    lon_col = 'location_lon' if 'location_lon' in filtered_df.columns else 'longitude'
    name_col = 'name' if 'name' in filtered_df.columns else 'facility_name'
    map_df = filtered_df.copy()
    if lat_col in map_df.columns and lon_col in map_df.columns:
        map_df[lat_col] = pd.to_numeric(map_df[lat_col], errors='coerce')
        map_df[lon_col] = pd.to_numeric(map_df[lon_col], errors='coerce')
        map_df = map_df.dropna(subset=[lat_col, lon_col])

    metric_col = "_map_metric_value"
    if selected_metric == "Capacity (MW)":
        map_df[metric_col] = pd.to_numeric(map_df[cap_col], errors="coerce")
    elif selected_metric == "Carbon Intensity (lbs CO₂/MWh)":
        map_df[metric_col] = pd.to_numeric(
            map_df.get("grid_lbs_co2_per_mwh"), errors="coerce"
        )
    elif selected_metric == "Drought Risk (DSCI)":
        drought_weights = {
            "drought_d0": 1,
            "drought_d1": 2,
            "drought_d2": 3,
            "drought_d3": 4,
            "drought_d4": 5,
        }
        drought_columns = [
            column for column in drought_weights if column in map_df.columns
        ]
        if drought_columns:
            drought_values = map_df[drought_columns].apply(pd.to_numeric, errors="coerce")
            weights = pd.Series(drought_weights, dtype=float)
            map_df[metric_col] = drought_values.mul(weights[drought_columns]).sum(
                axis=1, min_count=1
            )
        else:
            map_df[metric_col] = float("nan")
    else:
        income_values = pd.to_numeric(
            map_df.get("median_household_income"), errors="coerce"
        )
        map_df[metric_col] = income_values.where(income_values >= 0)

    map_df["_audit_row_id"] = range(len(map_df))
    map_facility_ids = dict(zip(map_df["_audit_row_id"], map_df.index))
    
    with col_map:
        if not map_df.empty and lat_col in map_df.columns and lon_col in map_df.columns:
            metric_values_available = map_df[metric_col].notna().any()
            if not metric_values_available:
                st.warning(f"No {selected_metric} values are available for the current filters.")
            color_scale = [
                [0.0, "#dc2626"],
                [0.5, "#f3f4f6"],
                [1.0, "#2563eb"],
            ] if selected_metric == "Median Household Income ($)" else [
                [0.0, "#2563eb"],
                [0.5, "#f3f4f6"],
                [1.0, "#dc2626"],
            ]
            coloraxis_config = {
                "colorbar": {"title": {"text": selected_metric}}
            }
            if selected_metric == "Median Household Income ($)" and metric_values_available:
                coloraxis_config.update(
                    cmin=50_000,
                    cmax=100_000
                )
            fig = px.scatter_map(
                map_df,
                lat=lat_col,
                lon=lon_col,
                size=cap_col,
                color=metric_col if metric_values_available else None,
                color_continuous_scale=color_scale,
                size_max=36,
                hover_name=name_col if name_col in filtered_df.columns else filtered_df.index,
                hover_data={metric_col: ":,.1f"} if metric_values_available else None,
                custom_data=["_audit_row_id"],
                labels={metric_col: selected_metric},
                zoom=3,
                height=550
            )
            fig.update_layout(
                map_style="open-street-map",
                map={
                    "center": {"lat": 39.5, "lon": -98.35},
                    "zoom": 3,
                },
                margin={"r":0,"t":0,"l":0,"b":0},
                coloraxis=coloraxis_config
            )
            
            # Capture click events on map points
            event = st.plotly_chart(
                fig,
                width="stretch",
                on_select="rerun",
                selection_mode="points",
                key=f"facility_map_{selected_state}_{min_cap}_{selected_metric}"
            )
        else:
            st.warning("No facility coordinates available for current filter selection.")
            event = None
            
    with col_card:
        st.markdown("### Facility Audit Card")
        if not filtered_df.empty:
            facility_ids = filtered_df.index.tolist()
            facility_labels = {
                facility_id: str(filtered_df.loc[facility_id, name_col]) if name_col in filtered_df.columns else str(facility_id)
                for facility_id in facility_ids
            }

            selection = event.get("selection", {}) if event else {}
            selected_points = selection.get("points", [])
            map_facility_id = None
            if selected_points:
                selected_point = selected_points[0]
                point_custom_data = selected_point.get("customdata")
                if isinstance(point_custom_data, (list, tuple)) and point_custom_data:
                    row_id = pd.to_numeric(point_custom_data[0], errors="coerce")
                    if pd.notna(row_id) and float(row_id).is_integer():
                        map_facility_id = map_facility_ids.get(int(row_id))

                if map_facility_id is None:
                    point_index = selected_point.get("point_index")
                    if isinstance(point_index, int) and 0 <= point_index < len(map_df):
                        map_facility_id = map_df.index[point_index]

            last_map_facility_id = st.session_state.get("_last_map_facility_id")
            if map_facility_id in facility_ids:
                if map_facility_id != last_map_facility_id:
                    st.session_state["audit_facility_id"] = map_facility_id
                    st.session_state["_last_map_facility_id"] = map_facility_id
            elif map_facility_id is None:
                st.session_state["_last_map_facility_id"] = None
            else:
                map_facility_id = None
                st.session_state["_last_map_facility_id"] = None

            if st.session_state.get("audit_facility_id") not in facility_ids:
                st.session_state["audit_facility_id"] = facility_ids[0]

            selected_facility_id = st.selectbox(
                "Select Facility",
                facility_ids,
                format_func=lambda facility_id: facility_labels.get(facility_id, str(facility_id)),
                key="audit_facility_id"
            )
            fac_row = filtered_df.loc[selected_facility_id]
            
            fac_name = fac_row.get(name_col, 'Facility')
            status = fac_row.get('status', 'N/A')
            fac_state = fac_row.get(state_col, 'N/A')
            fac_cap = fac_row.get(cap_col, 'N/A')
            co2_lbs = fac_row.get('grid_annual_co2_lbs', 0)
            co2_tons = (co2_lbs / 2000.0) if pd.notna(co2_lbs) else 'N/A'
            drought_val = fac_row.get('drought_d1', 'N/A')
            med_inc = fac_row.get('median_household_income', 'N/A')
            jobs = fac_row.get('est_total_operational_jobs', 'N/A')
            
            st.markdown(f"""
            <div class="card">
                <h4><b>{fac_name}</b></h4>
                <p><b>Status:</b> {status}</p>
                <p><b>State:</b> {fac_state}</p>
                <p><b>Capacity:</b> {fac_cap} MW</p>
                <p><b>Est. Annual CO₂:</b> {f"{co2_tons:,.0f} Tons" if isinstance(co2_tons, (int, float)) else 'N/A'}</p>
                <p><b>Drought Stress Index:</b> {drought_val}</p>
                <p><b>Host Median Income:</b> {f"${med_inc:,.0f}" if isinstance(med_inc, (int, float)) else 'N/A'}</p>
                <p><b>Est. Total Jobs Created:</b> {jobs}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No facilities match the current filter criteria.")

    st.markdown("---")
    col_back, col_next = st.columns([1, 1])
    with col_back:
        if st.button("⬅ Back to Context"):
            navigate_to('Context')
            st.rerun()
    with col_next:
        if st.button("Explore Key Findings ➔"):
            navigate_to('Findings')
            st.rerun()

# ============================================================
# PAGE 4: FINDINGS & PORTFOLIO
# ============================================================
elif st.session_state.page == 'Findings':
    st.markdown("# Key Findings & Strategic Next Steps")
    st.markdown("Summary takeaways from our multi-layered national infrastructure audit.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        ### Key Analytical Takeaways
        1. **Concentration of Capacity:** Many data centers are located very close to each other, raising concerns about local grid stress and community impacts.
        2. **Water Stress**: Few data centers are located in water-stressed regions, but they could have lasting impacts on local water availability if not managed properly.
        3. **Socioeconomic Disparities:** A significant number of data centers are located in counties with lower median household incomes, raising questions about equitable distribution of benefits and burdens.
        """)
    with col2:
        st.markdown("""
        ### Policy & Engineering Recommendations
        1. **Mandatory PUE & WUE Transparency:** Require public reporting of Power Usage Effectiveness and Water Usage Effectiveness for all subsidized data centers.
        2. **Community Benefit Agreements (CBAs):** Direct infrastructure tax revenues toward local educational and water conservation funds in host census tracts.
        3. **Community Engagement:** Establish ways for local communities to have a voice in data center decisions, ensuring their concerns are heard and truly taken into account.
        """)
        
    st.markdown("---")
    
    # Dataset Download
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Master Responsible AI Footprint Dataset (CSV)",
        data=csv_data,
        file_name="master_dataset.csv",
        mime="text/csv",
        type="primary"
    )
    
    st.markdown("---")
    st.markdown("### Connect & Collaborators")
    col_gh, col_li = st.columns(2)
    with col_gh:
        st.markdown("[![GitHub](https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github)](https://github.com/govrahul/explainable_ai-data_center_analysis)")
    with col_li:
        st.markdown("[![LinkedIn](https://img.shields.io/badge/LinkedIn-Profile-0A66C2?style=for-the-badge&logo=linkedin)](https://linkedin.com/govrahul)")

    with st.expander("Full Methodology & Limitations Report"):
        st.markdown("""
        This report details the data assumptions, estimation models, and structural constraints of this infrastructure audit. It includes information on emissions estimation, drought and water stress metrics, economic and job creation estimates, and spatial join precision.
        """)
        if st.button("View Full Methodology & Limitations"):
            navigate_to('Limitations')
            st.rerun()

# ============================================================
# PAGE 5: METHODOLOGY & LIMITATIONS CONTENT
# ============================================================
elif st.session_state.page == 'Limitations':
    st.markdown("# ℹ️ Methodology & Analytical Limitations")
    st.markdown("Transparency report detailing data assumptions, estimation models, and structural constraints of this infrastructure audit.")
    
    st.markdown("---")
    
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("### ⚡ 1. Emissions Estimation Model")
        st.markdown("""
        * **Methodology:** Annual carbon emissions are modeled by scaling facility operational capacity (`capacityMw_operational`) against regional grid carbon intensity factors ($\text{lbs } CO_2/\text{MWh}$) sourced from the **EPA eGRID database**.
        * **Limitations:** 
          * Assumes a generalized 24/7 continuous baseload capacity factor rather than real-time dynamic server utilization or actual power purchase agreements (PPAs) involving off-site renewables or nuclear allocation.
          * Does not account for scope 3 embodied carbon (manufacturing and chip fabrication supply chains).
        """)
        
        st.markdown("### 💧 2. Drought & Water Stress Metric")
        st.markdown("""
        * **Methodology:** County-level drought exposure is evaluated using the **U.S. Drought Monitor (USDM)** categorical percentages aggregated into the standard Drought Severity and Coverage Index (DSCI).
        * **Limitations:** 
          * Drought indices reflect regional climate and meteorological drought rather than industrial municipal water rights allocations or closed-loop cooling recycling rates.
        """)
        
    with col_r:
        st.markdown("### 🧑‍💼 3. Economic & Job Creation Estimates")
        st.markdown("""
        * **Methodology:** Operational and economic multipliers are derived from standard regional economic development benchmarks (~0.4 direct operational jobs per MW, scaled by a 3.0 total employment multiplier for indirect and induced local impact).
        * **Limitations:** 
          * These are *modeled regional projections* rather than verified corporate payroll audits. Actual local hiring varies significantly based on automation level, cloud provider outsourcing, and local labor market availability.
        """)
        
        st.markdown("### 🗺️ 4. Spatial Join & FIPS Precision")
        st.markdown("""
        * **Methodology:** Facilities (Compute Atlas coordinates) are spatially mapped and joined to county-level drought and socioeconomic tables using 5-digit FIPS codes.
        * **Limitations:** 
          * Large rural counties or sprawling facility footprints can occasionally span multiple census tracts, leading to localized demographic blurring.
        """)

    st.markdown("---")
    
    col_back, col_home = st.columns(2)
    with col_back:
        if st.button("⬅ Back to Findings"):
            navigate_to('Findings')
            st.rerun()
    with col_home:
        if st.button("🏠 Return to Home"):
            navigate_to('Home')
            st.rerun()