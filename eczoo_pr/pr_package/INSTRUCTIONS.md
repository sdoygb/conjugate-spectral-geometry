# 提交步骤（需要 GitHub 账号）

1. Fork: https://github.com/errorcorrectionzoo/eczoo_data （网页点 Fork）
2. 本地：git clone <你的fork>；然后把本目录两个文件复制进去：
   - quantum_reed_muller_modified.yml -> codes/quantum/qubits/stabilizer/rm/quantum_reed_muller.yml
   - users_db_modified.yml -> users/users_db.yml
3. 提交前请确认/更新 users_db 里的 name 和 githubusername（当前是占位 'Ouyang Guobin'，
   无 githubusername 字段；建议加上你的真实 GitHub 用户名）
4. git commit -m "quantum_reed_muller: add self-orthogonal CSS(RM(r,m)) family and certified distance"
   git push；开 PR（draft），body 用 PR_BODY.md 内容
5. 到 https://errorcorrectionzoo.org/gitpreview 输入 PR 编号预览
6. 预览无误后去掉 draft 标记；维护者（Victor）会 review
