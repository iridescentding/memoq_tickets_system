#!/bin/bash

# 定义源目录和目标目录
SOURCE_DIR="$(pwd)"
TARGET_DIR="/Users/jayding/Desktop/github"

# 创建目标目录（如果不存在）
mkdir -p "$TARGET_DIR"

echo "开始复制项目文件从 $SOURCE_DIR 到 $TARGET_DIR..."

# 使用rsync进行复制，排除不需要的文件
rsync -av --progress "$SOURCE_DIR/" "$TARGET_DIR/" \
  --exclude="*/__pycache__/*" \
  --exclude="*.pyc" \
  --exclude="*.pyo" \
  --exclude="*.pyd" \
  --exclude="*.so" \
  --exclude="*.dll" \
  --exclude="venv" \
  --exclude="env" \
  --exclude=".venv" \
  --exclude="node_modules" \
  --exclude=".cache" \
  --exclude=".pytest_cache" \
  --exclude=".coverage" \
  --exclude=".DS_Store" \
  --exclude="db.sqlite3" \
  --exclude="*.log" \
  --exclude="media/" \
  --exclude="static/collected/" \
  --exclude="*.tmp" \
  --exclude="*.bak" \
  --exclude="*.swp" \
  --exclude="*~" \
  --exclude="dist/" \
  --exclude="build/" \
  --exclude=".env" \
  --exclude=".env.*" \
  --include=".env.example" \
  --include=".env.*.example" \
  --exclude=".memoq-cache/"

# 创建.gitignore文件
cat > "$TARGET_DIR/.gitignore" << 'EOL'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Django
*.log
*.pot
*.pyc
db.sqlite3
media/
static/collected/

# Vue/Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.DS_Store
dist/
.cache/
.env.local
.env.*.local

# Editor directories and files
.idea/
.vscode/
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?

# Testing
.coverage
htmlcov/
.pytest_cache/

# Environment variables
.env
.env.production
.env.development

# Keep example files
!.env.example
!.env.*.example

# MemoQ specific
.memoq-cache/
EOL

echo "已创建 .gitignore 文件"

# 初始化Git仓库
cd "$TARGET_DIR"
git init
git add .
git commit -m "Initial commit"
git branch -M main

echo "项目已成功复制到 $TARGET_DIR 并初始化为Git仓库"
echo "您现在可以添加GitHub远程仓库并推送代码:"
echo "cd $TARGET_DIR"
echo "git remote add origin <您的GitHub仓库URL>"
echo "git push -u origin main"

exit 0