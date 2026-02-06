# 测试账号信息

## 学生端测试账号

| 项目 | 值 |
|------|-----|
| **用户名** | `test_student` |
| **密码** | `Test1234` |
| **邮箱** | `student@test.com` |
| **角色** | 学生 (student) |
| **学号** | S2024001 |
| **年级** | 大一 |
| **目标考试** | CET4 |
| **目标分数** | 500 |
| **当前水平** | B1 (intermediate) |

## 教师端测试账号

| 项目 | 值 |
|------|-----|
| **用户名** | `test_teacher` |
| **密码** | `Test1234` |
| **邮箱** | `teacher@test.com` |
| **角色** | 教师 (teacher) |
| **专业领域** | 英语口语、写作教学、语法 |
| **简介** | 专注于AI辅助英语教学，拥有10年教学经验 |

## 登录 API 示例

**学生登录**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test_student", "password": "Test1234"}'
```

**教师登录**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test_teacher", "password": "Test1234"}'
```

## 环境要求

- Docker PostgreSQL: english_teaching_postgres
- Docker Redis: english_Teaching_redis
- 后端服务: english_teaching_backend

## 测试注意事项

- 测试前确保 Docker 服务正在运行
- 单元测试 conftest.py 已配置使用 Docker PostgreSQL
- SQLAlchemy ARRAY 列类型需要 PostgreSQL，SQLite 不支持
