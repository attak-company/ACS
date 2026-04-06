#!/bin/bash

echo "🚀 設置 Live 協作環境"
echo "=========================="

# 檢查是否在 Git 倉庫中
if [ ! -d ".git" ]; then
    echo "❌ 錯誤：當前目錄不是 Git 倉庫"
    echo "請先運行：git init"
    exit 1
fi

# 設置 Git 配置
echo "📝 設置 Git 配置..."
read -p "請輸入你的名字: " name
read -p "請輸入你的郵箱: " email

git config user.name "$name"
git config user.email "$email"

echo "✅ Git 配置完成"

# 創建分支結構
echo "🌳 創建分支結構..."

# 創建 develop 分支
git checkout -b develop 2>/dev/null || git checkout develop
git push -u origin develop 2>/dev/null || echo "develop 分支已存在"

echo "✅ develop 分支創建完成"

# 創建協作者分支
read -p "請輸入你的用戶名 (用於分支命名): " username

git checkout -b "$username/工作區域" 2>/dev/null || echo "工作分支已存在"

echo "✅ 你的工作分支創建完成：$username/工作區域"

# 創建 AI 協作分支
git checkout -b "ai-assist/$(date +%Y%m%d)_待命" 2>/dev/null || echo "AI 分支已存在"

echo "✅ AI 協作分支創建完成"

# 創建協作狀態文件
echo "📋 創建協作狀態文件..."
cat > collaboration_status.txt << EOF
協作狀態 - $(date)
==================
用戶 $username: 活躍
其他用戶: 待更新
AI 狀態: 待命中

當前任務:
- 服務管理系統: 完成
- UI 設計: 進行中
- 錯誤修復: 完成

注意事項:
- AI 修改使用 ai-assist/* 分支
- 每次修改前先同步 develop
- 重大修改前通知團隊
EOF

echo "✅ 協作狀態文件創建完成"

# 創建同步腳本
echo "🔄 創建同步腳本..."
cat > sync.sh << 'EOF'
#!/bin/bash
echo "🔄 開始同步協作環境..."
echo "========================"

# 保存當前工作
git add .
if [ -n "$(git status --porcelain)" ]; then
    git commit -m "save: 自動保存工作進度 - $(date)"
    echo "✅ 當前工作已保存"
fi

# 同步最新代碼
git fetch origin
git checkout develop
git pull origin develop

echo "✅ develop 分支已同步到最新版本"

# 返回原分支
current_branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$current_branch" != "develop" ]; then
    git checkout -
    git rebase develop
    echo "✅ 當前分支已 rebase 到最新 develop"
fi

echo "🎉 同步完成！"
EOF

chmod +x sync.sh

echo "✅ 同步腳本創建完成"

# 創建監控腳本
echo "📊 創建監控腳本..."
cat > monitor.sh << 'EOF'
#!/bin/bash
echo "📊 協作狀態監控"
echo "=================="
echo "時間: $(date)"
echo ""

echo "🌳 分支狀態:"
git branch -a
echo ""

echo "📝 最近提交:"
git log --oneline -5
echo ""

echo "📋 協作狀態:"
if [ -f collaboration_status.txt ]; then
    cat collaboration_status.txt
else
    echo "❌ 協作狀態文件不存在"
fi

echo ""
echo "🔄 遠端狀態:"
git remote -v
echo ""

echo "⚠️  注意事項:"
echo "- 定期運行 ./sync.sh 同步代碼"
echo "- AI 修改使用 ai-assist/* 分支"
echo "- 重大修改前通知團隊成員"
echo "- 每天更新 collaboration_status.txt"
EOF

chmod +x monitor.sh

echo "✅ 監控腳本創建完成"

# 創建 AI 安全協作腳本
echo "🤖 創建 AI 安全協作腳本..."
cat > ai_assist.sh << 'EOF'
#!/bin/bash
echo "🤖 AI 安全協作模式"
echo "==================="

# 檢查當前分支
current_branch=$(git rev-parse --abbrev-ref HEAD)
echo "當前分支: $current_branch"

# 創建 AI 專用分支
ai_branch="ai-assist/$(date +%Y%m%d)_$(date +%H%M%S)_${1:-具體任務}"
echo "創建 AI 分支: $ai_branch"

# 備份當前狀態
backup_branch="backup/$(date +%Y%m%d_%H%M%S)_AI前備份"
git checkout -b $backup_branch
git add .
git commit -m "backup: AI 修改前備份 - $(date)"
echo "✅ 備份分支創建完成: $backup_branch"

# 創建 AI 工作分支
git checkout develop
git pull origin develop
git checkout -b $ai_branch

# 更新協作狀態
echo "更新協作狀態..."
cat > collaboration_status.txt << EOF
協作狀態 - $(date)
==================
AI 狀態: 工作中
AI 分支: $ai_branch
AI 任務: ${1:-具體任務}
開始時間: $(date)

注意事項:
- AI 正在 $ai_branch 分支工作
- 請勿同時修改相同文件
- 完成後創建 Pull Request
EOF

echo "✅ AI 協作環境設置完成"
echo "🎯 現在可以安全地與 AI 協作"
echo "📝 請明確指定 AI 任務範圍"
echo "🔄 完成後運行 ./sync.sh 同步"
EOF

chmod +x ai_assist.sh

echo "✅ AI 協作腳本創建完成"

# 創建緊急回滾腳本
echo "🚨 創建緊急回滾腳本..."
cat > emergency_rollback.sh << 'EOF'
#!/bin/bash
echo "🚨 緊急回滾模式"
echo "================="

# 檢查是否有未提交的更改
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  檢測到未提交的更改"
    echo "選擇操作:"
    echo "1. 保存更改並回滾"
    echo "2. 丟棄更改並回滾"
    read -p "請選擇 (1/2): " choice
    
    case $choice in
        1)
            git add .
            git commit -m "emergency: 緊急保存 - $(date)"
            ;;
        2)
            git reset --hard HEAD
            git clean -fd
            ;;
    esac
fi

# 顯示最近的提交
echo "📝 最近的提交:"
git log --oneline -10

# 選擇回滾點
echo ""
echo "選擇回滾方式:"
echo "1. 回滾到特定提交"
echo "2. 回滾到昨天"
echo "3. 回滾到標籤"
read -p "請選擇 (1/2/3): " rollback_choice

case $rollback_choice in
    1)
        read -p "請輸入要回滾到的提交 ID: " commit_id
        git reset --hard $commit_id
        ;;
    2)
        git reset --hard "$(git rev-list -1 --before=yesterday HEAD)"
        ;;
    3)
        git tag -l
        read -p "請輸入標籤名稱: " tag_name
        git reset --hard $tag_name
        ;;
esac

echo "✅ 回滾完成"
echo "🔄 如果需要推送到遠端，請使用:"
echo "git push --force-with-lease origin $(git rev-parse --abbrev-ref HEAD)"
EOF

chmod +x emergency_rollback.sh

echo "✅ 緊急回滾腳本創建完成"

# 設置 Git Hooks
echo "🔧 設置 Git Hooks..."
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/sh
echo "🔄 預提交檢查..."
echo "=================="

# 檢查協作狀態
if [ -f collaboration_status.txt ]; then
    echo "📋 當前協作狀態:"
    grep -A 5 "AI 狀態" collaboration_status.txt || echo "AI 狀態: 未知"
fi

# 檢查是否在 AI 分支
current_branch=$(git rev-parse --abbrev-ref HEAD)
if [[ $current_branch == ai-assist/* ]]; then
    echo "⚠️  檢測到 AI 分支提交"
    echo "請確認:"
    echo "- 所有功能都已測試"
    echo "- 沒有破壞性修改"
    echo "- 代碼質量良好"
    
    read -p "確認提交? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "❌ 提交已取消"
        exit 1
    fi
fi

echo "✅ 預提交檢查通過"
EOF

chmod +x .git/hooks/pre-commit

echo "✅ Git Hooks 設置完成"

# 創建快速啟動腳本
echo "🚀 創建快速啟動腳本..."
cat > start_collaboration.sh << 'EOF'
#!/bin/bash
echo "🚀 啟動 Live 協作環境"
echo "======================"

# 檢查環境
echo "📊 檢查協作環境..."
./monitor.sh

echo ""
echo "🔄 同步最新代碼..."
./sync.sh

echo ""
echo "📋 可用命令:"
echo "./sync.sh        - 同步代碼"
echo "./monitor.sh     - 監控狀態"
echo "./ai_assist.sh   - 啟動 AI 協作"
echo "./emergency_rollback.sh - 緊急回滾"
echo ""

echo "🎯 協作環境已就緒！"
EOF

chmod +x start_collaboration.sh

echo "✅ 快速啟動腳本創建完成"

# 創建文檔
echo "📚 創建協作文檔..."
cat > COLLABORATION_GUIDE.md << 'EOF'
# 🚀 Live 協作快速指南

## 🎯 日常使用

### 開始工作
```bash
./start_collaboration.sh
```

### 同步代碼
```bash
./sync.sh
```

### 監控狀態
```bash
./monitor.sh
```

### AI 協作
```bash
./ai_assist.sh "具體任務描述"
```

### 緊急回滾
```bash
./emergency_rollback.sh
```

## 📋 分支策略

- `develop` - 開發主分支
- `用戶名/工作區域` - 個人工作分支
- `ai-assist/日期_任務` - AI 協作分支
- `backup/時間戳` - 備份分支

## ⚠️  注意事項

1. **永遠不要直接修改 main 分支**
2. **AI 修改必須使用 ai-assist/* 分支**
3. **每次工作前先運行 ./sync.sh**
4. **重大修改前通知團隊成員**
5. **定期更新 collaboration_status.txt**

## 🚨 緊急情況

如果 AI 修改造成問題：
1. 立即停止 AI 協作
2. 運行 ./emergency_rollback.sh
3. 通知所有協作者
4. 分析問題並制定修復方案

## 📞 聯繫方式

- GitHub Issues: 報告問題
- Email: 緊急聯繫
- Discord: 實時溝通
EOF

echo "✅ 協作文檔創建完成"

echo ""
echo "🎉 Live 協作環境設置完成！"
echo "=============================="
echo ""
echo "📋 下一步操作:"
echo "1. 運行 ./start_collaboration.sh 開始協作"
echo "2. 閱讀 COLLABORATION_GUIDE.md 了解使用方法"
echo "3. 邀請團隊成員克隆倉庫"
echo "4. 設定 GitHub 保護規則"
echo ""
echo "🔗 重要文件:"
echo "- LIVE_COLLABORATION.md - 詳細協作指南"
echo "- COLLABORATION_GUIDE.md - 快速使用指南"
echo "- collaboration_status.txt - 實時協作狀態"
echo ""
echo "🚀 現在可以安全地進行 Live 協作了！"
