"""
Locust 压力测试脚本

使用方法:
    locust -f tests/performance/locustfile.py --host http://localhost:8000

分布式测试:
    locust -f tests/performance/locustfile.py --master --host http://localhost:8000
    locust -f tests/performance/locustfile.py --worker --master-host <master-ip>
"""
import time
import uuid
from typing import Optional
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner


class APIAuthBehavior:
    """API认证行为模拟"""

    def __init__(self, client):
        self.client = client
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.user_id: Optional[str] = None

    def login(self) -> bool:
        """模拟登录"""
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "username": "test_student",
                "email": "student@test.com",
                "password": "Test1234"
            },
            catch_response=True
        )
        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")
            self.user_id = data.get("user", {}).get("id")
            return True
        return False

    def get_headers(self) -> dict:
        """获取带认证的请求头"""
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers


class StudentUser(HttpUser):
    """学生用户行为模拟"""

    # 等待时间: 1-3秒之间随机
    wait_time = between(1, 3)

    def on_start(self):
        """用户启动时执行"""
        self.auth = APIAuthBehavior(self)
        # 登录获取token
        max_retries = 3
        for _ in range(max_retries):
            if self.auth.login():
                break
            time.sleep(1)

    def on_stop(self):
        """用户停止时执行"""
        # 可以在这里执行清理操作
        pass

    @task(10)
    def get_current_user(self):
        """获取当前用户信息 (高频操作)"""
        if not self.auth.access_token:
            self.auth.login()

        self.client.get(
            "/api/v1/auth/me",
            headers=self.auth.get_headers(),
            catch_response=True,
            name="/api/v1/auth/me"
        )

    @task(5)
    def get_recommendations(self):
        """获取每日推荐 (中频操作)"""
        if not self.auth.user_id:
            self.auth.login()

        self.client.get(
            f"/api/v1/students/{self.auth.user_id}/recommendations",
            headers=self.auth.get_headers(),
            catch_response=True,
            name="/api/v1/students/[id]/recommendations"
        )

    @task(3)
    def get_mistakes(self):
        """获取错题本 (低频操作)"""
        if not self.auth.access_token:
            self.auth.login()

        self.client.get(
            "/api/v1/mistakes/me",
            headers=self.auth.get_headers(),
            catch_response=True,
            name="/api/v1/mistakes/me"
        )

    @task(2)
    def get_reports(self):
        """获取学习报告 (低频操作)"""
        if not self.auth.access_token:
            self.auth.login()

        self.client.get(
            "/api/v1/reports/me",
            headers=self.auth.get_headers(),
            catch_response=True,
            name="/api/v1/reports/me"
        )

    @task(1)
    def health_check(self):
        """健康检查 (最低频)"""
        self.client.get(
            "/health",
            catch_response=True,
            name="/health"
        )


class TeacherUser(HttpUser):
    """教师用户行为模拟"""

    wait_time = between(2, 5)

    def on_start(self):
        """用户启动时执行"""
        self.auth = APIAuthBehavior(self)
        # 教师登录
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "username": "test_teacher",
                "email": "teacher@test.com",
                "password": "Test1234"
            },
            catch_response=True
        )
        if response.status_code == 200:
            data = response.json()
            self.auth.access_token = data.get("access_token")
            self.auth.refresh_token = data.get("refresh_token")
            self.auth.user_id = data.get("user", {}).get("id")

    @task(8)
    def get_question_banks(self):
        """获取题库列表"""
        if not self.auth.access_token:
            return

        self.client.get(
            "/api/v1/question-banks",
            headers=self.auth.get_headers(),
            catch_response=True,
            name="/api/v1/question-banks"
        )

    @task(5)
    def get_lesson_plans(self):
        """获取教案列表"""
        if not self.auth.access_token:
            return

        self.client.get(
            "/api/v1/lesson-plans",
            headers=self.auth.get_headers(),
            catch_response=True,
            name="/api/v1/lesson-plans"
        )

    @task(3)
    def get_student_list(self):
        """获取学生列表"""
        if not self.auth.access_token:
            return

        self.client.get(
            "/api/v1/users/students",
            headers=self.auth.get_headers(),
            catch_response=True,
            name="/api/v1/users/students"
        )


# 自定义事件处理器
def on_locust_init(environment, runner, **kwargs):
    """Locust初始化事件"""
    if isinstance(runner, MasterRunner):
        print(f"Master started. Target user count: {runner.target_user_count}")
    print(f"Locust environment initialized: {environment}")


def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """请求完成事件"""
    if exception:
        print(f"Request failed: {name} - {exception}")
    else:
        # 可以在这里记录到日志或监控系统
        pass


# 注册事件处理器
events.init.add_listener("locust_init", on_locust_init)
events.request.add_listener("request", on_request)
