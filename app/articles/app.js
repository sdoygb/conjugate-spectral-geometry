// 文档库前端应用
var articleTree = [];
var currentArticle = null;

// ========== 安全触发 MathJax 渲染 ==========
function renderMath(element) {
    if (!element) return;
    function doTypeset() {
        if (window.MathJax && MathJax.typesetPromise) {
            MathJax.typesetPromise([element]).catch(function(){});
        }
    }
    // MathJax 已加载完成
    if (window.MathJax && MathJax.startup && MathJax.startup.promise) {
        MathJax.startup.promise.then(doTypeset);
    } else if (window.MathJax && MathJax.typesetPromise) {
        doTypeset();
    } else {
        // MathJax 还在加载，轮询等待（最多等 10 秒）
        var attempts = 0;
        var timer = setInterval(function() {
            if (window.MathJax && MathJax.typesetPromise) {
                clearInterval(timer);
                MathJax.typesetPromise([element]).catch(function(){});
            }
            if (++attempts > 100) clearInterval(timer);
        }, 100);
    }
}

// ========== 清理文件名为标题 ==========
function cleanTitle(filename) {
    var name = filename.replace(/\.md$/, '');
    name = name.replace(/_CN_\d+\.?\d*$/, '');
    name = name.replace(/_HW_\d+\.?\d*$/, '');
    name = name.replace(/_\d{6}\.\d+$/, '');
    return name;
}

// ========== 统计目录下文件数 ==========
function countFiles(items) {
    var count = 0;
    for (var i = 0; i < items.length; i++) {
        if (items[i].type === 'file') count++;
        else count += countFiles(items[i].children);
    }
    return count;
}

// ========== 递归构建目录树 HTML ==========
function buildTreeHTML(items, depth) {
    var html = '';
    for (var i = 0; i < items.length; i++) {
        var item = items[i];
        if (item.type === 'dir') {
            var childFiles = countFiles(item.children);
            if (childFiles === 0) continue;
            html += '<div class="nav-dir">';
            html += '<div class="nav-dir-title" style="padding-left:' + (0.5 + depth) + 'rem">';
            html += '<span class="arrow">&#9660;</span> ' + item.name + ' <span style="opacity:0.5;font-size:0.75rem">(' + childFiles + ')</span>';
            html += '</div>';
            html += '<div class="nav-dir-children">';
            html += buildTreeHTML(item.children, depth + 1);
            html += '</div></div>';
        } else {
            var title = cleanTitle(item.name);
            var cls = depth === 0 ? 'nav-root-file' : 'nav-file';
            html += '<a class="' + cls + '" style="padding-left:' + (1 + depth) + 'rem" data-path="' + item.path + '">' + title + '</a>';
        }
    }
    return html;
}

// ========== 构建侧边栏 ==========
function buildSidebar(tree) {
    var sidebar = document.getElementById('sidebar');
    sidebar.innerHTML = buildTreeHTML(tree, 0);

    sidebar.addEventListener('click', function(e) {
        var titleEl = e.target.closest('.nav-dir-title');
        if (titleEl) {
            titleEl.classList.toggle('collapsed');
            return;
        }
        var fileEl = e.target.closest('.nav-file, .nav-root-file');
        if (fileEl && fileEl.dataset.path) {
            e.preventDefault();
            loadArticle(fileEl.dataset.path, fileEl);
        }
    });
}

// ========== 预处理Markdown: 保护LaTeX公式，防止marked破坏 ==========
function protectMath(md) {
    // 1. 先保护代码块
    var codeBlocks = [];
    md = md.replace(/```[\s\S]*?```/g, function(m) {
        codeBlocks.push(m);
        return '\x00CODE' + (codeBlocks.length - 1) + '\x00';
    });
    md = md.replace(/`[^`]+`/g, function(m) {
        codeBlocks.push(m);
        return '\x00CODE' + (codeBlocks.length - 1) + '\x00';
    });

    // 2. 把 $$...$$ 转为 <div class="math-display">$$...$$</div>
    md = md.replace(/\$\$([\s\S]*?)\$\$/g, function(match, formula) {
        return '\n\n<div class="math-display">$$' + formula + '$$</div>\n\n';
    });

    // 3. 把 $...$ 转为 <span class="math-inline">$...$</span>
    md = md.replace(/\$([^\$\n]+?)\$/g, function(match, formula) {
        return '<span class="math-inline">$' + formula + '$</span>';
    });

    // 4. 恢复代码块
    md = md.replace(/\x00CODE(\d+)\x00/g, function(m, idx) {
        return codeBlocks[parseInt(idx)];
    });

    return md;
}

// ========== 加载文章 ==========
function loadArticle(path, linkElement) {
    // 清除之前的激活状态
    var actives = document.querySelectorAll('.nav-file.active, .nav-root-file.active');
    for (var i = 0; i < actives.length; i++) {
        actives[i].classList.remove('active');
    }
    if (linkElement) linkElement.classList.add('active');

    var container = document.getElementById('article-content');
    container.innerHTML = '<div class="empty-state"><p>加载中...</p></div>';

    // 更新面包屑
    var breadcrumbPath = document.getElementById('breadcrumb-path');
    if (breadcrumbPath) {
        breadcrumbPath.textContent = ' / 文档库 / ' + cleanTitle(path.split('/').pop());
    }

    fetch(path)
        .then(function(response) {
            if (!response.ok) throw new Error('文件未找到 (404)');
            return response.text();
        })
        .then(function(content) {
            // 保护 LaTeX → marked 解析 → 插入 DOM
            var protectedMd = protectMath(content);
            var html = marked.parse(protectedMd);
            container.innerHTML = '<div class="article-container">' + html + '</div>';
            currentArticle = { path: path, content: content };

            // 触发 MathJax 渲染
            renderMath(container);

            // 滚动到顶部
            document.querySelector('.content').scrollTop = 0;
        })
        .catch(function(err) {
            container.innerHTML = '<div class="empty-state"><p style="color:#e74c3c;">加载失败: ' + err.message + '</p></div>';
        });
}

// ========== 初始化 ==========
function init() {
    if (typeof articleTreeData !== 'undefined' && articleTreeData.length > 0) {
        articleTree = articleTreeData;
        buildSidebar(articleTree);
    } else {
        document.getElementById('sidebar').innerHTML =
            '<div style="padding:12px;color:#f38ba8;font-size:12px;">文章数据未加载，请检查 articles_data.js</div>';
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', init);

// 键盘快捷键
document.addEventListener('keydown', function(e) {
    // Escape 清除选中
    if (e.key === 'Escape') {
        var actives = document.querySelectorAll('.nav-file.active, .nav-root-file.active');
        for (var i = 0; i < actives.length; i++) {
            actives[i].classList.remove('active');
        }
        var container = document.getElementById('article-content');
        container.innerHTML = '<div class="empty-state"><div class="icon">📚</div><p>几何论文档库</p><p style="font-size:13px;margin-top:4px;">从左侧选择文章开始阅读</p></div>';
        document.getElementById('breadcrumb-path').textContent = '';
    }
});
