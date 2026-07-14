import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from solver import BeamSolver

def render_mdm_html_table(spans, res):
    N = len(spans)
    
    # 1. Row 1: Joints (colspans to merge columns by joint)
    joints_row_html = '<tr><th style="background-color: #1e3c72; color: white; border: 1px solid #cbd5e1; padding: 10px; text-align: center;">Joint</th>'
    joints_row_html += '<th style="background-color: #1e3c72; color: white; border: 1px solid #cbd5e1; padding: 10px; text-align: center;" colspan="1">0</th>'
    for j in range(1, N):
        joints_row_html += f'<th style="background-color: #1e3c72; color: white; border: 1px solid #cbd5e1; padding: 10px; text-align: center;" colspan="2">{j}</th>'
    joints_row_html += f'<th style="background-color: #1e3c72; color: white; border: 1px solid #cbd5e1; padding: 10px; text-align: center;" colspan="1">{N}</th>'
    joints_row_html += '</tr>'
    
    # 2. Row 2: Members
    members_row_html = '<tr><td style="font-weight: bold; background-color: #f1f5f9; border: 1px solid #cbd5e1; padding: 10px;">Member</td>'
    members_row_html += '<td style="font-weight: bold; background-color: #f8fafc; border: 1px solid #cbd5e1; padding: 10px; text-align: center;">0-1</td>'
    for j in range(1, N):
        members_row_html += f'<td style="font-weight: bold; background-color: #f8fafc; border: 1px solid #cbd5e1; padding: 10px; text-align: center;">{j}-{j-1}</td>'
        members_row_html += f'<td style="font-weight: bold; background-color: #f8fafc; border: 1px solid #cbd5e1; padding: 10px; text-align: center;">{j}-{j+1}</td>'
    members_row_html += f'<td style="font-weight: bold; background-color: #f8fafc; border: 1px solid #cbd5e1; padding: 10px; text-align: center;">{N}-{N-1}</td>'
    members_row_html += '</tr>'
    
    # 3. Row 3: Distribution Factors
    df_row_html = '<tr><td style="font-weight: bold; background-color: #f1f5f9; border: 1px solid #cbd5e1; padding: 10px;">DF</td>'
    df_row_html += f'<td style="background-color: #f8fafc; border: 1px solid #cbd5e1; padding: 10px; text-align: center;">{res["DF_right"][0]:.3f}</td>'
    for j in range(1, N):
        df_row_html += f'<td style="background-color: #f8fafc; border: 1px solid #cbd5e1; padding: 10px; text-align: center;">{res["DF_left"][j]:.3f}</td>'
        df_row_html += f'<td style="background-color: #f8fafc; border: 1px solid #cbd5e1; padding: 10px; text-align: center;">{res["DF_right"][j]:.3f}</td>'
    df_row_html += f'<td style="background-color: #f8fafc; border: 1px solid #cbd5e1; padding: 10px; text-align: center;">{res["DF_left"][N]:.3f}</td>'
    df_row_html += '</tr>'
    
    # Generate the step rows (FEM, Balances, Carry Overs)
    steps_rows_html = ''
    for idx, step in enumerate(res['steps_log']):
        step_name = step['Step']
        bg_color = "#ffffff" if idx % 2 == 0 else "#f8fafc"
        
        # Style highlighted rows
        weight_style = "font-weight: 600; color: #1e3c72;" if "Initial" in step_name else ""
        
        row_html = f'<tr style="background-color: {bg_color}; {weight_style}">'
        row_html += f'<td style="font-weight: bold; border: 1px solid #cbd5e1; padding: 8px;">{step_name}</td>'
        
        # Column 0: Span 0 Left increment
        row_html += f'<td style="border: 1px solid #cbd5e1; padding: 8px; text-align: center;">{step["M_L_inc"][0]:.3f}</td>'
        # Interior columns
        for i in range(1, N):
            # Span i-1 Right increment
            row_html += f'<td style="border: 1px solid #cbd5e1; padding: 8px; text-align: center;">{step["M_R_inc"][i-1]:.3f}</td>'
            # Span i Left increment
            row_html += f'<td style="border: 1px solid #cbd5e1; padding: 8px; text-align: center;">{step["M_L_inc"][i]:.3f}</td>'
        # Column 2N-1: Span N-1 Right increment
        row_html += f'<td style="border: 1px solid #cbd5e1; padding: 8px; text-align: center;">{step["M_R_inc"][N-1]:.3f}</td>'
        row_html += '</tr>'
        steps_rows_html += row_html
        
    # Final moments row
    final_row_html = '<tr style="font-weight: bold; background-color: #e2e8f0; border-top: 2px solid #94a3b8; border-bottom: 4px double #94a3b8; color: #1e3c72;">'
    final_row_html += '<td style="border: 1px solid #cbd5e1; padding: 10px;">Final Moment</td>'
    final_row_html += f'<td style="border: 1px solid #cbd5e1; padding: 10px; text-align: center;">{res["M_L"][0]:.3f}</td>'
    for i in range(1, N):
        final_row_html += f'<td style="border: 1px solid #cbd5e1; padding: 10px; text-align: center;">{res["M_R"][i-1]:.3f}</td>'
        final_row_html += f'<td style="border: 1px solid #cbd5e1; padding: 10px; text-align: center;">{res["M_L"][i]:.3f}</td>'
    final_row_html += f'<td style="border: 1px solid #cbd5e1; padding: 10px; text-align: center;">{res["M_R"][N-1]:.3f}</td>'
    final_row_html += '</tr>'
    
    # Table template
    table_style = 'width: 100%; border-collapse: collapse; border: 1px solid #cbd5e1; font-family: "Outfit", sans-serif; font-size: 0.95rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 1.5rem;'
    full_table_html = f'<div style="overflow-x: auto;"><table style="{table_style}">'
    full_table_html += joints_row_html
    full_table_html += members_row_html
    full_table_html += df_row_html
    full_table_html += steps_rows_html
    full_table_html += final_row_html
    full_table_html += '</table></div>'
    
    return full_table_html

# Page configuration
st.set_page_config(
    page_title="Hardy Cross Beam Solver",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Premium Custom CSS injection for rich aesthetics
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
    /* Overall page background and styling */
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 40%, #e2e8f0 100%) !important;
    }
    
    /* Glassy Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(248, 250, 252, 0.45) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.3) !important;
    }
    
    /* Font style overrides */
    html, body, [class*="css"], .stButton, .stInput {
        font-family: 'Outfit', sans-serif !important;
    }
    
    /* Gradient Title Card */
    .title-card {
        background: linear-gradient(135deg, rgba(30, 60, 114, 0.95) 0%, rgba(42, 82, 152, 0.95) 100%) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        padding: 2.2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        box-shadow: 0 12px 40px rgba(30, 60, 114, 0.18) !important;
    }
    .title-card h1 {
        margin: 0;
        font-weight: 800;
        font-size: 2.7rem;
        color: #ffffff !important;
        letter-spacing: -0.5px;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .title-card p {
        margin: 0.5rem 0 0 0;
        opacity: 0.95;
        font-size: 1.15rem;
        font-weight: 300;
        letter-spacing: 0.2px;
    }
    
    /* Section headers */
    .section-header {
        font-size: 1.6rem;
        font-weight: 700;
        color: #1e3c72;
        border-bottom: 2px solid rgba(30, 60, 114, 0.15);
        padding-bottom: 0.6rem;
        margin-top: 1.8rem;
        margin-bottom: 1.2rem;
        text-shadow: 0 1px 2px rgba(255,255,255,0.7);
    }
    
    /* Premium Glassmorphism input & display cards */
    .span-card {
        background: rgba(255, 255, 255, 0.55) !important;
        backdrop-filter: blur(12px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(12px) saturate(180%) !important;
        border: 1px solid rgba(255, 255, 255, 0.45) !important;
        border-radius: 20px !important;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.04) !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    }
    .span-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.08) !important;
        border-color: rgba(255, 255, 255, 0.75) !important;
    }
    
    /* Metrics Row (Glassmorphism boxes) */
    .metric-box {
        background: rgba(255, 255, 255, 0.65) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.45) !important;
        border-radius: 16px !important;
        padding: 1.2rem 1rem;
        text-align: center;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.03) !important;
        transition: all 0.3s ease;
    }
    .metric-box:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 35px 0 rgba(31, 38, 135, 0.06) !important;
        border-color: rgba(255, 255, 255, 0.7) !important;
    }
    .metric-val {
        font-size: 1.9rem;
        font-weight: 700;
        color: #1e3c72;
        margin: 0;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
        margin-top: 0.3rem;
    }
    
    /* Solve Button custom styling */
    .stButton>button {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 0.7rem 2rem !important;
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        box-shadow: 0 6px 20px rgba(30, 60, 114, 0.25) !important;
        transition: all 0.2s ease !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(30, 60, 114, 0.35) !important;
        filter: brightness(1.1);
    }
    
    /* Styling table internally for transparency */
    table {
        background: rgba(255, 255, 255, 0.3) !important;
        backdrop-filter: blur(8px) !important;
    }
    th {
        background-color: rgba(30, 60, 114, 0.9) !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Header HTML
st.markdown(
    """
    <div class="title-card">
        <h1>Continuous Beam Solver</h1>
        <p>Analyze structural beams with the Hardy Cross Moment Distribution Method (MDM)</p>
    </div>
    """,
    unsafe_allow_html=True
)

# --- SIDEBAR CONFIGURATION ---
st.sidebar.markdown('<div style="font-size: 1.3rem; font-weight: 700; color: #1e3c72; margin-bottom: 1rem;">⚙️ Solver Configuration</div>', unsafe_allow_html=True)

# General settings
num_spans = st.sidebar.number_input("Number of Spans", min_value=1, max_value=10, value=2, step=1)
tolerance = st.sidebar.number_input("MDM Convergence Tolerance (kNm)", min_value=0.0001, max_value=0.1, value=0.001, step=0.0005, format="%.4f")
max_iter = st.sidebar.number_input("Max Iterations", min_value=10, max_value=1000, value=200, step=10)

# Diagram Display Settings
st.sidebar.markdown('---')
st.sidebar.markdown('<div style="font-size: 1.1rem; font-weight: 600; color: #1e3c72; margin-bottom: 0.5rem;">📈 Diagram Settings</div>', unsafe_allow_html=True)
invert_bmd = st.sidebar.toggle("Invert BMD Y-Axis (Tension Side Down)", value=True, help="Plot positive sagging moments downwards (European / UK Standard)")
show_free_bmd = st.sidebar.toggle("Overlay Free Bending Moments", value=True)
show_support_bmd = st.sidebar.toggle("Overlay Support Moments Only", value=True)

# Support Conditions Settings
st.sidebar.markdown('---')
st.sidebar.markdown('<div style="font-size: 1.1rem; font-weight: 600; color: #1e3c72; margin-bottom: 0.5rem;">🦿 Support Conditions</div>', unsafe_allow_html=True)

supports = []
# Render support conditions selects
for j in range(num_spans + 1):
    if j == 0:
        label = "Support 0 (Left End)"
        options = ["Pinned", "Fixed"]
        default_val = "Pinned"
    elif j == num_spans:
        label = f"Support {j} (Right End)"
        options = ["Pinned", "Fixed"]
        default_val = "Pinned"
    else:
        label = f"Support {j} (Interior)"
        options = ["Continuous", "Fixed"]
        default_val = "Continuous"
        
    supt_type = st.sidebar.selectbox(label, options, index=options.index(default_val), key=f"supt_{j}")
    supports.append(supt_type)

# --- MAIN PANEL CONFIGURATION ---
st.markdown('<div class="section-header">📏 Span & Loading Properties</div>', unsafe_allow_html=True)

spans_data = []

# Generate inputs for each span
for i in range(num_spans):
    st.markdown(f'<div style="font-weight: 600; font-size: 1.15rem; color: #2a5298; margin-top: 1rem; margin-bottom: 0.5rem;">Span {i+1}</div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="span-card">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            L = st.number_input(f"Length L (m)", min_value=0.5, max_value=30.0, value=6.0, step=0.5, key=f"L_{i}")
        with col2:
            EI = st.number_input(f"Rigidity EI (kNm²)", min_value=1.0, max_value=1000000.0, value=10000.0, step=1000.0, key=f"EI_{i}")
            
        with col3:
            st.markdown('<p style="font-size: 0.9rem; font-weight: 600; margin: 0; color: #475569;">Loadings Configurator</p>', unsafe_allow_html=True)
            
            sub_col1, sub_col2 = st.columns(2)
            with sub_col1:
                enable_udl = st.checkbox(f"Enable UDL", value=True, key=f"enable_udl_{i}")
                udl_w = 0.0
                udl_start = 0.0
                udl_end = L
                if enable_udl:
                    udl_w = st.number_input(f"  UDL w (kN/m)", min_value=0.0, max_value=200.0, value=10.0, step=1.0, key=f"udl_w_{i}")
                    udl_range_toggle = st.checkbox("  Partial Span UDL?", value=False, key=f"udl_partial_{i}")
                    if udl_range_toggle:
                        udl_start = st.number_input(f"    Start Position (m)", min_value=0.0, max_value=L, value=0.0, step=0.5, key=f"udl_start_{i}")
                        udl_end = st.number_input(f"    End Position (m)", min_value=udl_start, max_value=L, value=L, step=0.5, key=f"udl_end_{i}")

            with sub_col2:
                num_pt_loads = st.selectbox(f"Point Loads", [0, 1, 2], index=0, key=f"num_pt_{i}")
                pt_loads = []
                for k in range(num_pt_loads):
                    pt_col1, pt_col2 = st.columns(2)
                    with pt_col1:
                        P = st.number_input(f"  P{k+1} (kN)", min_value=0.0, max_value=1000.0, value=20.0, step=5.0, key=f"P_{i}_{k}")
                    with pt_col2:
                        a = st.number_input(f"  Pos x (m)", min_value=0.0, max_value=L, value=L/2.0, step=0.5, key=f"a_{i}_{k}")
                    pt_loads.append({'type': 'Point', 'P': P, 'a': a})
                    
        # Package span load list
        span_loads = []
        if enable_udl and udl_w > 0.0:
            span_loads.append({
                'type': 'UDL',
                'w': udl_w,
                'a': udl_start,
                'b': udl_end
            })
        for pt_load in pt_loads:
            if pt_load['P'] > 0.0:
                span_loads.append(pt_load)
                
        spans_data.append({
            'L': L,
            'EI': EI,
            'loads': span_loads
        })
        
        st.markdown('</div>', unsafe_allow_html=True)

# Run solver
if st.button("🚀 Solve Beam", type="primary", use_container_width=True):
    try:
        # Run Hardy Cross solver
        res = BeamSolver.solve(spans_data, supports, tolerance=tolerance, max_iter=max_iter)
        forces = BeamSolver.get_internal_forces(spans_data, res)
        
        st.markdown('<div class="section-header">📊 Analysis Results</div>', unsafe_allow_html=True)
        
        # Summary Metrics
        if res['converged']:
            st.success(f"Moment Distribution converged successfully in {res['iterations']} iterations!")
        else:
            st.warning(f"Moment Distribution did not converge below tolerance of {tolerance} kNm in {max_iter} iterations. Displaying last results.")
            
        m1, m2, m3, m4 = st.columns(4)
        
        max_moment = max(max(forces['bending_moment']), abs(min(forces['bending_moment'])))
        max_shear = max(max(forces['shear_force']), abs(min(forces['shear_force'])))
        
        # Find maximum sagging (positive) and hogging (negative) moments
        sag_moments = [val for val in forces['bending_moment'] if val >= 0]
        hog_moments = [val for val in forces['bending_moment'] if val < 0]
        max_sag = max(sag_moments) if len(sag_moments) > 0 else 0.0
        max_hog = min(hog_moments) if len(hog_moments) > 0 else 0.0
        
        with m1:
            st.markdown(
                f"""
                <div class="metric-box">
                    <p class="metric-val">{max_sag:.2f} kNm</p>
                    <p class="metric-label">Max Sagging Moment (+)</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        with m2:
            st.markdown(
                f"""
                <div class="metric-box">
                    <p class="metric-val">{max_hog:.2f} kNm</p>
                    <p class="metric-label">Max Hogging Moment (-)</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        with m3:
            st.markdown(
                f"""
                <div class="metric-box">
                    <p class="metric-val">{max_shear:.2f} kN</p>
                    <p class="metric-label">Max Shear Force</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        with m4:
            st.markdown(
                f"""
                <div class="metric-box">
                    <p class="metric-val">{res['iterations']}</p>
                    <p class="metric-label">Hardy Cross Cycles</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        # 1. Beam Schematic Plotly Figure
        st.markdown('<div style="font-size: 1.25rem; font-weight: 600; color: #1e3c72; margin-top: 1.5rem; margin-bottom: 0.5rem;">🏗️ Beam Diagram / Schematic</div>', unsafe_allow_html=True)
        fig_beam = go.Figure()
        
        # Beam line
        total_L = sum([s['L'] for s in spans_data])
        fig_beam.add_trace(go.Scatter(
            x=[0, total_L], y=[0, 0],
            mode='lines',
            line=dict(color='#334155', width=6),
            name='Beam Axis',
            showlegend=False
        ))
        
        # Draw supports
        bounds = forces['span_boundaries']
        for j, x_sup in enumerate(bounds):
            sup_type = supports[j]
            
            if sup_type == 'Fixed':
                # Clamped support: vertical block
                fig_beam.add_trace(go.Scatter(
                    x=[x_sup, x_sup], y=[-0.4, 0.4],
                    mode='lines',
                    line=dict(color='#0f172a', width=8),
                    name=f'Support {j} (Fixed)',
                    showlegend=False
                ))
                # Add hatch markings behind the fixed support
                h_xs = []
                h_ys = []
                spacing = 0.1
                for y_offset in np.arange(-0.4, 0.5, spacing):
                    # Short hatch lines
                    h_xs.extend([x_sup, x_sup - 0.1, None] if j == 0 else [x_sup, x_sup + 0.1, None])
                    h_ys.extend([y_offset, y_offset - 0.05, None])
                fig_beam.add_trace(go.Scatter(
                    x=h_xs, y=h_ys,
                    mode='lines',
                    line=dict(color='#64748b', width=2),
                    showlegend=False
                ))
            else:
                # Pinned/Continuous: Draw a triangle marker
                fig_beam.add_trace(go.Scatter(
                    x=[x_sup], y=[-0.15],
                    mode='markers',
                    marker=dict(symbol='triangle-up', size=20, color='#0f172a', line=dict(color='black', width=1)),
                    name=f'Support {j} ({sup_type})',
                    showlegend=False
                ))
            
            # Support Label
            fig_beam.add_annotation(
                x=x_sup, y=-0.5,
                text=f"R{j}<br><b>{res['support_reactions'][j]:.2f} kN</b>",
                showarrow=False,
                font=dict(size=12, color="#0f172a"),
                align="center"
            )
            
        # Draw loads
        x_offset = 0.0
        for i, span in enumerate(spans_data):
            L_i = span['L']
            for load in span['loads']:
                if load['type'] == 'Point':
                    p_x = x_offset + load['a']
                    P_val = load['P']
                    # Downward arrow for point load
                    fig_beam.add_annotation(
                        x=p_x, y=0.1,
                        ax=p_x, ay=0.8,
                        xref="x", yref="y",
                        axref="x", ayref="y",
                        text="",
                        showarrow=True,
                        arrowhead=2,
                        arrowsize=1.2,
                        arrowwidth=3,
                        arrowcolor="#dc2626"
                    )
                    fig_beam.add_annotation(
                        x=p_x, y=0.95,
                        text=f"{P_val} kN",
                        showarrow=False,
                        font=dict(color="#dc2626", size=11, weight="bold")
                    )
                elif load['type'] == 'UDL':
                    udl_start = x_offset + load['a']
                    udl_end = x_offset + load['b']
                    w_val = load['w']
                    
                    # Draw UDL block above beam
                    fig_beam.add_shape(
                        type="rect",
                        x0=udl_start, y0=0.08,
                        x1=udl_end, y1=0.35,
                        line=dict(color="#0ea5e9", width=2),
                        fillcolor="rgba(14, 165, 233, 0.15)"
                    )
                    # Draw wavy curves or lines to represent load distribution
                    udl_xs = np.linspace(udl_start, udl_end, 15)
                    for ux in udl_xs:
                        fig_beam.add_annotation(
                            x=ux, y=0.09,
                            ax=ux, ay=0.32,
                            xref="x", yref="y",
                            axref="x", ayref="y",
                            text="",
                            showarrow=True,
                            arrowhead=1,
                            arrowsize=0.8,
                            arrowwidth=1.5,
                            arrowcolor="#0ea5e9"
                        )
                    fig_beam.add_annotation(
                        x=(udl_start + udl_end)/2.0, y=0.45,
                        text=f"{w_val} kN/m",
                        showarrow=False,
                        font=dict(color="#0ea5e9", size=11, weight="bold")
                    )
            x_offset += L_i
            
        fig_beam.update_layout(
            title=dict(text="Continuous Beam Loading & Reaction Schematic", font=dict(size=15, color='#1e3c72', weight='bold')),
            xaxis=dict(title="Length Coordinate (m)", range=[-0.5, total_L + 0.5], gridcolor='rgba(0,0,0,0.05)'),
            yaxis=dict(range=[-1.0, 1.2], showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=320,
            margin=dict(l=40, r=40, t=50, b=40),
        )
        st.markdown('<div class="span-card">', unsafe_allow_html=True)
        st.plotly_chart(fig_beam, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 2. Diagrams side-by-side in Columns
        diag_col1, diag_col2 = st.columns(2)
        
        with diag_col1:
            fig_bmd = go.Figure()
            
            # Gridlines and baseline
            fig_bmd.add_trace(go.Scatter(
                x=[0, sum([s['L'] for s in spans_data])], y=[0, 0],
                mode='lines',
                line=dict(color='black', width=1.5),
                showlegend=False
            ))
            
            # Final BMD Curve
            y_final = np.array(forces['bending_moment'])
            x_vals = np.array(forces['x'])
            
            fig_bmd.add_trace(go.Scatter(
                x=x_vals,
                y=y_final,
                mode='lines',
                line=dict(color='#4f46e5', width=3),
                fill='tozeroy',
                fillcolor='rgba(79, 70, 229, 0.15)',
                name='Final BMD',
                hovertemplate="x: %{x:.2f} m<br>Moment: %{y:.2f} kNm<extra></extra>"
            ))
            
            # Optional Free BMD overlay
            if show_free_bmd:
                fig_bmd.add_trace(go.Scatter(
                    x=x_vals,
                    y=forces['free_moment'],
                    mode='lines',
                    line=dict(color='#059669', width=1.5, dash='dash'),
                    name='Free BMD',
                    hoverinfo='skip'
                ))
                
            # Optional Support BMD overlay
            if show_support_bmd:
                fig_bmd.add_trace(go.Scatter(
                    x=x_vals,
                    y=forces['support_moment'],
                    mode='lines',
                    line=dict(color='#dc2626', width=1.5, dash='dash'),
                    name='Support Moments',
                    hoverinfo='skip'
                ))
            
            # Mark support lines
            for bound in forces['span_boundaries']:
                fig_bmd.add_shape(
                    type="line",
                    x0=bound, y0=min(y_final)*1.1,
                    x1=bound, y1=max(y_final)*1.1,
                    line=dict(color="#cbd5e1", width=1, dash="dot"),
                )

            # Invert axis logic
            yaxis_opts = dict(
                title="Bending Moment (kNm)",
                gridcolor='#f1f5f9',
                zerolinecolor='#cbd5e1'
            )
            if invert_bmd:
                yaxis_opts['autorange'] = 'reversed'
                
            fig_bmd.update_layout(
                title=dict(text="Bending Moment Diagram (BMD)", font=dict(size=15, color='#1e3c72', weight='bold')),
                xaxis=dict(title="Length Coordinate (m)", gridcolor='rgba(0,0,0,0.05)', zeroline=False),
                yaxis=yaxis_opts,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=400,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=40, r=40, t=60, b=40),
            )
            st.markdown('<div class="span-card">', unsafe_allow_html=True)
            st.plotly_chart(fig_bmd, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with diag_col2:
            fig_sfd = go.Figure()
            
            # Baseline
            fig_sfd.add_trace(go.Scatter(
                x=[0, sum([s['L'] for s in spans_data])], y=[0, 0],
                mode='lines',
                line=dict(color='black', width=1.5),
                showlegend=False
            ))
            
            y_shear = np.array(forces['shear_force'])
            x_vals = np.array(forces['x'])
            
            fig_sfd.add_trace(go.Scatter(
                x=x_vals,
                y=y_shear,
                mode='lines',
                line=dict(color='#0d9488', width=3),
                fill='tozeroy',
                fillcolor='rgba(13, 148, 136, 0.15)',
                name='Shear Force',
                hovertemplate="x: %{x:.2f} m<br>Shear: %{y:.2f} kN<extra></extra>"
            ))
            
            # Mark support lines
            for bound in forces['span_boundaries']:
                fig_sfd.add_shape(
                    type="line",
                    x0=bound, y0=min(y_shear)*1.1,
                    x1=bound, y1=max(y_shear)*1.1,
                    line=dict(color="#cbd5e1", width=1, dash="dot"),
                )
                
            fig_sfd.update_layout(
                title=dict(text="Shear Force Diagram (SFD)", font=dict(size=15, color='#1e3c72', weight='bold')),
                xaxis=dict(title="Length Coordinate (m)", gridcolor='rgba(0,0,0,0.05)', zeroline=False),
                yaxis=dict(title="Shear Force (kN)", gridcolor='rgba(0,0,0,0.05)', zerolinecolor='rgba(0,0,0,0.1)'),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=400,
                margin=dict(l=40, r=40, t=60, b=40),
            )
            st.markdown('<div class="span-card">', unsafe_allow_html=True)
            st.plotly_chart(fig_sfd, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        # 3. Moment Distribution Step Logger Table
        st.markdown('<div style="font-size: 1.25rem; font-weight: 600; color: #1e3c72; margin-top: 1.5rem; margin-bottom: 0.5rem;">📋 Moment Distribution (Hardy Cross Method) Steps</div>', unsafe_allow_html=True)
        st.markdown('<p style="font-weight: 500; color: #475569; margin-bottom: 0.5rem;">Detailed step-by-step joint moments (values in <b>kNm</b>):</p>', unsafe_allow_html=True)
        
        html_table = render_mdm_html_table(spans_data, res)
        st.markdown(html_table, unsafe_allow_html=True)
        
        # Add mathematical documentation
        with st.expander("📚 Moment Distribution Method (Hardy Cross Method) Explanation"):
            st.markdown(
                """
                ### Summary of Hardy Cross Method
                The **Moment Distribution Method** is a structural analysis method for statically indeterminate beams and frames. 
                It is an iterative numerical technique discovered by Hardy Cross in 1930.
                
                The method works as follows:
                1. **Fixed End Moments (FEMs)** are calculated for all spans as if their joint boundaries were fully fixed (clamped).
                2. **Relative Stiffnesses ($K$)** of the members meeting at each joint are determined:
                   $$K = \\frac{EI}{L}$$
                3. **Distribution Factors ($DF$)** are computed at each joint to partition the unbalanced moment among the adjacent member ends:
                   $$DF_{j, L} = \\frac{K_L}{K_L + K_R}$$
                   $$DF_{j, R} = \\frac{K_R}{K_L + K_R}$$
                4. **Iterative Loops**:
                   - **Balance**: Joints are released and unbalanced moments are distributed back to member ends in opposite directions proportional to their distribution factors.
                   - **Carry Over**: 50% ($C_f = 0.5$) of the balanced moments are transferred (carried over) to the opposite end of each span.
                5. This cycle (Balance $\\rightarrow$ Carry Over) is repeated until the out-of-balance joint moments converge below the specified tolerance limit ($0.001\\text{ kNm}$).
                """
            )
            
    except Exception as err:
        st.error(f"An error occurred during calculations: {err}")
        st.info("Please review your input span dimensions, flexural rigidity values, and load coordinate boundaries.")
else:
    # Initial load notice
    st.info("💡 Adjust span dimensions and load properties in the cards above, then click 'Solve Beam' to run the analysis.")
