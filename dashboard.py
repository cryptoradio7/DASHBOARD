#!/usr/bin/env python3
"""
Dashboard Agents — AgileVizion
Serveur local http://localhost:8787
Onglet 1: Agents (registry.json, statut systemd, controle ON/OFF)
Onglet 2: Config (skills, plugins, MCP, memoire, fichiers cles)
"""

import json, subprocess, os, sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from pathlib import Path
from urllib.request import Request, urlopen

AGENTS_DIR = Path.home() / "Bureau" / "agents-ia" / "agents"
REGISTRY = AGENTS_DIR / "registry.json"
CLAUDE_DIR = Path.home() / ".claude"
COMMANDS_DIR = CLAUDE_DIR / "commands"
MEMORY_DIR = CLAUDE_DIR / "projects" / "-home-egx" / "memory"
SETTINGS_FILE = CLAUDE_DIR / "settings.json"
CLAUDE_MD = CLAUDE_DIR / "CLAUDE.md"
APPS_DIR = Path.home() / "Bureau" / "APPS"
PORT = 8787

# ─── Apps configuration ───
APPS_CONFIG = [
    {
        "id": "agilevizion",
        "name": "AgileVizion",
        "desc": "Site de vente vertical agilevizion.com",
        "path": str(APPS_DIR / "agilevizion"),
        "type": "static",
        "port": 8001,
        "start": "python3 -m http.server 8001",
        "process_grep": "http.server 8001",
        "url": "http://localhost:8001",
        "icon": "🌐",
    },
    {
        "id": "cryptoradio",
        "name": "CryptoRadio",
        "desc": "Dashboard BTC Analyst — score 0-100, analyse IA",
        "path": str(APPS_DIR / "cryptoradio"),
        "type": "web",
        "port": 3000,
        "start": "bash start.sh",
        "process_grep": "uvicorn.*8000|next.*3000",
        "url": "http://localhost:3000",
        "icon": "📡",
    },
    {
        "id": "dashboard",
        "name": "Dashboard Agents",
        "desc": "Cockpit Claude Code — agents, config, MCP",
        "path": str(APPS_DIR / "DASHBOARD"),
        "type": "self",
        "port": 8787,
        "url": "http://localhost:8787",
        "icon": "⚙️",
    },
    {
        "id": "post-its",
        "name": "Post-its",
        "desc": "Post-its memo desktop (GTK)",
        "path": str(APPS_DIR / "post-its"),
        "type": "desktop",
        "start": "python3 src/main.py",
        "process_grep": "post-its/src/main.py",
        "icon": "📌",
    },
]

CSS = '''
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Segoe UI', system-ui, sans-serif;
    background: #0d1117;
    color: #c9d1d9;
    padding: 24px 32px;
  }
  h1 { color: #fff; font-size: 1.4rem; margin-bottom: 4px; }
  h2 { color: #fff; font-size: 1.1rem; margin: 24px 0 12px 0; }
  .subtitle { color: #8b949e; font-size: 0.85rem; margin-bottom: 16px; }
  .msg {
    background: #1a3c2a; color: #3fb950; padding: 8px 16px;
    border-radius: 6px; margin-bottom: 16px; font-size: 0.85rem;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
    margin-bottom: 8px;
  }
  thead th {
    background: #161b22;
    color: #8b949e;
    text-align: left;
    padding: 10px 12px;
    border-bottom: 2px solid #30363d;
    white-space: nowrap;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 0.72rem;
    letter-spacing: 0.5px;
  }
  tbody td {
    padding: 10px 12px;
    border-bottom: 1px solid #21262d;
    vertical-align: top;
  }
  tbody tr:hover { background: #161b22; }
  .col-name { white-space: nowrap; }
  .col-center { text-align: center; }
  .col-units { font-family: monospace; font-size: 0.75rem; color: #8b949e; }
  .col-stack { color: #8b949e; font-size: 0.78rem; }
  .col-cmds code {
    display: inline-block;
    background: #1a2a3c;
    color: #58a6ff;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.72rem;
    margin: 1px 0;
    white-space: nowrap;
  }
  table { table-layout: fixed; width: 100%; }
  thead th:nth-child(1) { width: 10%; }
  thead th:nth-child(2) { width: 28%; }
  thead th:nth-child(3) { width: 7%; }
  thead th:nth-child(4) { width: 38%; }
  thead th:nth-child(5) { width: 17%; }
  td { overflow: hidden; text-overflow: ellipsis; word-wrap: break-word; }
  td:nth-child(2) { overflow: visible; }

  .badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.72rem;
    font-weight: 600;
  }
  .bg-green  { background: #1a3c2a; color: #3fb950; }
  .bg-red    { background: #3c1a1a; color: #f85149; }
  .bg-gray   { background: #21262d; color: #8b949e; }
  .bg-purple { background: #2a1a3c; color: #bc8cff; }
  .bg-blue   { background: #1a2a3c; color: #58a6ff; }
  .bg-cyan   { background: #1a2c2c; color: #56d4d4; }

  .toggle-btn {
    border: none;
    padding: 5px 14px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.2s;
  }
  .toggle-btn:hover { opacity: 0.8; }
  .btn-on  { background: #1a3c2a; color: #3fb950; }
  .btn-off { background: #3c1a1a; color: #f85149; }
  .muted { color: #484f58; }
  .dir-link {
    color: #8b949e;
    text-decoration: none;
    font-size: 0.72rem;
    font-family: monospace;
  }
  .dir-link:hover { color: #58a6ff; }
  .billing-link {
    color: #58a6ff;
    text-decoration: none;
    font-size: 0.85rem;
    padding: 6px 14px;
    border: 1px solid #30363d;
    border-radius: 6px;
    white-space: nowrap;
    transition: border-color 0.2s;
  }
  .billing-link:hover { border-color: #58a6ff; }

  .tabs {
    display: flex;
    gap: 0;
    margin-bottom: 20px;
    border-bottom: 2px solid #30363d;
  }
  .tab {
    padding: 10px 24px;
    color: #8b949e;
    text-decoration: none;
    font-size: 0.9rem;
    font-weight: 600;
    border-bottom: 2px solid transparent;
    margin-bottom: -2px;
    transition: color 0.2s, border-color 0.2s;
  }
  .tab:hover { color: #c9d1d9; }
  .tab.active { color: #58a6ff; border-bottom-color: #58a6ff; }

  .card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
  }
  .card h3 {
    color: #58a6ff;
    font-size: 0.85rem;
    margin-bottom: 10px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .grid-2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }
  .grid-3 {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 16px;
  }
  .mono { font-family: monospace; font-size: 0.78rem; }
  .path { color: #8b949e; font-family: monospace; font-size: 0.72rem; }
  .count { color: #3fb950; font-size: 1.4rem; font-weight: 700; }
  .label { color: #8b949e; font-size: 0.75rem; margin-top: 2px; }
  .rule { color: #f0883e; font-size: 0.8rem; margin: 4px 0; }

  .section-nav {
    position: sticky;
    top: 0;
    z-index: 100;
    background: #0d1117;
    border-bottom: 1px solid #30363d;
    padding: 8px 0;
    margin-bottom: 16px;
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
  }
  .section-nav a {
    color: #8b949e;
    text-decoration: none;
    font-size: 0.75rem;
    padding: 4px 12px;
    border-radius: 12px;
    background: #161b22;
    border: 1px solid #30363d;
    transition: all 0.2s;
  }
  .section-nav a:hover {
    color: #58a6ff;
    border-color: #58a6ff;
  }

  details.agent-details {
    margin-top: 8px;
  }
  details.agent-details summary {
    color: #58a6ff;
    font-size: 0.75rem;
    cursor: pointer;
    list-style: none;
  }
  details.agent-details summary::-webkit-details-marker { display: none; }
  details.agent-details summary::before { content: "[details]"; }
  details.agent-details[open] summary::before { content: "[masquer]"; }
  details.agent-details summary:hover { text-decoration: underline; }
  details.agent-details .details-body {
    margin-top: 10px;
    padding: 14px 16px;
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    font-size: 0.8rem;
    line-height: 1.5;
    color: #c9d1d9;
  }
  .phase-title {
    color: #e6edf3;
    font-weight: 700;
    font-size: 0.82rem;
    margin-top: 16px;
    margin-bottom: 6px;
    padding: 4px 8px;
    background: #21262d;
    border-radius: 4px;
    border-left: 3px solid #58a6ff;
  }
  .phase-title:first-child { margin-top: 0; }
  .step-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  .step-list li {
    color: #c9d1d9;
    padding: 3px 0 3px 12px;
    line-height: 1.7;
  }
  .step-list li::before {
    content: "—";
    color: #484f58;
    margin-right: 6px;
  }

  .footer {
    margin-top: 20px;
    color: #484f58;
    font-size: 0.75rem;
    text-align: center;
  }
'''


def load_registry():
    with open(REGISTRY) as f:
        return json.load(f)


def get_unit_status(unit_name):
    try:
        r = subprocess.run(
            ["systemctl", "--user", "is-active", unit_name],
            capture_output=True, text=True, timeout=5
        )
        return r.stdout.strip()
    except Exception:
        return "unknown"


def get_unit_enabled(unit_name):
    try:
        r = subprocess.run(
            ["systemctl", "--user", "is-enabled", unit_name],
            capture_output=True, text=True, timeout=5
        )
        return r.stdout.strip()
    except Exception:
        return "unknown"


def get_agent_status(agent):
    if agent["type"] == "manual":
        return "manual"
    if agent["type"] == "interactive":
        return "interactive"
    if agent["type"] == "autostart":
        return "autostart"
    # Agents VPS : pas de systemctl local, on indique "vps"
    if agent.get("source") == "vps":
        return "vps"
    units = agent["timers"] + agent["services"]
    if not units:
        return "manual"
    statuses = [get_unit_status(u) for u in units]
    if "active" in statuses:
        return "active"
    if "failed" in statuses:
        return "failed"
    enabled = [get_unit_enabled(u) for u in units]
    if "enabled" in enabled:
        return "active"
    return "inactive"


# ─── Apps management ───

def get_app_status(app):
    """Check if an app is running."""
    if app["type"] == "self":
        return "running"  # dashboard is always running if we're here
    grep_pattern = app.get("process_grep", "")
    if not grep_pattern:
        return "stopped"
    try:
        r = subprocess.run(
            ["pgrep", "-f", grep_pattern.split("|")[0]],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0 and r.stdout.strip():
            return "running"
        # Try other patterns if pipe-separated
        for pattern in grep_pattern.split("|")[1:]:
            r2 = subprocess.run(
                ["pgrep", "-f", pattern],
                capture_output=True, text=True, timeout=5
            )
            if r2.returncode == 0 and r2.stdout.strip():
                return "running"
    except Exception:
        pass
    return "stopped"


def start_app(app_id):
    app = next((a for a in APPS_CONFIG if a["id"] == app_id), None)
    if not app:
        return f"App {app_id} introuvable"
    if app["type"] == "self":
        return "Dashboard deja en cours"
    if get_app_status(app) == "running":
        return f"{app['name']} deja en cours"
    start_cmd = app.get("start", "")
    if not start_cmd:
        return f"Pas de commande de demarrage pour {app['name']}"
    log_path = Path(app["path"]) / "logs"
    log_path.mkdir(exist_ok=True)
    log_file = log_path / "dashboard-launch.log"
    try:
        with open(log_file, "a") as lf:
            subprocess.Popen(
                start_cmd, shell=True, cwd=app["path"],
                stdout=lf, stderr=lf,
                start_new_session=True
            )
        return f"{app['name']} demarre"
    except Exception as e:
        return f"Erreur demarrage {app['name']}: {e}"


def stop_app(app_id):
    app = next((a for a in APPS_CONFIG if a["id"] == app_id), None)
    if not app:
        return f"App {app_id} introuvable"
    if app["type"] == "self":
        return "Impossible d'arreter le dashboard depuis le dashboard"
    grep_pattern = app.get("process_grep", "")
    if not grep_pattern:
        return f"Pas de pattern pour {app['name']}"
    killed = []
    for pattern in grep_pattern.split("|"):
        try:
            r = subprocess.run(
                ["pgrep", "-f", pattern],
                capture_output=True, text=True, timeout=5
            )
            for pid in r.stdout.strip().split("\n"):
                if pid:
                    subprocess.run(["kill", pid], capture_output=True, timeout=5)
                    killed.append(pid)
        except Exception:
            pass
    if killed:
        return f"{app['name']} arrete (PID: {', '.join(killed)})"
    return f"{app['name']} n'etait pas en cours"


def toggle_agent(agent_id, action):
    agents = load_registry()
    agent = next((a for a in agents if a["id"] == agent_id), None)
    if not agent:
        return f"Agent {agent_id} introuvable"
    if agent["type"] == "manual":
        return "Agent manuel — pas de service a basculer"
    if agent["type"] == "interactive":
        return "Agent interactif — lance /audit-grc dans Claude Code"

    results = []
    timers = agent.get("timers", [])
    services = agent.get("services", [])

    if action == "on":
        for t in timers:
            subprocess.run(["systemctl", "--user", "enable", "--now", t], capture_output=True)
            results.append(f"Timer {t} active")
        if not timers:
            for s in services:
                subprocess.run(["systemctl", "--user", "enable", "--now", s], capture_output=True)
                results.append(f"Service {s} active")
    else:
        for t in timers:
            subprocess.run(["systemctl", "--user", "disable", "--now", t], capture_output=True)
            results.append(f"Timer {t} desactive")
        for s in services:
            subprocess.run(["systemctl", "--user", "stop", s], capture_output=True)
            results.append(f"Service {s} arrete")
        if not timers:
            for s in services:
                subprocess.run(["systemctl", "--user", "disable", s], capture_output=True)
                results.append(f"Service {s} desactive")

    return " | ".join(results)


# ─── Collecte config ───

def get_skills():
    """Liste des skills disponibles."""
    skills = []
    if COMMANDS_DIR.exists():
        for f in sorted(COMMANDS_DIR.iterdir()):
            if f.suffix == ".md":
                name = f.stem
                target = str(f.resolve()) if f.is_symlink() else str(f)
                broken = f.is_symlink() and not f.exists()
                # Lire 1ere ligne pour description
                desc = ""
                if not broken:
                    try:
                        with open(f) as fh:
                            first = fh.readline().strip()
                            if first.startswith("---"):
                                # YAML frontmatter, chercher description
                                for line in fh:
                                    if line.startswith("description:"):
                                        desc = line.split(":", 1)[1].strip()
                                        break
                                    if line.startswith("---"):
                                        break
                            else:
                                desc = first
                    except Exception:
                        pass
                skills.append({"name": name, "desc": desc, "broken": broken, "path": target})
    return skills


def get_plugins():
    """Plugins actifs depuis settings.json."""
    plugins = []
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE) as f:
                data = json.load(f)
            for name, enabled in data.get("enabledPlugins", {}).items():
                plugins.append({"name": name.replace("@claude-plugins-official", "").strip("@"), "enabled": enabled})
        except Exception:
            pass
    return plugins


def get_memory_files():
    """Fichiers memoire."""
    files = []
    if MEMORY_DIR.exists():
        for f in sorted(MEMORY_DIR.iterdir()):
            if f.suffix == ".md" and f.name != "MEMORY.md":
                # Lire type depuis frontmatter
                mtype = ""
                desc = ""
                try:
                    with open(f) as fh:
                        in_fm = False
                        for line in fh:
                            if line.strip() == "---" and not in_fm:
                                in_fm = True
                                continue
                            if line.strip() == "---" and in_fm:
                                break
                            if in_fm and line.startswith("type:"):
                                mtype = line.split(":", 1)[1].strip()
                            if in_fm and line.startswith("description:"):
                                desc = line.split(":", 1)[1].strip()
                except Exception:
                    pass
                files.append({"name": f.stem, "type": mtype, "desc": desc})
    return files


def get_permissions():
    """Regles allow/deny depuis settings.json."""
    allow = []
    deny = []
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE) as f:
                data = json.load(f)
            perms = data.get("permissions", {})
            allow = perms.get("allow", [])
            deny = perms.get("deny", [])
        except Exception:
            pass
    return allow, deny


def get_claude_md_rules():
    """Extraire les regles OBLIGATOIRE du CLAUDE.md."""
    rules = []
    if CLAUDE_MD.exists():
        try:
            with open(CLAUDE_MD) as f:
                current_section = ""
                for line in f:
                    if line.startswith("## ") and "OBLIGATOIRE" in line:
                        current_section = line.strip().replace("## ", "")
                    elif line.startswith("## ") and "OBLIGATOIRE" not in line:
                        current_section = ""
                    elif current_section and line.startswith("- "):
                        rules.append({"section": current_section, "rule": line.strip()[2:]})
        except Exception:
            pass
    return rules


def get_key_files():
    """Fichiers de configuration cles."""
    files = [
        ("CLAUDE.md global", "~/.claude/CLAUDE.md", "Regles globales, identite, securite, conventions — charge a chaque session"),
        ("Settings", "~/.claude/settings.json", "Permissions bash (allow/deny), plugins actifs, config Claude Code"),
        ("Skills", "~/.claude/commands/", "Dossier des slash commands (/mail, /veille, /cockpit, etc.)"),
        ("Memoire", "~/.claude/projects/-home-egx/memory/", "Memoire persistante entre sessions (feedback, references, projets)"),
        ("Secrets (GPG)", "~/.claude/secrets/web-credentials.gpg", "Tous les credentials chiffres (12 services) — source unique"),
        ("Registry agents", "~/Bureau/agents-ia/agents/registry.json", "Catalogue des agents (statut, services systemd, stack)"),
        ("Guide Agent Optimal", "~/Bureau/agents-ia/docs/guides/guide_agent_optimal.md", "Source of truth — construire un agent optimal (anatomie, questionnaire 9 blocs, orchestration)"),
        ("Infrastructure Client", "~/Bureau/agents-ia/docs/guides/infrastructure_client.md", "Architecture deploiement client (Docker, OpenClaw, AWS, backup)"),
        ("Templates Agent", "~/Bureau/agents-ia/docs/templates/", "Squelettes T01-T08 pour /init-agent (CLAUDE.md, SPECS, SKILL, state, hooks, .gitignore)"),
        ("Services web", "~/Bureau/agents-ia/agents/web-login/context/services.json", "URLs des services web pour ouverture navigateur (8 sites)"),
    ]
    result = []
    for label, path, desc in files:
        expanded = Path(path.replace("~", str(Path.home())))
        exists = expanded.exists()
        full_path = str(expanded)
        result.append({"label": label, "path": path, "full_path": full_path, "desc": desc, "exists": exists})
    return result


def get_gpg_services():
    """Liste des services dans le GPG (noms seulement)."""
    try:
        r = subprocess.run(
            ["gpg", "--quiet", "--decrypt", str(Path.home() / ".claude/secrets/web-credentials.gpg")],
            capture_output=True, text=True, timeout=10
        )
        if r.returncode == 0:
            data = json.loads(r.stdout)
            return [k for k in data.keys()]
    except Exception:
        pass
    return []


def get_mcp_servers():
    """Serveurs MCP installes depuis .mcp.json."""
    mcp_file = CLAUDE_DIR / ".mcp.json"
    servers = []
    if mcp_file.exists():
        try:
            with open(mcp_file) as f:
                data = json.load(f)
            for name, conf in data.get("mcpServers", {}).items():
                cmd = conf.get("command", "")
                args = conf.get("args", [])
                # Extraire un résumé lisible
                if args:
                    detail = " ".join(str(a) for a in args[:2])
                else:
                    detail = cmd
                servers.append({"name": name, "command": cmd, "detail": detail})
        except Exception:
            pass
    return servers


def get_version():
    try:
        r = subprocess.run(["claude", "--version"], capture_output=True, text=True, timeout=5)
        return r.stdout.strip()
    except Exception:
        return "?"


# ─── HTML builders ───

def get_deepseek_balance():
    """Recupere le solde DeepSeek via API"""
    try:
        creds = json.loads(subprocess.check_output(
            ["gpg", "--quiet", "--decrypt", str(Path.home() / ".claude/secrets/web-credentials.gpg")],
            stderr=subprocess.DEVNULL
        ))
        api_key = creds["deepseek"]["api_key"]
        req = Request("https://api.deepseek.com/user/balance",
                       headers={"Authorization": f"Bearer {api_key}"})
        resp = json.loads(urlopen(req, timeout=5).read())
        if resp.get("balance_infos"):
            return resp["balance_infos"][0]["total_balance"]
    except Exception:
        pass
    return None


def build_header(active_tab="agents"):
    tab_agents = "active" if active_tab == "agents" else ""
    tab_apps = "active" if active_tab == "apps" else ""
    tab_config = "active" if active_tab == "config" else ""
    deepseek_bal = get_deepseek_balance()
    # Section nav only on config page
    section_nav = ""
    if active_tab == "config":
        section_nav = '''
<nav class="section-nav">
  <a href="#guide">Guide</a>
  <a href="#skills">Skills</a>
  <a href="#plugins">Plugins</a>
  <a href="#mcp">MCP</a>
  <a href="#gpg">Credentials</a>
  <a href="#memory">Memoire</a>
  <a href="#tools">Tools</a>
  <a href="#rules">Regles</a>
  <a href="#files">Fichiers</a>
</nav>'''
    return f'''
<div style="display:flex;justify-content:space-between;align-items:start">
  <div>
    <h1>Dashboard — AgileVizion</h1>
    <p class="subtitle">Cockpit Claude Code &middot; <a href="/" style="color:#58a6ff">Actualiser</a></p>
  </div>
  <div style="display:flex;gap:10px">
    <a href="https://claude.ai/settings/usage" target="_blank" class="billing-link">Forfait Claude &rarr;</a>
    <a href="https://console.anthropic.com/settings/billing" target="_blank" class="billing-link">Claude API &rarr;</a>
    <a href="https://platform.deepseek.com/usage" target="_blank" class="billing-link">DeepSeek API{f" (${deepseek_bal})" if deepseek_bal else ""} &rarr;</a>
  </div>
</div>
<div class="tabs">
  <a href="/" class="tab {tab_agents}">Agents</a>
  <a href="/apps" class="tab {tab_apps}">Apps</a>
  <a href="/config" class="tab {tab_config}">Config</a>
</div>
{section_nav}'''


def build_agents_html(msg_html=""):
    all_agents = load_registry()
    pinned = [a for a in all_agents if a["id"] == "init-agent"]
    others = sorted([a for a in all_agents if a["id"] != "init-agent"], key=lambda a: a["name"].lower())
    agents = pinned + others

    rows = ""
    for a in agents:
        automation = a.get("automation", "—")
        tooltip_raw = a.get("tooltip", "")
        source = a.get("source", "local")

        row_style = ' style="background:#1a2a2a"' if a["id"] == "init-agent" else ""

        # Build description cell with optional expandable details
        if tooltip_raw:
            lines = tooltip_raw.split("\n")
            body_html = ""
            in_list = False
            for line in lines:
                line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                if line.startswith("PHASE") or line.startswith("BLOC"):
                    if in_list:
                        body_html += "</ul>"
                        in_list = False
                    body_html += f'<div class="phase-title">{line}</div>'
                elif line.strip() == "":
                    if in_list:
                        body_html += "</ul>"
                        in_list = False
                else:
                    if not in_list:
                        body_html += '<ul class="step-list">'
                        in_list = True
                    body_html += f"<li>{line}</li>"
            if in_list:
                body_html += "</ul>"
            desc_cell = f'''{a['description']}<details class="agent-details"><summary></summary><div class="details-body">{body_html}</div></details>'''
        else:
            desc_cell = a['description']

        source_badge = '<span class="badge bg-blue">VPS</span>' if source == "vps" else '<span class="badge bg-gray">Local</span>'

        rows += f'''
        <tr{row_style}>
          <td class="col-name"><strong>{a['name']}</strong></td>
          <td>{desc_cell}</td>
          <td class="col-center">{source_badge}</td>
          <td>{automation}</td>
          <td class="col-stack">{a['stack']}</td>
        </tr>'''

    return f'''{msg_html}
<table>
  <thead>
    <tr>
      <th>Agent</th>
      <th>Description</th>
      <th>Source</th>
      <th>Automatisation</th>
      <th>Stack</th>
    </tr>
  </thead>
  <tbody>
    {rows}
  </tbody>
</table>'''


def build_config_html():
    version = get_version()
    skills = get_skills()
    plugins = get_plugins()
    memories = get_memory_files()
    allow, deny = get_permissions()
    rules = get_claude_md_rules()
    key_files = get_key_files()
    gpg_services = get_gpg_services()

    # Compteurs
    n_skills = len(skills)
    n_broken = sum(1 for s in skills if s["broken"])
    n_plugins = len(plugins)
    n_memories = len(memories)
    n_rules = len(rules)
    n_gpg = len(gpg_services)

    # Guide explicatif
    home = str(Path.home())
    guide_html = f'''
<div class="card" id="guide">
  <h3>Comment ca marche</h3>
  <table>
    <thead><tr><th style="width:130px">Concept</th><th>C\'est quoi</th><th>Exemple</th></tr></thead>
    <tbody>
      <tr>
        <td><strong style="color:#58a6ff">Skills</strong></td>
        <td>Commandes slash (<code>/nom</code>) qui injectent un prompt specialise dans la conversation. Fichiers Markdown dans <a href="file://{home}/.claude/commands/" class="dir-link">~/.claude/commands/</a>.</td>
        <td><code>/mail</code> = envoi d\'email, <code>/cockpit</code> = etat systeme</td>
      </tr>
      <tr>
        <td><strong style="color:#58a6ff">Plugins</strong></td>
        <td>Extensions npm (<code>@claude-plugins</code>) qui ajoutent des capacites natives a Claude Code : nouvelles commandes, hooks, integrations.</td>
        <td><strong>Playwright</strong> = navigateur, <strong>Context7</strong> = doc librairies</td>
      </tr>
      <tr>
        <td><strong style="color:#58a6ff">MCP</strong></td>
        <td>Serveurs externes qui exposent des <em>tools</em> a Claude via le protocole MCP. Configures dans <a href="file://{home}/.claude/.mcp.json" class="dir-link">~/.claude/.mcp.json</a>.</td>
        <td>Serveur <strong>Figma</strong> = designs, <strong>SQLite</strong> = base locale</td>
      </tr>
      <tr>
        <td><strong style="color:#58a6ff">Tools</strong></td>
        <td>Commandes bash autorisees ou interdites dans le terminal. Permissions dans <a href="file://{home}/.claude/settings.json" class="dir-link">~/.claude/settings.json</a>.</td>
        <td><code>git *</code> autorise, <code>rm -rf /</code> interdit</td>
      </tr>
      <tr>
        <td><strong style="color:#58a6ff">Agents</strong></td>
        <td>Services automatises via systemd (timers/cron). Geres depuis l\'onglet Agents. Registry dans <a href="file://{home}/Bureau/agents-ia/agents/registry.json" class="dir-link">registry.json</a>.</td>
        <td><strong>Veille cyber</strong> = newsletter 6h30, <strong>web-login</strong> = connexion sites</td>
      </tr>
      <tr>
        <td><strong style="color:#58a6ff">Memoire</strong></td>
        <td>Fichiers Markdown persistants entre sessions. Indexes dans <a href="file://{home}/.claude/projects/-home-egx/memory/MEMORY.md" class="dir-link">MEMORY.md</a>.</td>
        <td>Feedback style de reponse, reference agent mail</td>
      </tr>
      <tr>
        <td><strong style="color:#58a6ff">Credentials</strong></td>
        <td>Secrets chiffres dans un fichier GPG unique. Jamais en clair, jamais dans le code ou la memoire.</td>
        <td>Login WorkMail, cle API Anthropic, tokens LinkedIn</td>
      </tr>
      <tr>
        <td><strong style="color:#58a6ff">CLAUDE.md</strong></td>
        <td>Fichier d\'instructions charge a chaque session. Regles obligatoires et conventions. <a href="file://{home}/.claude/CLAUDE.md" class="dir-link">~/.claude/CLAUDE.md</a></td>
        <td>Securite credentials, actions externes, standards de code</td>
      </tr>
      <tr>
        <td><strong style="color:#58a6ff">Init-Agent</strong></td>
        <td>Createur d\'agents via questionnaire interactif 9 blocs (persona, autonomie, orchestration). Utilise les <a href="file://{home}/Bureau/agents-ia/docs/templates/" class="dir-link">templates T01-T08</a> et le <a href="file://{home}/Bureau/agents-ia/docs/guides/guide_agent_optimal.md" class="dir-link">guide optimal</a>.</td>
        <td><code>/init-agent</code> dans Claude Code</td>
      </tr>
      <tr>
        <td><strong style="color:#58a6ff">Infra Client</strong></td>
        <td>Architecture deploiement : containers Docker isoles par client, OpenClaw (Discord/Teams), backup 3 niveaux. <a href="file://{home}/Bureau/agents-ia/docs/guides/infrastructure_client.md" class="dir-link">infrastructure_client.md</a></td>
        <td>AWS EC2 + Docker + OpenClaw</td>
      </tr>
    </tbody>
  </table>
</div>'''

    stats = ""

    # Skills table
    skill_rows = ""
    for s in skills:
        status = '<span class="badge bg-red">CASSEE</span>' if s["broken"] else '<span class="badge bg-green">OK</span>'
        desc = s["desc"][:80] if s["desc"] else '<span class="muted">—</span>'
        skill_rows += f'<tr><td class="mono">/{s["name"]}</td><td>{desc}</td><td class="col-center">{status}</td></tr>'

    skills_html = f'''
<div class="card" id="skills">
  <h3>Skills ({n_skills} installees)</h3>
  <p class="path" style="margin-bottom:8px"><a href="file://{home}/.claude/commands/" class="dir-link">~/.claude/commands/</a> &middot; Creer une skill : <code>/skill-creator</code></p>
  <table>
    <thead><tr><th>Commande</th><th>Description</th><th>Statut</th></tr></thead>
    <tbody>{skill_rows}</tbody>
  </table>
</div>'''

    # Plugins table + annuaires plugins
    plugin_rows = ""
    for p in plugins:
        badge = '<span class="badge bg-green">ON</span>' if p["enabled"] else '<span class="badge bg-gray">OFF</span>'
        plugin_rows += f'<tr><td class="mono">{p["name"]}</td><td class="col-center">{badge}</td><td></td></tr>'

    plugin_annuaires = [
        ("Claude Code Plugins (npm)", "https://www.npmjs.com/search?q=%40claude-plugins", "Plugins officiels sur npm"),
        ("Anthropic Docs — Plugins", "https://docs.anthropic.com/en/docs/claude-code/plugins", "Documentation officielle"),
    ]
    for name, url, desc in plugin_annuaires:
        plugin_rows += f'<tr><td><a href="{url}" target="_blank" style="color:#58a6ff;text-decoration:none">{name}</a></td><td class="col-center"><span class="badge bg-purple">ANNUAIRE</span></td><td style="color:#8b949e;font-size:0.78rem">{desc}</td></tr>'

    plugins_html = f'''
<div class="card" id="plugins">
  <h3>Plugins</h3>
  <table>
    <thead><tr><th>Plugin</th><th>Statut</th><th>Description</th></tr></thead>
    <tbody>{plugin_rows}</tbody>
  </table>
</div>'''

    # MCP servers + annuaires
    mcp_servers = get_mcp_servers()
    mcp_rows = ""
    for s in mcp_servers:
        mcp_rows += f'<tr><td class="mono">{s["name"]}</td><td><code>{s["command"]}</code></td><td class="col-center"><span class="badge bg-green">INSTALLE</span></td></tr>'

    mcp_annuaires = [
        ("Smithery", "https://smithery.ai/", "Annuaire principal — recherche, installation, reviews"),
        ("MCP.so", "https://mcp.so/", "Communautaire — classement par categorie"),
        ("Glama MCP", "https://glama.ai/mcp/servers", "Catalogue avec documentation et exemples"),
        ("PulseMCP", "https://www.pulsemcp.com/", "Classement par popularite et tendances"),
        ("MCP Hub", "https://www.mcphub.tools/", "Hub centralise — recherche et filtrage"),
        ("Awesome MCP Servers", "https://github.com/punkpeye/awesome-mcp-servers", "Liste curatee GitHub"),
        ("Anthropic Docs — MCP", "https://modelcontextprotocol.io/", "Documentation officielle du protocole"),
    ]
    for name, url, desc in mcp_annuaires:
        mcp_rows += f'<tr><td><a href="{url}" target="_blank" style="color:#58a6ff;text-decoration:none">{name}</a></td><td style="color:#8b949e;font-size:0.78rem">{desc}</td><td class="col-center"><span class="badge bg-purple">ANNUAIRE</span></td></tr>'

    mcp_html = f'''
<div class="card" id="mcp">
  <h3>Serveurs MCP ({len(mcp_servers)} installes)</h3>
  <p class="path" style="margin-bottom:8px"><a href="file://{home}/.claude/.mcp.json" class="dir-link">~/.claude/.mcp.json</a></p>
  <table>
    <thead><tr><th>Serveur</th><th>Commande / Description</th><th>Statut</th></tr></thead>
    <tbody>{mcp_rows}</tbody>
  </table>
</div>'''

    # GPG services
    gpg_rows = ""
    for svc in sorted(gpg_services):
        gpg_rows += f'<tr><td class="mono">{svc}</td></tr>'

    gpg_html = f'''
<div class="card" id="gpg">
  <h3>Credentials GPG ({n_gpg})</h3>
  <p class="path" style="margin-bottom:8px">~/.claude/secrets/web-credentials.gpg</p>
  <table>
    <thead><tr><th>Service</th></tr></thead>
    <tbody>{gpg_rows}</tbody>
  </table>
</div>'''

    # Memory
    mem_rows = ""
    for m in memories:
        badge = f'<span class="badge bg-blue">{m["type"]}</span>' if m["type"] else ""
        mem_rows += f'<tr><td class="mono">{m["name"]}</td><td>{badge}</td><td>{m["desc"][:60] if m["desc"] else "—"}</td></tr>'

    memory_html = f'''
<div class="card" id="memory">
  <h3>Memoire ({n_memories} fichiers)</h3>
  <p class="path" style="margin-bottom:8px">~/.claude/projects/-home-egx/memory/</p>
  <table>
    <thead><tr><th>Fichier</th><th>Type</th><th>Description</th></tr></thead>
    <tbody>{mem_rows}</tbody>
  </table>
</div>'''

    # Rules
    rules_html_rows = ""
    current_section = ""
    for r in rules:
        if r["section"] != current_section:
            current_section = r["section"]
            rules_html_rows += f'<tr><td colspan="2" style="color:#58a6ff;font-weight:600;padding-top:12px">{current_section}</td></tr>'
        rules_html_rows += f'<tr><td class="rule">{r["rule"]}</td></tr>'

    rules_html = f'''
<div class="card" id="rules">
  <h3>Regles OBLIGATOIRE ({n_rules})</h3>
  <p class="path" style="margin-bottom:8px">~/.claude/CLAUDE.md — Cle GPG: emmanuel.genesteix@agilevizion.com</p>
  <table><tbody>{rules_html_rows}</tbody></table>
</div>'''

    # Permissions
    allow_list = ", ".join(f'<code>{a}</code>' for a in allow[:15])
    deny_list = ", ".join(f'<code style="color:#f85149">{d}</code>' for d in deny)

    perms_html = f'''
<div class="card" id="tools">
  <h3>Tools (Permissions Bash)</h3>
  <p class="path" style="margin-bottom:8px">Commandes autorisees/interdites dans le terminal Claude Code</p>
  <p style="margin-bottom:6px"><strong style="color:#3fb950">Allow ({len(allow)}):</strong> {allow_list}{" ..." if len(allow) > 15 else ""}</p>
  <p><strong style="color:#f85149">Deny ({len(deny)}):</strong> {deny_list}</p>
</div>'''

    # Key files
    file_rows = ""
    for kf in key_files:
        status = '<span class="badge bg-green">OK</span>' if kf["exists"] else '<span class="badge bg-red">ABSENT</span>'
        link = f'<a href="file://{kf["full_path"]}" class="dir-link" style="font-size:0.78rem">{kf["path"]}</a>'
        file_rows += f'<tr><td><strong>{kf["label"]}</strong></td><td>{link}</td><td style="color:#8b949e;font-size:0.78rem">{kf["desc"]}</td><td class="col-center">{status}</td></tr>'

    files_html = f'''
<div class="card" id="files">
  <h3>Fichiers cles</h3>
  <table>
    <thead><tr><th>Element</th><th>Chemin</th><th>Description</th><th>Statut</th></tr></thead>
    <tbody>{file_rows}</tbody>
  </table>
</div>'''

    return f'''{guide_html}
{stats}
<div class="grid-2">
  <div>{skills_html}{plugins_html}</div>
  <div>{mcp_html}{gpg_html}</div>
</div>
{memory_html}
{perms_html}
{rules_html}
{files_html}'''


def build_apps_html(msg_html=""):
    cards = ""
    for app in APPS_CONFIG:
        status = get_app_status(app)
        is_running = status == "running"
        is_self = app["type"] == "self"

        # Status badge
        if is_running:
            badge = '<span class="badge bg-green">EN COURS</span>'
        else:
            badge = '<span class="badge bg-gray">ARRETE</span>'

        # Action buttons
        if is_self:
            actions = '<span style="color:#484f58;font-size:0.78rem">Ce dashboard</span>'
        elif is_running:
            actions = f'''<form method="POST" action="/apps" style="display:inline">
                <input type="hidden" name="app_id" value="{app['id']}">
                <input type="hidden" name="action" value="stop">
                <button type="submit" class="toggle-btn btn-off">Arreter</button>
            </form>'''
        else:
            actions = f'''<form method="POST" action="/apps" style="display:inline">
                <input type="hidden" name="app_id" value="{app['id']}">
                <input type="hidden" name="action" value="start">
                <button type="submit" class="toggle-btn btn-on">Demarrer</button>
            </form>'''

        # Open buttons
        open_btns = ""
        url = app.get("url")
        if url and is_running:
            open_btns += f'<a href="{url}" target="_blank" class="toggle-btn btn-on" style="text-decoration:none;margin-left:6px;display:inline-block">Ouvrir</a>'

        open_btns += f'''<a href="/open?path={app['path']}" class="toggle-btn" style="background:#1a2a3c;color:#58a6ff;text-decoration:none;margin-left:6px;display:inline-block">Dossier</a>'''
        open_btns += f'''<a href="javascript:void(0)" onclick="fetch('/cursor?path={app['path']}')" class="toggle-btn" style="background:#21262d;color:#c9d1d9;text-decoration:none;margin-left:6px;display:inline-block">Cursor</a>'''

        cards += f'''
        <div class="card" style="display:flex;align-items:center;gap:20px;padding:20px">
            <div style="font-size:2rem;width:48px;text-align:center">{app['icon']}</div>
            <div style="flex:1">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px">
                    <strong style="color:#e6edf3;font-size:1rem">{app['name']}</strong>
                    {badge}
                </div>
                <div style="color:#8b949e;font-size:0.82rem;margin-bottom:2px">{app['desc']}</div>
                <div class="path">{app['path']}</div>
            </div>
            <div style="display:flex;align-items:center;flex-wrap:wrap;gap:4px">
                {actions}
                {open_btns}
            </div>
        </div>'''

    return f'''{msg_html}{cards}'''


def build_page(body, active_tab="agents"):
    header = build_header(active_tab)
    return f'''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
{"<meta http-equiv='refresh' content='30'>" if active_tab == "agents" else ""}
<title>Dashboard — AgileVizion</title>
<style>{CSS}</style>
</head>
<body>
{header}
{body}
<p class="footer">Config: registry.json &middot; Serveur: localhost:{PORT}</p>
</body>
</html>'''


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path == "/open":
            # Ouvrir un repertoire dans le file manager
            target = params.get("path", [""])[0]
            if target and os.path.exists(target):
                subprocess.Popen(["xdg-open", target])
                self.send_response(302)
                self.send_header("Location", "/")
                self.end_headers()
                return
            self.send_response(404)
            self.end_headers()
            return

        if path == "/cursor":
            target = params.get("path", [""])[0]
            if target and os.path.exists(target):
                subprocess.Popen(["cursor", target])
            self.send_response(204)
            self.end_headers()
            return

        if path == "/config":
            body = build_config_html()
            html = build_page(body, "config")
        elif path == "/apps":
            body = build_apps_html()
            html = build_page(body, "apps")
        else:
            body = build_agents_html()
            html = build_page(body, "agents")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode()
        params = parse_qs(body)
        parsed = urlparse(self.path)
        post_path = parsed.path

        # Apps actions
        if post_path == "/apps":
            app_id = params.get("app_id", [""])[0]
            action = params.get("action", [""])[0]
            msg_html = ""
            if app_id and action:
                if action == "start":
                    result = start_app(app_id)
                elif action == "stop":
                    result = stop_app(app_id)
                else:
                    result = f"Action inconnue: {action}"
                msg_html = f'<div class="msg">{result}</div>'
            body_html = build_apps_html(msg_html)
            html = build_page(body_html, "apps")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode())
            return

        # Agents actions (default)
        agent_id = params.get("id", [""])[0]
        action = params.get("action", [""])[0]

        msg_html = ""
        if agent_id and action:
            result = toggle_agent(agent_id, action)
            msg_html = f'<div class="msg">{result}</div>'

        body_html = build_agents_html(msg_html)
        html = build_page(body_html, "agents")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())


if __name__ == "__main__":
    print(f"Dashboard sur http://localhost:{PORT}")
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
