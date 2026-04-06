# 🚀 GitHub 設置與協作指南

## 📋 第一步：創建 GitHub 倉庫

### 1.1 在 GitHub 創建新倉庫
1. 登入 [GitHub](https://github.com)
2. 點擊右上角的 "+" → "New repository"
3. 倉庫名稱：`line-ai-appointment-system`
4. 描述：`LINE AI 智能預約系統`
5. 設置為 **Private** (私有倉庫)
6. **不要** 勾選 "Add a README file"
7. 點擊 "Create repository"

### 1.2 連接本地倉庫
```bash
# 設置遠端倉庫 (替換為你的用戶名)
git remote add origin https://github.com/你的用戶名/line-ai-appointment-system.git

# 推送到遠端
git push -u origin ai-assist/服務管理系統
```

## 👥 第二步：邀請協作者

### 2.1 添加協作者
1. 進入你的 GitHub 倉庫
2. 點擊 "Settings" 標籤
3. 左側選單點擊 "Collaborators"
4. 點擊 "Add people"
5. 輸入協作者的 GitHub 用戶名或郵箱
6. 設置權限為 "Write"
7. 點擊 "Add collaborator"

### 2.2 協作者接受邀請
1. 協作者檢查郵箱
2. 點擊邀請連結
3. 點擊 "Accept invitation"

## 🛡️ 第三步：設置分支保護

### 3.1 保護 main 分支
1. 進入倉庫 → Settings → Branches
2. 點擊 "Add rule"
3. Branch name: `main`
4. 勾選：
   - ✅ Require pull request reviews before merging
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
5. 點擊 "Create"

### 3.2 保護 develop 分支
1. 重複上述步驟
2. Branch name: `develop`
3. 設置相同的保護規則

## 🔄 第四步：設置自動化

### 4.1 GitHub Actions (可選)
```yaml
# .github/workflows/collaboration.yml
name: 協作檢查
on: [push, pull_request]

jobs:
  check-collaboration:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: 檢查協作狀態
      run: |
        if [ -f collaboration_status.txt ]; then
          echo "📋 協作狀態:"
          cat collaboration_status.txt
        fi
```

### 4.2 設置 Issues 模板
```markdown
<!-- .github/ISSUE_TEMPLATE/bug_report.md -->
---
name: Bug Report
about: 報告問題
title: "[BUG] "
labels: bug
assignees: ''
---

**描述問題**
清楚描述遇到的問題

**重現步驟**
1. 進入 '...'
2. 點擊 '....'
3. 滾動到 '....'
4. 看到錯錯誤

**預期行為**
描述你期望發生的情況

**實際行為**
描述實際發生的情況

**截圖**
如果適用，添加截圖

**環境**
- OS: [Windows/Mac/Linux]
- 瀏覽器: [Chrome/Firefox/Safari]
- 版本: [版本號]
```

## 🎯 第五步：協作工作流程

### 5.1 日常協作流程
```bash
# 1. 克隆倉庫 (協作者)
git clone https://github.com/你的用戶名/line-ai-appointment-system.git
cd line-ai-appointment-system

# 2. 設置協作環境
./setup_collaboration.sh

# 3. 開始工作
./start_collaboration.sh
```

### 5.2 AI 協作流程
```bash
# 1. 啟動 AI 安全協作
./ai_assist.sh "服務管理系統優化"

# 2. AI 完成工作後
git add .
git commit -m "feat: AI 協助完成服務管理優化"
git push origin ai-assist/20260406_服務管理系統優化

# 3. 創建 Pull Request
# 在 GitHub 上創建 PR 到 develop 分支
```

### 5.3 代碼審查流程
1. **創建 Pull Request**
   - 標題：`[AI Assist] 服務管理系統重寫`
   - 描述：詳細說明修改內容
   - 標籤：`ai-assist`, `enhancement`

2. **Code Review**
   - 協作者檢查代碼
   - 測試所有功能
   - 提出建議或問題

3. **合併**
   - 所有審查通過後合併
   - 刪除功能分支
   - 更新文檔

## 🚨 第六步：緊急應對

### 6.1 AI 修改造成問題
```bash
# 1. 立即停止
# 2. 回滾到安全版本
./emergency_rollback.sh

# 3. 創建修復分支
git checkout develop
git checkout -b hotfix/修復AI問題

# 4. 修復並推送
git add .
git commit -m "hotfix: 修復 AI 修改問題"
git push origin hotfix/修復AI問題
```

### 6.2 團隊溝通
1. **GitHub Issues** - 報告問題
2. **Discord/Slack** - 實時溝通
3. **Email** - 緊急聯繫
4. **Phone** - 緊急情況

## 📊 第七步：監控與維護

### 7.1 定期檢查
```bash
# 每日檢查
./monitor.sh

# 每週清理
git branch -d $(git branch --merged)
git remote prune origin
```

### 7.2 性能監控
- GitHub Insights 查看活動
- 維護分支清潔
- 定期備份重要版本

## 🎉 第八步：最佳實踐

### ✅ 推薦做法
1. **小步驟提交** - 每個功能分開提交
2. **清晰的提交訊息** - 說明修改目的
3. **定期同步** - 每天同步最新代碼
4. **Code Review** - 所有修改都經過審查
5. **文檔更新** - 及時更新文檔

### ❌ 避免做法
1. **直接修改 main** - 永遠不要直接修改主分支
2. **大量一次性修改** - 避免一次修改太多
3. **無測試推送** - 推送前必須測試
4. **不溝通修改** - 重大修改前通知團隊

## 🔧 快速命令參考

```bash
# 設置環境
./setup_collaboration.sh

# 開始工作
./start_collaboration.sh

# 同步代碼
./sync.sh

# 監控狀態
./monitor.sh

# AI 協作
./ai_assist.sh "任務描述"

# 緊急回滾
./emergency_rollback.sh

# 查看分支
git branch -a

# 查看狀態
git status

# 查看日誌
git log --oneline -10
```

## 📞 支援與聯繫

### 獲取幫助
- 📖 文檔：`LIVE_COLLABORATION.md`
- 🚀 快速指南：`COLLABORATION_GUIDE.md`
- 🛠️ 腳本：`./setup_collaboration.sh`
- 🐛 問題報告：GitHub Issues

### 聯繫方式
- 📧 Email: your.email@example.com
- 💬 Discord: 你的 Discord
- 📱 Phone: 你的電話
- 🐛 GitHub: @你的用戶名

## 🎯 總結

這個 GitHub 設置確保：
- ✅ **安全的協作環境** - 分支保護和權限控制
- ✅ **清晰的流程** - 標準化的工作流程
- ✅ **AI 安全協作** - 隔離的 AI 工作環境
- ✅ **緊急應對** - 快速問題解決機制
- ✅ **團隊協作** - 完整的協作工具

現在你可以安全地與朋友進行 Live 協作，AI 修改不會造成混亂！🎉
