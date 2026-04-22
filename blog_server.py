#!/usr/bin/env python3
import http.server, socketserver, os, re

DOCS_DIR = os.path.expanduser("~/workspace/spring-backend-template/docs")
PORT = 8878

# ── AWS-style 로컬 개발 구성도 ──────────────────────────────────────────────
LOCAL_DEV_DIAGRAM = """
<div class="aws-diagram" id="local-dev-diagram">
  <div class="aws-diagram-title">로컬 개발 구성도</div>
  <div class="ldev-stage">
    <!-- SVG arrows — marker 기반 자동 방향 화살촉 -->
    <svg class="ldev-svg" width="680" height="420" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <marker id="arr-gray" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
          <polygon points="0 0, 8 3, 0 6" fill="#64748b"/>
        </marker>
        <marker id="arr-pg" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
          <polygon points="0 0, 8 3, 0 6" fill="#4169E1"/>
        </marker>
        <marker id="arr-minio" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
          <polygon points="0 0, 8 3, 0 6" fill="#C72E28"/>
        </marker>
        <marker id="arr-nas" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
          <polygon points="0 0, 8 3, 0 6" fill="#7AA116"/>
        </marker>
      </defs>

      <!-- Flutter → Spring Boot (solid) -->
      <line x1="140" y1="205" x2="218" y2="205"
            stroke="#64748b" stroke-width="2" marker-end="url(#arr-gray)"/>
      <text x="179" y="197" font-size="10" fill="#94a3b8" text-anchor="middle" font-family="sans-serif">HTTP</text>

      <!-- Spring Boot → PostgreSQL (solid, 위 대각선) -->
      <line x1="366" y1="190" x2="450" y2="72"
            stroke="#4169E1" stroke-width="2" marker-end="url(#arr-pg)"/>

      <!-- Spring Boot → MinIO (dashed, 수평) -->
      <line x1="366" y1="205" x2="450" y2="205"
            stroke="#C72E28" stroke-width="2" stroke-dasharray="5,3" marker-end="url(#arr-minio)"/>
      <text x="408" y="197" font-size="10" fill="#C72E28" text-anchor="middle" font-family="sans-serif">파일 업로드 테스트</text>

      <!-- Spring Boot → NAS MinIO (dashed, 아래 대각선) -->
      <line x1="366" y1="220" x2="450" y2="336"
            stroke="#7AA116" stroke-width="2" stroke-dasharray="5,3" marker-end="url(#arr-nas)"/>
      <text x="420" y="295" font-size="10" fill="#7AA116" text-anchor="middle" font-family="sans-serif">LAN 직접</text>
    </svg>

    <!-- Flutter -->
    <div class="ldev-node-pos" style="left:8px;top:150px">
      <div class="aws-node compute" style="width:130px">
        <div class="aws-icon" style="background:#042B59">
          <img src="https://cdn.simpleicons.org/flutter/54C5F8" width="26" height="26" alt="Flutter">
        </div>
        <div class="aws-name">Flutter 앱</div>
        <div class="aws-sub">iOS Simulator</div>
      </div>
    </div>

    <!-- Spring Boot -->
    <div class="ldev-node-pos" style="left:218px;top:150px">
      <div class="aws-node compute" style="width:148px">
        <div class="aws-icon" style="background:#1A3D1E">
          <img src="https://cdn.simpleicons.org/springboot/6DB33F" width="26" height="26" alt="Spring Boot">
        </div>
        <div class="aws-name">Spring Boot</div>
        <div class="aws-sub">JVM 직접 실행 · :8081</div>
      </div>
    </div>

    <!-- PostgreSQL -->
    <div class="ldev-node-pos" style="left:452px;top:16px">
      <div class="aws-node database" style="width:130px">
        <div class="aws-icon" style="background:#1A2F4A">
          <img src="https://cdn.simpleicons.org/postgresql/4169E1" width="26" height="26" alt="PostgreSQL">
        </div>
        <div class="aws-name">PostgreSQL</div>
        <div class="aws-sub">docker · :5433</div>
      </div>
    </div>

    <!-- MinIO -->
    <div class="ldev-node-pos" style="left:452px;top:150px">
      <div class="aws-node storage optional" style="width:130px">
        <div class="aws-icon" style="background:#3D0E0C">
          <img src="https://cdn.simpleicons.org/minio/C72E28" width="26" height="26" alt="MinIO">
        </div>
        <div class="aws-name">MinIO</div>
        <div class="aws-sub">docker · :9000 선택</div>
      </div>
    </div>

    <!-- NAS MinIO -->
    <div class="ldev-node-pos" style="left:452px;top:284px">
      <div class="aws-node storage optional" style="width:130px">
        <div class="aws-icon" style="background:#1E2A06">
          <img src="https://cdn.simpleicons.org/minio/7AA116" width="26" height="26" alt="NAS MinIO">
        </div>
        <div class="aws-name">NAS MinIO</div>
        <div class="aws-sub">LAN · :9000 선택</div>
      </div>
    </div>

  </div>

  <div class="aws-legend">
    <span class="legend-item compute">Compute</span>
    <span class="legend-item database">Database</span>
    <span class="legend-item storage">Storage</span>
    <span style="font-size:11px;color:#94a3b8;display:flex;align-items:center;gap:4px">
      <svg width="24" height="8"><line x1="0" y1="4" x2="24" y2="4" stroke="#94a3b8" stroke-width="2" stroke-dasharray="4,2"/></svg>
      선택적 연결
    </span>
  </div>
</div>
"""

# ── AWS-style 운영 구성도 ───────────────────────────────────────────────────
PROD_DIAGRAM = """
<div class="aws-diagram" id="prod-diagram">
  <div class="aws-diagram-title">운영 구성도</div>

  <div class="aws-prod-canvas">

    <!-- Row 1: Internet → Cloudflare -->
    <div class="aws-prod-row">
      <div class="aws-node network" style="width:130px">
        <div class="aws-icon" style="background:#1e3a5f">
          <img src="https://cdn.simpleicons.org/internetexplorer/4dabf7" width="26" height="26" alt="Internet" onerror="this.parentElement.textContent='🌐'">
        </div>
        <div class="aws-name">인터넷 사용자</div>
      </div>
      <div class="aws-harrow">
        <span>HTTPS</span>
        <svg width="60" height="20"><line x1="0" y1="10" x2="50" y2="10" stroke="#94a3b8" stroke-width="2"/><polygon points="50,6 60,10 50,14" fill="#94a3b8"/></svg>
      </div>
      <div class="aws-node network" style="width:150px">
        <div class="aws-icon" style="background:#3D1F00">
          <img src="https://cdn.simpleicons.org/cloudflare/F38020" width="26" height="26" alt="Cloudflare">
        </div>
        <div class="aws-name">Cloudflare 엣지</div>
        <div class="aws-sub">TLS · DDoS · WAF</div>
      </div>
      <div class="aws-harrow">
        <span>Tunnel</span>
        <svg width="60" height="20"><line x1="0" y1="10" x2="50" y2="10" stroke="#94a3b8" stroke-width="2" stroke-dasharray="4,2"/><polygon points="50,6 60,10 50,14" fill="#94a3b8"/></svg>
      </div>
      <div class="aws-group prod-host" style="flex:1">
        <div class="aws-group-label">🖥 맥미니 · OrbStack</div>

        <div class="aws-prod-inner-row">
          <div class="aws-node network" style="width:120px">
            <div class="aws-icon" style="background:#042040">
              <img src="https://cdn.simpleicons.org/kamal/0ea5e9" width="26" height="26" alt="kamal" onerror="this.parentElement.innerHTML='🔀'">
            </div>
            <div class="aws-name">kamal-proxy</div>
            <div class="aws-sub">:80 Blue/Green</div>
          </div>
          <div class="aws-harrow small">
            <svg width="40" height="20"><line x1="0" y1="10" x2="30" y2="10" stroke="#94a3b8" stroke-width="2"/><polygon points="30,6 40,10 30,14" fill="#94a3b8"/></svg>
          </div>
          <div class="aws-node compute" style="width:140px">
            <div class="aws-icon" style="background:#1A3D1E">
              <img src="https://cdn.simpleicons.org/springboot/6DB33F" width="26" height="26" alt="Spring Boot">
            </div>
            <div class="aws-name">Spring Boot</div>
            <div class="aws-sub">container :8080</div>
          </div>
        </div>

        <div class="aws-group obs-group" style="margin-top:16px">
          <div class="aws-group-label">📊 관측성 스택 (docker-compose)</div>
          <div class="aws-row" style="gap:8px">
            <div class="aws-node obs mini"><div class="aws-icon sm" style="background:#3D1200"><img src="https://cdn.simpleicons.org/prometheus/E6522C" width="20" height="20" alt="Prometheus"></div><div class="aws-name sm">Prometheus<br/>:9090</div></div>
            <div class="aws-node obs mini"><div class="aws-icon sm" style="background:#1A1A2E"><img src="https://cdn.simpleicons.org/grafana/F5A623" width="20" height="20" alt="Loki" onerror="this.parentElement.textContent='📋'"></div><div class="aws-name sm">Loki<br/>:3100</div></div>
            <div class="aws-node obs mini"><div class="aws-icon sm" style="background:#2A1800"><img src="https://cdn.simpleicons.org/grafana/F46800" width="20" height="20" alt="Grafana"></div><div class="aws-name sm">Grafana<br/>:3000</div></div>
            <div class="aws-node obs mini"><div class="aws-icon sm" style="background:#2A001A"><img src="https://cdn.simpleicons.org/prometheus/E01E5A" width="20" height="20" alt="Alertmanager"></div><div class="aws-name sm">Alertmanager<br/>:9093</div></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Row 2: Spring Boot 외부 연결 -->
    <div class="aws-prod-row ext-row">
      <div style="flex:1"></div>
      <div class="aws-ext-connectors">
        <div class="aws-ext-item">
          <div class="aws-varrow">
            <svg width="20" height="40"><line x1="10" y1="0" x2="10" y2="30" stroke="#94a3b8" stroke-width="2"/><polygon points="6,30 14,30 10,40" fill="#94a3b8"/></svg>
            <span>JDBC :6543</span>
          </div>
          <div class="aws-node database" style="width:130px">
            <div class="aws-icon" style="background:#0D2918">
              <img src="https://cdn.simpleicons.org/supabase/3ECF8E" width="26" height="26" alt="Supabase">
            </div>
            <div class="aws-name">Supabase Seoul</div>
            <div class="aws-sub">PostgreSQL</div>
          </div>
        </div>
        <div class="aws-ext-item">
          <div class="aws-varrow">
            <svg width="20" height="40"><line x1="10" y1="0" x2="10" y2="30" stroke="#94a3b8" stroke-width="2"/><polygon points="6,30 14,30 10,40" fill="#94a3b8"/></svg>
            <span>S3 API</span>
          </div>
          <div class="aws-node storage" style="width:130px">
            <div class="aws-icon" style="background:#1E2A06">
              <img src="https://cdn.simpleicons.org/minio/7AA116" width="26" height="26" alt="MinIO">
            </div>
            <div class="aws-name">NAS MinIO</div>
            <div class="aws-sub">Tailscale LAN</div>
          </div>
        </div>
      </div>
    </div>

  </div>

  <div class="aws-legend">
    <span class="legend-item compute">Compute</span>
    <span class="legend-item database">Database</span>
    <span class="legend-item storage">Storage</span>
    <span class="legend-item network">Network</span>
    <span class="legend-item obs">Observability</span>
  </div>
</div>
"""

AWS_CSS = """
/* ── AWS Diagram ─────────────────────────────────── */
.aws-diagram {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 28px 32px 24px;
  margin: 28px 0;
  font-family: 'Inter', 'Noto Sans KR', sans-serif;
}
.aws-diagram-title {
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: .8px;
  margin-bottom: 24px;
}
.aws-canvas {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  flex-wrap: wrap;
}
.aws-prod-canvas { display: flex; flex-direction: column; gap: 0; }
.aws-prod-row { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.ext-row { margin-top: 0; padding-left: 24px; }

.aws-group {
  border: 2px dashed #cbd5e1;
  border-radius: 12px;
  padding: 16px 20px 20px;
  position: relative;
  background: white;
}
.aws-group.inner {
  background: #f8fafc;
  border-color: #e2e8f0;
  margin-top: 12px;
}
.aws-group.prod-host {
  background: white;
  border-color: #cbd5e1;
}
.aws-group.obs-group {
  background: #fdf4ff;
  border-color: #e9d5ff;
  border-style: solid;
}
.aws-group-label {
  position: absolute;
  top: -11px;
  left: 14px;
  background: white;
  padding: 0 8px;
  font-size: 11px;
  font-weight: 700;
  color: #475569;
  letter-spacing: .3px;
  border-radius: 4px;
}
.aws-group.obs-group .aws-group-label { background: #fdf4ff; }

.aws-row { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
.aws-prod-inner-row { display: flex; align-items: center; gap: 4px; margin-top: 8px; }

.aws-node {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  min-width: 100px;
  box-shadow: 0 1px 4px rgba(0,0,0,.06);
  transition: box-shadow .15s, transform .15s;
}
.aws-node:hover { box-shadow: 0 4px 12px rgba(0,0,0,.1); transform: translateY(-1px); }
.aws-node.optional { opacity: .7; border-style: dashed; }
.aws-node.mini { min-width: 80px; padding: 8px 10px; }

.aws-icon {
  width: 40px; height: 40px;
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}
.aws-icon.sm { width: 28px; height: 28px; font-size: 14px; border-radius: 6px; }

.aws-name { font-size: 12px; font-weight: 600; color: #1e293b; text-align: center; line-height: 1.3; }
.aws-name.sm { font-size: 10px; }
.aws-sub { font-size: 10px; color: #94a3b8; text-align: center; }

/* node type border accent */
.aws-node.compute { border-top: 3px solid #FF9900; }
.aws-node.database { border-top: 3px solid #336791; }
.aws-node.storage  { border-top: 3px solid #7AA116; }
.aws-node.network  { border-top: 3px solid #6366f1; }
.aws-node.obs      { border-top: 3px solid #a855f7; }

/* connectors */
.aws-connector { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.aws-conn-line { width: 48px; height: 2px; background: #94a3b8; }
.aws-conn-arrow { color: #94a3b8; font-size: 14px; margin-top: -4px; }
.aws-conn-label { font-size: 10px; color: #94a3b8; font-weight: 500; white-space: nowrap; }

.aws-side-connector {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 4px; padding: 0 8px;
}
.aws-conn-vert { width: 2px; height: 40px; background: #94a3b8; border-style: dashed; }

.aws-harrow {
  display: flex; flex-direction: column; align-items: center;
  gap: 2px; padding: 0 4px;
}
.aws-harrow span { font-size: 10px; color: #94a3b8; font-weight: 500; white-space: nowrap; }
.aws-harrow.small { padding: 0 2px; }

.aws-varrow {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
}
.aws-varrow span { font-size: 10px; color: #94a3b8; font-weight: 500; }

.aws-ext-connectors { display: flex; gap: 48px; padding-left: 32px; }
.aws-ext-item { display: flex; flex-direction: column; align-items: center; }

/* legend */
/* ── Local Dev Layout ── */
.ldev-wrap { display: flex; flex-direction: column; gap: 0; }
.ldev-macbook { padding: 20px 24px 24px; position: relative; }
.ldev-top { display: flex; align-items: center; gap: 0; justify-content: center; }
.ldev-arrow-h { display: flex; flex-direction: column; align-items: center; gap: 2px; padding: 0 8px; }
.ldev-arrow-h span { font-size: 10px; color: #94a3b8; font-weight: 500; white-space: nowrap; }
.ldev-branch { width: 100%; margin: 0; padding: 0; }
.ldev-stage {
  position: relative;
  height: 420px;
  width: 680px;
  overflow: visible;
}
.ldev-svg {
  position: absolute;
  top: 0; left: 0;
  width: 680px;
  height: 420px;
  pointer-events: none;
}
.ldev-node-pos {
  position: absolute;
}
.aws-icon img { display: block; }
.ldev-services {
  display: flex;
  justify-content: space-around;
  gap: 12px;
  flex-wrap: wrap;
}
.ldev-services .aws-node { flex: 1; min-width: 120px; max-width: 160px; }
.ldev-docker-badge {
  margin-top: 10px;
  text-align: center;
  font-size: 11px;
  color: #94a3b8;
  border: 1px dashed #e2e8f0;
  border-radius: 6px;
  padding: 4px 12px;
  display: inline-block;
  align-self: center;
  width: fit-content;
  margin-left: auto;
  margin-right: auto;
}

/* ── Legend ── */
.aws-legend {
  display: flex; gap: 12px; margin-top: 20px; padding-top: 16px;
  border-top: 1px solid #e2e8f0; flex-wrap: wrap;
}
.legend-item {
  font-size: 11px; font-weight: 500; color: #64748b;
  padding: 3px 10px; border-radius: 20px; border: 1px solid;
}
.legend-item.compute  { border-color: #FF9900; color: #c67600; background: #fff7ed; }
.legend-item.database { border-color: #336791; color: #336791; background: #eff6ff; }
.legend-item.storage  { border-color: #7AA116; color: #5a7a11; background: #f0fdf4; }
.legend-item.network  { border-color: #6366f1; color: #6366f1; background: #eef2ff; }
.legend-item.obs      { border-color: #a855f7; color: #a855f7; background: #fdf4ff; }
"""

SHELL_HTML = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>spring-backend-template docs</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+KR:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/java.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/sql.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/bash.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/yaml.min.js"></script>
<style>
:root {
  --bg: #fafafa;
  --sidebar-bg: #0f0f0f;
  --sidebar-w: 248px;
  --accent: #6366f1;
  --text: #111;
  --text-secondary: #6b7280;
  --border: #e5e7eb;
  --radius: 10px;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Noto Sans KR', 'Inter', sans-serif;
  background: var(--bg);
  color: var(--text);
  display: flex;
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
}

/* ── Sidebar ── */
.sidebar {
  width: var(--sidebar-w);
  min-height: 100vh;
  background: var(--sidebar-bg);
  padding: 24px 12px;
  position: fixed;
  top: 0; left: 0;
  overflow-y: auto;
  border-right: 1px solid #1f1f1f;
}
.sidebar-brand {
  padding: 4px 10px 20px;
  border-bottom: 1px solid #222;
  margin-bottom: 12px;
}
.sidebar-brand .name {
  font-size: 13px;
  font-weight: 700;
  color: #f9fafb;
  letter-spacing: -.2px;
}
.sidebar-brand .sub {
  font-size: 11px;
  color: #6b7280;
  margin-top: 3px;
}
.nav-group {
  font-size: 10px;
  font-weight: 600;
  color: #4b5563;
  letter-spacing: 1px;
  text-transform: uppercase;
  padding: 14px 10px 6px;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #9ca3af;
  padding: 7px 10px;
  border-radius: 7px;
  font-size: 13px;
  cursor: pointer;
  transition: background .12s, color .12s;
  text-decoration: none;
  margin-bottom: 1px;
}
.nav-item:hover { background: #1a1a1a; color: #e5e7eb; }
.nav-item.active {
  background: #1e1b4b;
  color: #a5b4fc;
  font-weight: 500;
}
.nav-item .dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #374151;
  flex-shrink: 0;
}
.nav-item.active .dot { background: var(--accent); }

/* ── Main ── */
.main { margin-left: var(--sidebar-w); flex: 1; min-width: 0; }

/* ── Post Header ── */
.post-header {
  padding: 56px 48px 44px;
  border-bottom: 1px solid var(--border);
  background: white;
  position: relative;
  overflow: hidden;
}
.post-header::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: linear-gradient(90deg, #6366f1, #8b5cf6, #d946ef);
}
.post-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  color: #6366f1;
  background: #eef2ff;
  padding: 4px 10px;
  border-radius: 20px;
  margin-bottom: 14px;
  letter-spacing: .3px;
}
.post-header h1 {
  font-size: 34px;
  font-weight: 700;
  color: #0f0f0f;
  line-height: 1.25;
  letter-spacing: -.5px;
  margin-bottom: 12px;
}
.post-header .desc {
  font-size: 15px;
  color: #6b7280;
  line-height: 1.7;
  max-width: 580px;
}

/* ── Post Body ── */
.post-body {
  margin: 40px 48px 80px;
  padding: 0;
  line-height: 1.8;
  font-size: 15px;
}

/* Typography */
.post-body h1 { display: none; }
.post-body h2 {
  font-size: 20px;
  font-weight: 700;
  color: #0f0f0f;
  margin: 52px 0 14px;
  letter-spacing: -.3px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.post-body h2::before {
  content: '';
  display: inline-block;
  width: 4px; height: 20px;
  background: linear-gradient(180deg, #6366f1, #8b5cf6);
  border-radius: 2px;
  flex-shrink: 0;
}
.post-body h2:first-of-type { margin-top: 0; }
.post-body h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 32px 0 10px;
  letter-spacing: -.2px;
}
.post-body h4 {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin: 22px 0 8px;
}
.post-body p { margin: 0 0 14px; color: #374151; }
.post-body ul, .post-body ol { margin: 0 0 14px 22px; color: #374151; }
.post-body li { margin-bottom: 5px; }
.post-body strong { color: #111; font-weight: 600; }

/* Inline code */
.post-body :not(pre) > code {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12.5px;
  background: #f3f4f6;
  color: #6366f1;
  padding: 2px 6px;
  border-radius: 5px;
  border: 1px solid #e5e7eb;
}

/* Code block */
.post-body pre {
  margin: 20px 0;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid #1f1f1f;
}
.post-body pre code {
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  line-height: 1.65;
  background: none !important;
  padding: 20px 24px !important;
  display: block;
}

/* Table */
.post-body table {
  width: 100%;
  border-collapse: collapse;
  margin: 20px 0;
  font-size: 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}
.post-body th {
  background: #f9fafb;
  padding: 10px 16px;
  text-align: left;
  font-weight: 600;
  color: #374151;
  border-bottom: 1px solid var(--border);
  font-size: 13px;
}
.post-body td {
  padding: 10px 16px;
  border-bottom: 1px solid #f3f4f6;
  color: #4b5563;
  vertical-align: top;
}
.post-body tr:last-child td { border-bottom: none; }
.post-body tr:hover td { background: #fafafa; }

/* Blockquote */
.post-body blockquote {
  border-left: 3px solid #6366f1;
  background: #fafafa;
  border-radius: 0 8px 8px 0;
  padding: 14px 18px;
  margin: 20px 0;
  color: #4b5563;
  font-size: 14px;
}

/* HR */
.post-body hr { border: none; border-top: 1px solid var(--border); margin: 40px 0; }
.post-body a { color: #6366f1; text-decoration: none; }
.post-body a:hover { text-decoration: underline; }

/* AWS diagram injected styles */
AWSCSS_PLACEHOLDER
</style>
</head>
<body>

<nav class="sidebar">
  <div class="sidebar-brand">
    <div class="name">spring-backend-template</div>
    <div class="sub">Architecture Docs</div>
  </div>

  <div class="nav-group">핵심 문서</div>
  <a class="nav-item" data-doc="architecture.md"><span class="dot"></span>Architecture</a>
  <a class="nav-item" data-doc="philosophy.md"><span class="dot"></span>Philosophy</a>
  <a class="nav-item" data-doc="infrastructure.md"><span class="dot"></span>Infrastructure</a>

  <div class="nav-group">컨벤션</div>
  <a class="nav-item" data-doc="conventions/design-principles.md"><span class="dot"></span>Design Principles</a>
  <a class="nav-item" data-doc="conventions/exception-handling.md"><span class="dot"></span>Exception Handling</a>
  <a class="nav-item" data-doc="conventions/contract-testing.md"><span class="dot"></span>Contract Testing</a>
  <a class="nav-item" data-doc="conventions/module-dependencies.md"><span class="dot"></span>Module Dependencies</a>

  <div class="nav-group">가이드</div>
  <a class="nav-item" data-doc="guides/deployment.md"><span class="dot"></span>Deployment</a>
  <a class="nav-item" data-doc="guides/onboarding.md"><span class="dot"></span>Onboarding</a>
  <a class="nav-item" data-doc="guides/mac-mini-setup.md"><span class="dot"></span>Mac Mini Setup</a>
</nav>

<main class="main">
  <div class="post-header">
    <div class="post-tag">spring-backend-template</div>
    <h1 id="post-title">Loading...</h1>
    <p class="desc" id="post-desc"></p>
  </div>
  <article class="post-body" id="content">
    <p style="color:#9ca3af;text-align:center;padding:60px 0">문서를 선택하세요</p>
  </article>
</main>

<script>
const META = {
  'architecture.md':    { title: 'Architecture Reference',   desc: '모듈 구조, 파일 트리, 의존 방향, DB 전략' },
  'philosophy.md':      { title: 'Repository Philosophy',    desc: '모듈러 모놀리스, 포트/어댑터, 앱별 독립 DB — 각 설계 결정의 이유' },
  'infrastructure.md':  { title: 'Infrastructure',           desc: '맥미니 홈서버, Supabase, Cloudflare Tunnel, 블루그린 배포' },
  'conventions/design-principles.md': { title: 'Design Principles', desc: '코드 작성 원칙' },
  'conventions/exception-handling.md': { title: 'Exception Handling', desc: '예외 처리 표준' },
  'conventions/contract-testing.md':  { title: 'Contract Testing', desc: '계약 기반 테스트 전략' },
  'conventions/module-dependencies.md': { title: 'Module Dependencies', desc: '모듈 의존 방향 규칙' },
  'guides/deployment.md':   { title: 'Deployment Guide',  desc: '배포 전략 및 운영 가이드' },
  'guides/onboarding.md':   { title: 'Onboarding',        desc: '신규 개발자 온보딩' },
  'guides/mac-mini-setup.md': { title: 'Mac Mini Setup',  desc: '홈서버 맥미니 셋업' },
};

marked.use({
  breaks: true,
  gfm: true,
  html: true,
  renderer: {
    code({ text, lang }) {
      if (!lang) lang = '';
      const validLang = lang && hljs.getLanguage(lang) ? lang : null;
      const highlighted = validLang
        ? hljs.highlight(text, { language: validLang }).value
        : (lang ? hljs.highlightAuto(text).value : text.replace(/&/g,'&amp;').replace(/</g,'&lt;'));
      const langLabel = lang ? `<div class="code-lang">${lang}</div>` : '';
      return `<div style="position:relative">${langLabel}<pre class="hljs"><code>${highlighted}</code></pre></div>`;
    }
  }
});

async function loadDoc(docPath) {
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.doc === docPath);
  });
  const meta = META[docPath] || { title: docPath, desc: '' };
  document.getElementById('post-title').textContent = meta.title;
  document.getElementById('post-desc').textContent = meta.desc;
  document.getElementById('content').innerHTML =
    '<p style="color:#9ca3af;text-align:center;padding:60px 0">로딩 중...</p>';

  try {
    const res = await fetch('/raw/' + docPath);
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const md = await res.text();
    document.getElementById('content').innerHTML = marked.parse(md);
    document.querySelectorAll('pre code').forEach(el => hljs.highlightElement(el));
    window.scrollTo(0, 0);
  } catch(e) {
    console.error(e);
    document.getElementById('content').innerHTML =
      `<p style="color:#ef4444;padding:20px">오류: ${e.message}</p>`;
  }
}

// 다이어그램 HTML — marked가 파싱하지 않도록 JS에서 직접 주입
const DIAGRAMS = {};
DIAGRAMS['LOCAL_DEV'] = `LOCALDEV_PLACEHOLDER`;
DIAGRAMS['PROD'] = `PROD_PLACEHOLDER`;

async function loadDoc(docPath) {
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.doc === docPath);
  });
  const meta = META[docPath] || { title: docPath, desc: '' };
  document.getElementById('post-title').textContent = meta.title;
  document.getElementById('post-desc').textContent = meta.desc;
  document.getElementById('content').innerHTML =
    '<p style="color:#9ca3af;text-align:center;padding:60px 0">로딩 중...</p>';

  try {
    const res = await fetch('/raw/' + docPath);
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const md = await res.text();
    let html = marked.parse(md);
    // 마커를 실제 다이어그램 HTML로 교체
    html = html.replace(/<p>%%LOCAL_DEV_DIAGRAM%%<\/p>/g, DIAGRAMS['LOCAL_DEV']);
    html = html.replace(/<p>%%PROD_DIAGRAM%%<\/p>/g, DIAGRAMS['PROD']);
    document.getElementById('content').innerHTML = html;
    document.querySelectorAll('pre code').forEach(el => hljs.highlightElement(el));
    window.scrollTo(0, 0);
  } catch(e) {
    console.error(e);
    document.getElementById('content').innerHTML =
      `<p style="color:#ef4444;padding:20px">오류: ${e.message}</p>`;
  }
}

document.querySelector('.sidebar').addEventListener('click', e => {
  const item = e.target.closest('.nav-item');
  if (item && item.dataset.doc) loadDoc(item.dataset.doc);
});

loadDoc('architecture.md');
</script>
</body>
</html>"""

import re, json

def _js_escape(s):
    return s.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')

SHELL_HTML = SHELL_HTML.replace('AWSCSS_PLACEHOLDER', AWS_CSS)
SHELL_HTML = SHELL_HTML.replace('LOCALDEV_PLACEHOLDER', _js_escape(LOCAL_DEV_DIAGRAM))
SHELL_HTML = SHELL_HTML.replace('PROD_PLACEHOLDER', _js_escape(PROD_DIAGRAM))

def inject_diagrams(content, rel_path):
    if rel_path != 'infrastructure.md':
        return content
    content = re.sub(
        r'```\n\[개발자 맥북\].*?```',
        '\n%%LOCAL_DEV_DIAGRAM%%\n',
        content, flags=re.DOTALL
    )
    content = re.sub(
        r'```\n\[인터넷 사용자\].*?```',
        '\n%%PROD_DIAGRAM%%\n',
        content, flags=re.DOTALL
    )
    return content


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass

    def do_GET(self):
        p = self.path
        if p in ('/', ''):
            self._send(200, 'text/html; charset=utf-8', SHELL_HTML.encode())
            return
        if p.startswith('/raw/'):
            rel = p[5:]
            fpath = os.path.join(DOCS_DIR, rel)
            if not os.path.isfile(fpath):
                self._send(404, 'text/plain', b'not found')
                return
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            content = inject_diagrams(content, rel)
            self._send(200, 'text/plain; charset=utf-8', content.encode('utf-8'))
            return
        self._send(200, 'text/html; charset=utf-8', SHELL_HTML.encode())

    def _send(self, code, ctype, body):
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"✅  http://localhost:{PORT}")
    httpd.serve_forever()
