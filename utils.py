"""
Utilidades compartidas para NoTechnoTempo
Estilos, logo y funciones comunes
"""

import streamlit as st


def apply_custom_css():
    """Aplica estilos CSS personalizados para NoTechnoTempo - Diseño moderno y profesional"""
    st.markdown("""
    <style>
    /* ==================== VARIABLES DE DISEÑO ==================== */
    :root {
        --primary-color: #6366f1;
        --primary-dark: #4f46e5;
        --primary-light: #818cf8;
        --secondary-color: #8b5cf6;
        --accent-color: #ec4899;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --error-color: #ef4444;
        --bg-primary: #ffffff;
        --bg-secondary: #f8fafc;
        --bg-tertiary: #f1f5f9;
        --text-primary: #0f172a;
        --text-secondary: #475569;
        --text-tertiary: #64748b;
        --border-color: #e2e8f0;
        --border-hover: #cbd5e1;
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        --radius-sm: 6px;
        --radius-md: 8px;
        --radius-lg: 12px;
        --radius-xl: 16px;
    }
    
    /* ==================== RESET Y BASE ==================== */
    * {
        box-sizing: border-box;
    }
    
    .stApp {
        background: var(--bg-secondary);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Inter', 'Helvetica Neue', Arial, sans-serif;
    }
    
    .main {
        background: var(--bg-secondary);
    }
    
    .main .block-container {
        padding-top: 0.5rem;
        padding-bottom: 0.5rem;
        max-width: 100%;
    }
    
    /* ==================== HEADER COMPACTO ==================== */
    .no-techno-header {
        background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
        border-bottom: 1px solid var(--border-color);
        padding: 0.5rem 0;
        margin-bottom: 0.75rem;
        box-shadow: var(--shadow-sm);
        position: sticky;
        top: 0;
        z-index: 100;
        backdrop-filter: blur(10px);
    }
    
    .header-content {
        max-width: 100%;
        margin: 0 auto;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0 1rem;
    }
    
    .logo-combined {
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        border-radius: var(--radius-lg);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        color: #ffffff;
        font-weight: 300;
        box-shadow: var(--shadow-sm);
        flex-shrink: 0;
    }
    
    .header-text {
        flex: 1;
    }
    
    .no-techno-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0;
        letter-spacing: -0.025em;
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .no-techno-subtitle {
        font-size: 0.75rem;
        color: var(--text-secondary);
        margin: 0.125rem 0 0 0;
        font-weight: 400;
    }
    
    /* ==================== CARDS MODERNAS ==================== */
    .ntt-card {
        background: var(--bg-primary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: 2rem;
        box-shadow: var(--shadow-sm);
        transition: all 0.2s ease;
        margin-bottom: 1.5rem;
    }
    
    .ntt-card:hover {
        box-shadow: var(--shadow-md);
        border-color: var(--border-hover);
    }
    
    .ntt-card-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid var(--border-color);
    }
    
    .ntt-card-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0;
    }
    
    .ntt-card-icon {
        font-size: 1.5rem;
    }
    
    /* ==================== TABS COMPACTAS ==================== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.25rem;
        background-color: transparent;
        border-bottom: 1px solid var(--border-color);
        padding: 0;
        margin-bottom: 0.75rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: var(--radius-sm) var(--radius-sm) 0 0;
        padding: 0.5rem 1rem;
        font-weight: 500;
        color: var(--text-secondary);
        border-bottom: 2px solid transparent;
        transition: all 0.2s ease;
        font-size: 0.875rem;
        margin-right: 0.125rem;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--primary-color);
        background-color: var(--bg-tertiary);
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--bg-primary);
        color: var(--primary-color);
        border-bottom: 3px solid var(--primary-color);
        font-weight: 600;
    }
    
    /* ==================== BOTONES MODERNOS ==================== */
    .stButton > button {
        border-radius: var(--radius-md);
        font-weight: 500;
        border: none;
        transition: all 0.2s ease;
        font-size: 0.95rem;
        padding: 0.625rem 1.5rem;
        letter-spacing: 0.01em;
    }
    
    .stButton > button[type="primary"] {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%);
        color: #ffffff;
        box-shadow: var(--shadow-sm);
    }
    
    .stButton > button[type="primary"]:hover {
        background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary-color) 100%);
        transform: translateY(-1px);
        box-shadow: var(--shadow-md);
    }
    
    .stButton > button:not([type="primary"]) {
        background-color: var(--bg-primary);
        color: var(--text-primary);
        border: 1.5px solid var(--border-color);
    }
    
    .stButton > button:not([type="primary"]):hover {
        background-color: var(--bg-tertiary);
        border-color: var(--primary-color);
        color: var(--primary-color);
    }
    
    /* ==================== INPUTS Y SELECTS ==================== */
    .stSelectbox > div > div,
    .stMultiselect > div > div {
        background-color: var(--bg-primary) !important;
        border: 1.5px solid var(--border-color) !important;
        border-radius: var(--radius-md);
        transition: all 0.2s ease;
    }
    
    .stSelectbox > div > div:hover,
    .stMultiselect > div > div:hover {
        border-color: var(--primary-color) !important;
    }
    
    .stMultiselect > div > div[data-baseweb="base-input"] {
        background-color: var(--bg-primary) !important;
    }
    
    .stMultiselect [data-baseweb="tag"] {
        background: linear-gradient(135deg, var(--primary-light) 0%, var(--primary-color) 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: var(--radius-sm);
        font-weight: 500;
        padding: 0.25rem 0.75rem;
    }
    
    .stTextInput > div > div > input {
        border: 1.5px solid var(--border-color);
        border-radius: var(--radius-md);
        background-color: var(--bg-primary);
        transition: all 0.2s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
    }
    
    .stSlider > div > div {
        color: var(--primary-color);
    }
    
    /* ==================== TABLAS MODERNAS ==================== */
    .stDataFrame {
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        overflow: hidden;
        box-shadow: var(--shadow-sm);
        background: var(--bg-primary);
    }
    
    /* ==================== TIPOGRAFÍA COMPACTA ==================== */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
        font-weight: 600;
        letter-spacing: -0.02em;
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    h1 {
        font-size: 1.5rem;
        font-weight: 700;
    }
    
    h2 {
        font-size: 1.25rem;
    }
    
    h3 {
        font-size: 1rem;
    }
    
    p, div, span, label {
        color: var(--text-secondary) !important;
    }
    
    /* ==================== MÉTRICAS COMPACTAS ==================== */
    [data-testid="stMetricContainer"] {
        background: var(--bg-primary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-sm);
        padding: 0.75rem;
        box-shadow: var(--shadow-sm);
    }
    
    [data-testid="stMetricValue"] {
        color: var(--text-primary);
        font-weight: 700;
        font-size: 1.25rem;
    }
    
    [data-testid="stMetricLabel"] {
        color: var(--text-secondary);
        font-weight: 500;
        font-size: 0.75rem;
    }
    
    [data-testid="stMetricDelta"] {
        font-weight: 600;
    }
    
    /* ==================== MENSAJES MEJORADOS ==================== */
    .stSuccess {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        border-left: 4px solid var(--success-color);
        color: #065f46;
        border-radius: var(--radius-md);
        padding: 1rem 1.5rem;
    }
    
    .stInfo {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        border-left: 4px solid var(--primary-color);
        color: #1e40af;
        border-radius: var(--radius-md);
        padding: 1rem 1.5rem;
    }
    
    .stWarning {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border-left: 4px solid var(--warning-color);
        color: #92400e;
        border-radius: var(--radius-md);
        padding: 1rem 1.5rem;
    }
    
    .stError {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        border-left: 4px solid var(--error-color);
        color: #991b1b;
        border-radius: var(--radius-md);
        padding: 1rem 1.5rem;
    }
    
    /* ==================== SECCIONES ==================== */
    .section-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent 0%, var(--border-color) 50%, transparent 100%);
        margin: 2.5rem 0;
        border: none;
    }
    
    /* ==================== CHECKBOX Y TOGGLE ==================== */
    .stCheckbox > label {
        color: var(--text-primary);
        font-weight: 500;
    }
    
    /* ==================== SCROLLBAR PERSONALIZADA ==================== */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-secondary);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--border-hover);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-tertiary);
    }
    
    /* ==================== ANIMACIONES ==================== */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .fade-in {
        animation: fadeIn 0.3s ease-out;
    }
    
    /* ==================== RESPONSIVE ==================== */
    @media (max-width: 768px) {
        .header-content {
            padding: 0 1rem;
        }
        
        .no-techno-title {
            font-size: 1.75rem;
        }
        
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)


def render_header():
    """Renderiza el header de NoTechnoTempo con logo combinado"""
    st.markdown("""
    <div class="no-techno-header">
        <div class="header-content">
            <div class="logo-combined">⏱</div>
            <div class="header-text">
                <h1 class="no-techno-title">NoTechnoTempo</h1>
                <p class="no-techno-subtitle">Tu biblioteca musical definitiva</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_card(title: str, icon: str = "", content: str = ""):
    """Renderiza una card moderna con título y contenido"""
    icon_html = f'<span class="ntt-card-icon">{icon}</span>' if icon else ""
    return f"""
    <div class="ntt-card fade-in">
        <div class="ntt-card-header">
            {icon_html}
            <h3 class="ntt-card-title">{title}</h3>
        </div>
        {content}
    </div>
    """
