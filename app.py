import streamlit as st
import pandas as pd
import plotly.express as px

# --- Configuration & Data Loading ---
st.set_page_config(page_title="Palo Alto HR Diagnostics", layout="wide")

@st.cache_data
def load_data():
    # Load the dataset generated from the Jupyter notebook phase
    return pd.read_csv("Palo_Alto_Processed.csv")

df = load_data()

# --- Sidebar Controls ---
st.sidebar.header("Diagnostic Filters")
department_filter = st.sidebar.multiselect("Department", options=df['Department'].unique(), default=df['Department'].unique())
role_filter = st.sidebar.multiselect("Job Role", options=df['JobRole'].unique(), default=df['JobRole'].unique())
overtime_toggle = st.sidebar.radio("Overtime Status", options=['All', 'Yes', 'No'])
engagement_threshold = st.sidebar.slider("Engagement Index Threshold", min_value=1.0, max_value=4.0, value=2.5, step=0.1)
tenure_range = st.sidebar.slider("Years at Company", min_value=0, max_value=int(df['YearsAtCompany'].max()), value=(0, 10))

# Apply Filters
filtered_df = df[
    (df['Department'].isin(department_filter)) &
    (df['JobRole'].isin(role_filter)) &
    (df['YearsAtCompany'] >= tenure_range[0]) &
    (df['YearsAtCompany'] <= tenure_range[1])
]

if overtime_toggle != 'All':
    filtered_df = filtered_df[filtered_df['OverTime'] == overtime_toggle]

# --- Main Dashboard Header ---
st.title("Palo Alto Networks: Employee Diagnostic Dashboard")
st.markdown("Early-warning diagnostics for engagement gaps and burnout risks.")

# --- KPIs ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Avg Engagement Index", f"{filtered_df['Engagement_Index'].mean():.2f} / 4.0")
with col2:
    high_risk_count = len(filtered_df[filtered_df['Burnout_Risk'] == 'High'])
    st.metric("High Burnout Risk Employees", high_risk_count)
with col3:
    st.metric("Avg Work-Life Balance", f"{filtered_df['WorkLifeBalance'].mean():.2f} / 4.0")
with col4:
    attrition_rate = (len(filtered_df[filtered_df['Attrition'] == 'Yes']) / len(filtered_df)) * 100 if 'Yes' in filtered_df['Attrition'].values else 0
    st.metric("Cohort Attrition Rate", f"{attrition_rate:.1f}%")

st.divider()

# --- Module Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(["Engagement Overview", "Burnout Risk", "Career Stage Analysis", "Manager Action Panel"])

with tab1:
    st.header("Engagement Health Overview")
    colA, colB = st.columns(2)
    
    with colA:
        # Engagement Distribution
        fig_eng = px.histogram(filtered_df, x="Engagement_Index", nbins=10, 
                               title="Distribution of Engagement Scores",
                               color_discrete_sequence=['#2E86C1'])
        fig_eng.add_vline(x=engagement_threshold, line_dash="dash", line_color="red", annotation_text="Threshold")
        st.plotly_chart(fig_eng, use_container_width=True)
        
    with colB:
        # Satisfaction Dimensions Radar/Bar
        sat_avg = filtered_df[['JobInvolvement', 'JobSatisfaction', 'EnvironmentSatisfaction', 'RelationshipSatisfaction']].mean().reset_index()
        sat_avg.columns = ['Dimension', 'Average Score']
        fig_sat = px.bar(sat_avg, x='Dimension', y='Average Score', range_y=[0,4],
                         title="Average Satisfaction by Dimension", color='Dimension')
        st.plotly_chart(fig_sat, use_container_width=True)

with tab2:
    st.header("Burnout Risk Dashboard")
    colA, colB = st.columns(2)
    
    with colA:
        # Burnout Risk Distribution
        risk_counts = filtered_df['Burnout_Risk'].value_counts().reset_index()
        risk_counts.columns = ['Risk Level', 'Count']
        fig_risk = px.pie(risk_counts, values='Count', names='Risk Level', 
                          title="Burnout Risk Segmentation",
                          color='Risk Level', color_discrete_map={'High':'#E74C3C', 'Medium':'#F39C12', 'Low':'#27AE60'})
        st.plotly_chart(fig_risk, use_container_width=True)
        
    with colB:
        # Workload Stress vs Engagement
        fig_stress = px.box(filtered_df, x="Burnout_Risk", y="Engagement_Index", 
                            title="Engagement Index vs. Burnout Risk Segment",
                            color="Burnout_Risk")
        st.plotly_chart(fig_stress, use_container_width=True)

with tab3:
    st.header("Role & Career Stage Analysis")
    
    # Tenure vs Engagement Trend
    fig_tenure = px.scatter(filtered_df, x="YearsAtCompany", y="Engagement_Index", 
                            color="Department", trendline="lowess",
                            title="Engagement Trends over Company Tenure")
    st.plotly_chart(fig_tenure, use_container_width=True)
    
    # Engagement by Job Role
    role_eng = filtered_df.groupby('JobRole')['Engagement_Index'].mean().reset_index().sort_values('Engagement_Index')
    fig_role = px.bar(role_eng, x="Engagement_Index", y="JobRole", orientation='h',
                      title="Average Engagement by Job Role")
    st.plotly_chart(fig_role, use_container_width=True)

with tab4:
    st.header("Manager Action Panel")
    st.markdown("### ⚠️ Priority Intervention Alerts")
    
    # Filter for employees strictly below the engagement threshold AND at High burnout risk
    at_risk_employees = filtered_df[(filtered_df['Engagement_Index'] < engagement_threshold) & 
                                    (filtered_df['Burnout_Risk'] == 'High')]
    
    if not at_risk_employees.empty:
        st.error(f"Alert: {len(at_risk_employees)} employees identified in the high-risk intervention zone (Low Engagement + High Burnout).")
        # Display actionable columns for managers
        action_df = at_risk_employees[['Department', 'JobRole', 'Engagement_Index', 'WorkLifeBalance', 'OverTime', 'YearsWithCurrManager']]
        st.dataframe(action_df.style.highlight_min(subset=['Engagement_Index', 'WorkLifeBalance'], color='#ffcccc'))
    else:
        st.success("No employees currently fall into the critical intervention zone based on active filters.")
        
    st.markdown("### Recommended Preventive Actions")
    st.info("""
    * **High Overtime + Low WLB:** Immediately audit workload distribution for identified roles.
    * **Low Environment Satisfaction:** Initiate anonymous feedback loops for specific departments.
    * **Tenure Stagnation (3-5 Years):** Review internal mobility and promotion cycles for mid-tenure employees showing engagement dips.
    """)