# Phase 1 ? VM Setup and Toolchain

**What was done:**
- Checked installed versions of Python, git, curl, tmux, and screen.
- Updated apt and installed dependencies: python3-pip, python3-venv, git, uild-essential, jq, curl, and 	mux.
- Scaffolding created in ~/codesentinel-ai.
- Git initialized with .gitignore and pyproject.toml.
- Python virtual environment created and activated at .venv.

**Exact commands run:**
\\\ash
python3 --version
git --version
docker --version || echo "Docker not installed"
curl --version | head -n 1
tmux -V || echo "tmux not installed"
screen -v || echo "screen not installed"
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv git build-essential jq curl tmux
mkdir -p ~/codesentinel-ai/PHASE_REPORTS
cd ~/codesentinel-ai
git config --global user.email "student@example.com"
git config --global user.name "Student"
git init -b main
python3 -m venv .venv
source .venv/bin/activate
cat << 'EOF2' > .gitignore
.venv/
venv/
__pycache__/
.env
*.pyc
dist/
build/
EOF2
cat << 'EOF2' > pyproject.toml
[project]
name = "codesentinel-ai"
requires-python = ">=3.12"
version = "0.1.0"
EOF2
git add .
git commit -m "chore: scaffold project"
\\\

**Proof of completion:**
- Python 3.14.4
- git version 2.53.0
- Docker not installed
- curl 8.18.0
- tmux 3.6
- Screen version 4.09.01
- Project structure: ~/codesentinel-ai
- Virtual env: /home/student/codesentinel-ai/.venv/bin/python

**What changed in the dashboard:**
N/A (Dashboard is introduced in Phase 2).

**What's left for the next phase:**
Phase 2: Minimal Action skeleton AND a working dashboard skeleton.
