// Web 模組基本 JavaScript

// 工具函數
function showAlert(message, type = 'info') {
    // 創建警告元素
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    
    // 添加到頁面頂部
    const container = document.querySelector('.container') || document.body;
    container.insertBefore(alertDiv, container.firstChild);
    
    // 3秒後自動移除
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 3000);
}

function showSuccess(message) {
    showAlert(message, 'success');
}

function showError(message) {
    showAlert(message, 'danger');
}

function showInfo(message) {
    showAlert(message, 'info');
}

// 表單驗證
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function validatePhone(phone) {
    const phoneRegex = /^[\d\s\-\(\)]+$/;
    return phoneRegex.test(phone.replace(/\s/g, ''));
}

// AJAX 請求封裝
async function makeRequest(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
        ...options
    };

    try {
        const response = await fetch(url, defaultOptions);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Request failed:', error);
        throw error;
    }
}

// DOM 載入完成
document.addEventListener('DOMContentLoaded', function() {
    console.log('Web modules loaded successfully');
    
    // 初始化所有表單
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', handleFormSubmit);
    });
    
    // 初始化所有按鈕
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', handleButtonClick);
    });
});

// 表單提交處理
function handleFormSubmit(event) {
    const form = event.target;
    const submitBtn = form.querySelector('[type="submit"]');
    
    if (submitBtn) {
        // 顯示載入狀態
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = '載入中...';
        
        // 恢復按鈕狀態（如果請求失敗）
        setTimeout(() => {
            if (submitBtn.disabled) {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        }, 5000);
    }
}

// 按鈕點擊處理
function handleButtonClick(event) {
    const button = event.target;
    
    // 添加點擊效果
    button.style.transform = 'scale(0.95)';
    
    setTimeout(() => {
        button.style.transform = 'scale(1)';
    }, 100);
}

// 密碼顯示/隱藏切換
function togglePassword(inputId, button) {
    const input = document.getElementById(inputId);
    const icon = button.querySelector('i');
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.className = 'fas fa-eye-slash';
    } else {
        input.type = 'password';
        icon.className = 'fas fa-eye';
    }
}

// 複製到剪貼板
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showSuccess('已複製到剪貼板');
        }).catch(err => {
            showError('複製失敗');
        });
    } else {
        // 後備方案
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        
        try {
            document.execCommand('copy');
            showSuccess('已複製到剪貼板');
        } catch (err) {
            showError('複製失敗');
        }
        
        document.body.removeChild(textArea);
    }
}

// 格式化日期時間
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('zh-TW', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// 防止重複提交
let isSubmitting = false;
function preventDuplicateSubmit(form) {
    if (isSubmitting) {
        return false;
    }
    
    isSubmitting = true;
    setTimeout(() => {
        isSubmitting = false;
    }, 3000);
    
    return true;
}

// 頁面滾動到頂部
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// 檢查表單欄位
function validateFormField(field, rules = {}) {
    const value = field.value.trim();
    const errors = [];
    
    // 必填檢查
    if (rules.required && !value) {
        errors.push('此欄位為必填');
    }
    
    // 最小長度檢查
    if (rules.minLength && value.length < rules.minLength) {
        errors.push(`最少需要 ${rules.minLength} 個字符`);
    }
    
    // 最大長度檢查
    if (rules.maxLength && value.length > rules.maxLength) {
        errors.push(`最多允許 ${rules.maxLength} 個字符`);
    }
    
    // 類型檢查
    if (rules.type === 'email' && value && !validateEmail(value)) {
        errors.push('請輸入有效的電子郵件');
    }
    
    if (rules.type === 'phone' && value && !validatePhone(value)) {
        errors.push('請輸入有效的電話號碼');
    }
    
    return {
        isValid: errors.length === 0,
        errors: errors
    };
}
