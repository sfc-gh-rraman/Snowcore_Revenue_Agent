#!/usr/bin/env python3
import json
from pathlib import Path

ICON_CACHE = Path("/Users/rraman/Documents/isf-solution-onboarding-skill/assets/icons_b64_cache.json")
OUTPUT_HTML = Path("/Users/rraman/Documents/vulcan_revenue_forecast/isf/ISF_Architecture_ManufacturingRevenueIntelligence.html")

with open(ICON_CACHE) as f:
    icons = json.load(f)

def get_icon(key, size=48):
    if key in icons:
        return f'<img src="data:image/svg+xml;base64,{icons[key]}" width="{size}" height="{size}" alt="{key}">'
    return f'<span style="font-size:{size}px">⚙️</span>'

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Manufacturing Revenue Intelligence Platform - Architecture</title>
<style>
:root {{
  --sf-blue: #29B5E8;
  --sf-dark-blue: #1a73e8;
  --sf-light-blue: #e8f4fd;
  --sf-navy: #0d2240;
  --sf-white: #ffffff;
  --sf-gray-100: #f8f9fa;
  --sf-gray-200: #e9ecef;
  --sf-gray-600: #6c757d;
  --sf-success: #28a745;
  --sf-warning: #ffc107;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background: var(--sf-gray-100); color: var(--sf-navy); line-height: 1.6; }}
.container {{ max-width: 1400px; margin: 0 auto; padding: 40px 20px; }}
.header {{ background: linear-gradient(135deg, var(--sf-navy) 0%, #1e3a5f 100%); color: var(--sf-white); padding: 60px 40px; border-radius: 16px; margin-bottom: 40px; text-align: center; }}
.header h1 {{ font-size: 2.5rem; margin-bottom: 16px; font-weight: 700; }}
.header p {{ font-size: 1.2rem; opacity: 0.9; max-width: 800px; margin: 0 auto; }}
.header .badge {{ display: inline-block; background: var(--sf-blue); padding: 8px 20px; border-radius: 20px; font-size: 0.9rem; margin-top: 20px; }}
.metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 24px; margin-bottom: 40px; }}
.metric {{ background: var(--sf-white); padding: 32px; border-radius: 12px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
.metric .value {{ font-size: 2.5rem; font-weight: 700; color: var(--sf-blue); }}
.metric .label {{ color: var(--sf-gray-600); font-size: 0.95rem; margin-top: 8px; }}
.section {{ background: var(--sf-white); border-radius: 16px; padding: 40px; margin-bottom: 32px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
.section h2 {{ font-size: 1.5rem; margin-bottom: 24px; color: var(--sf-navy); border-bottom: 3px solid var(--sf-blue); padding-bottom: 12px; display: inline-block; }}
.arch-diagram {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; margin-top: 24px; }}
.arch-layer {{ background: var(--sf-gray-100); border-radius: 12px; padding: 20px; text-align: center; }}
.arch-layer h3 {{ font-size: 0.85rem; color: var(--sf-gray-600); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 16px; }}
.arch-component {{ background: var(--sf-white); border: 2px solid var(--sf-gray-200); border-radius: 8px; padding: 16px; margin-bottom: 12px; transition: all 0.2s; }}
.arch-component:hover {{ border-color: var(--sf-blue); transform: translateY(-2px); }}
.arch-component .icon {{ margin-bottom: 8px; }}
.arch-component .name {{ font-weight: 600; font-size: 0.9rem; }}
.arch-component .desc {{ font-size: 0.75rem; color: var(--sf-gray-600); margin-top: 4px; }}
.pipeline {{ display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px; margin-top: 24px; }}
.pipeline-step {{ flex: 1; min-width: 150px; background: var(--sf-light-blue); border-radius: 12px; padding: 24px 16px; text-align: center; position: relative; }}
.pipeline-step::after {{ content: '→'; position: absolute; right: -20px; top: 50%; transform: translateY(-50%); font-size: 1.5rem; color: var(--sf-blue); }}
.pipeline-step:last-child::after {{ display: none; }}
.pipeline-step .step-num {{ background: var(--sf-blue); color: white; width: 28px; height: 28px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 0.85rem; font-weight: 600; margin-bottom: 12px; }}
.pipeline-step .step-title {{ font-weight: 600; font-size: 0.9rem; }}
.governance {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 24px; margin-top: 24px; }}
.gov-card {{ background: var(--sf-gray-100); border-radius: 12px; padding: 24px; border-left: 4px solid var(--sf-blue); }}
.gov-card h4 {{ font-size: 1rem; margin-bottom: 8px; }}
.gov-card p {{ font-size: 0.9rem; color: var(--sf-gray-600); }}
.cost-table {{ width: 100%; border-collapse: collapse; margin-top: 24px; }}
.cost-table th, .cost-table td {{ padding: 16px; text-align: left; border-bottom: 1px solid var(--sf-gray-200); }}
.cost-table th {{ background: var(--sf-navy); color: white; font-weight: 600; }}
.cost-table tr:nth-child(even) {{ background: var(--sf-gray-100); }}
.cost-table .highlight {{ background: var(--sf-light-blue); font-weight: 600; }}
.footer {{ text-align: center; padding: 40px; color: var(--sf-gray-600); font-size: 0.9rem; }}
.footer .logo {{ margin-bottom: 16px; }}
</style>
</head>
<body>
<div class="container">
  <header class="header">
    <div class="logo">{get_icon('snowflake', 64)}</div>
    <h1>Manufacturing Revenue Intelligence Platform</h1>
    <p>AI-Powered Probabilistic Forecasting for Modern CFOs - Transform uncertainty into actionable financial intelligence</p>
    <span class="badge">IND-MFG | CFO Persona | Cortex AI</span>
  </header>

  <div class="metrics">
    <div class="metric"><div class="value">40%</div><div class="label">Forecast Accuracy Improvement</div></div>
    <div class="metric"><div class="value">$2M+</div><div class="label">Annual Savings</div></div>
    <div class="metric"><div class="value">70%</div><div class="label">Faster Analysis Cycles</div></div>
    <div class="metric"><div class="value">10K+</div><div class="label">Monte Carlo Simulations/sec</div></div>
  </div>

  <section class="section">
    <h2>Solution Architecture</h2>
    <div class="arch-diagram">
      <div class="arch-layer">
        <h3>Data Sources</h3>
        <div class="arch-component"><div class="icon">{get_icon('database', 36)}</div><div class="name">ERP/SAP Data</div><div class="desc">Sales orders, contracts</div></div>
        <div class="arch-component"><div class="icon">{get_icon('table', 36)}</div><div class="name">Historical Revenue</div><div class="desc">5+ years time series</div></div>
        <div class="arch-component"><div class="icon">{get_icon('marketplace', 36)}</div><div class="name">Market Data</div><div class="desc">Commodities, indices</div></div>
      </div>
      <div class="arch-layer">
        <h3>Ingestion</h3>
        <div class="arch-component"><div class="icon">{get_icon('snowpipe', 36)}</div><div class="name">Snowpipe Streaming</div><div class="desc">Real-time ingestion</div></div>
        <div class="arch-component"><div class="icon">{get_icon('dynamic-tables', 36)}</div><div class="name">Dynamic Tables</div><div class="desc">Incremental refresh</div></div>
        <div class="arch-component"><div class="icon">{get_icon('streams', 36)}</div><div class="name">Change Data Capture</div><div class="desc">Delta processing</div></div>
      </div>
      <div class="arch-layer">
        <h3>Processing</h3>
        <div class="arch-component"><div class="icon">{get_icon('snowpark', 36)}</div><div class="name">Snowpark Python</div><div class="desc">Monte Carlo engine</div></div>
        <div class="arch-component"><div class="icon">{get_icon('cortex', 36)}</div><div class="name">Cortex AI</div><div class="desc">LLM analysis</div></div>
        <div class="arch-component"><div class="icon">{get_icon('ml', 36)}</div><div class="name">ML Models</div><div class="desc">Time series forecasting</div></div>
      </div>
      <div class="arch-layer">
        <h3>Services</h3>
        <div class="arch-component"><div class="icon">{get_icon('container-services', 36)}</div><div class="name">SPCS</div><div class="desc">Container services</div></div>
        <div class="arch-component"><div class="icon">{get_icon('api', 36)}</div><div class="name">REST APIs</div><div class="desc">External integration</div></div>
        <div class="arch-component"><div class="icon">{get_icon('tasks', 36)}</div><div class="name">Scheduled Tasks</div><div class="desc">Automated refresh</div></div>
      </div>
      <div class="arch-layer">
        <h3>Applications</h3>
        <div class="arch-component"><div class="icon">{get_icon('streamlit', 36)}</div><div class="name">Streamlit Dashboard</div><div class="desc">Interactive UI</div></div>
        <div class="arch-component"><div class="icon">{get_icon('notebook', 36)}</div><div class="name">Notebooks</div><div class="desc">Analysis workspace</div></div>
        <div class="arch-component"><div class="icon">{get_icon('chart', 36)}</div><div class="name">Executive Reports</div><div class="desc">Board-ready outputs</div></div>
      </div>
    </div>
  </section>

  <section class="section">
    <h2>Data Pipeline Flow</h2>
    <div class="pipeline">
      <div class="pipeline-step"><span class="step-num">1</span><div class="step-title">Ingest</div><div class="desc">ERP + Market feeds</div></div>
      <div class="pipeline-step"><span class="step-num">2</span><div class="step-title">Transform</div><div class="desc">Feature engineering</div></div>
      <div class="pipeline-step"><span class="step-num">3</span><div class="step-title">Simulate</div><div class="desc">10K Monte Carlo runs</div></div>
      <div class="pipeline-step"><span class="step-num">4</span><div class="step-title">Analyze</div><div class="desc">P10/P50/P90 ranges</div></div>
      <div class="pipeline-step"><span class="step-num">5</span><div class="step-title">Present</div><div class="desc">CFO dashboard</div></div>
    </div>
  </section>

  <section class="section">
    <h2>Governance & Security</h2>
    <div class="governance">
      <div class="gov-card"><h4>Role-Based Access</h4><p>Fine-grained RBAC ensures CFO, FP&A, and analysts see only authorized data and forecasts.</p></div>
      <div class="gov-card"><h4>Audit Trail</h4><p>Complete lineage tracking from source data through Monte Carlo simulations to final projections.</p></div>
      <div class="gov-card"><h4>Data Masking</h4><p>Dynamic masking protects sensitive financial data while enabling cross-functional collaboration.</p></div>
      <div class="gov-card"><h4>SOX Compliance</h4><p>Built-in controls support Sarbanes-Oxley requirements for financial forecasting systems.</p></div>
    </div>
  </section>

  <section class="section">
    <h2>Cost Comparison: Traditional vs Snowflake</h2>
    <table class="cost-table">
      <tr><th>Component</th><th>Traditional Approach</th><th>Snowflake Platform</th><th>Savings</th></tr>
      <tr><td>Infrastructure</td><td>$500K+ (on-prem servers)</td><td>Pay-per-use compute</td><td>60-70%</td></tr>
      <tr><td>Data Integration</td><td>$200K (ETL tools)</td><td>Native connectors + Snowpipe</td><td>50%</td></tr>
      <tr><td>ML Platform</td><td>$300K (separate ML infra)</td><td>Snowpark ML + Cortex</td><td>70%</td></tr>
      <tr><td>Maintenance</td><td>3-5 FTEs</td><td>Fully managed</td><td>80%</td></tr>
      <tr class="highlight"><td><strong>Total TCO</strong></td><td><strong>$1.5M+/year</strong></td><td><strong>$400K/year</strong></td><td><strong>73%</strong></td></tr>
    </table>
  </section>

  <footer class="footer">
    <div class="logo">{get_icon('snowflake', 48)}</div>
    <p>Manufacturing Revenue Intelligence Platform | Powered by Snowflake</p>
    <p style="margin-top:8px;font-size:0.8rem;">ISF Solution Template v3.1.0 | IND-MFG | Generated March 2026</p>
  </footer>
</div>
</body>
</html>
'''

OUTPUT_HTML.write_text(html)
print(f"Generated: {OUTPUT_HTML}")
