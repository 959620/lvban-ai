from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import HTMLResponse

from app.api import api_router
from app.config import get_settings
from app.database import init_db
from app.openapi_docs import APP_DESCRIPTION, OPENAPI_TAGS
from app.schemas import HealthOut


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description=APP_DESCRIPTION,
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_tags=OPENAPI_TAGS,
        swagger_ui_parameters={
            "docExpansion": "list",
            "defaultModelsExpandDepth": 2,
            "persistAuthorization": True,
            "displayRequestDuration": True,
        },
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health", response_model=HealthOut, tags=["系统"], summary="健康检查")
    def health() -> HealthOut:
        """确认服务是否正常运行。"""
        return HealthOut(status="ok", app=settings.app_name)

    @app.get("/docs", include_in_schema=False)
    def swagger_docs() -> HTMLResponse:
        html = get_swagger_ui_html(
            openapi_url=app.openapi_url or "/openapi.json",
            title=f"{settings.app_name} · 接口文档",
            swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
            swagger_ui_parameters={
                "docExpansion": "list",
                "defaultModelsExpandDepth": 2,
                "persistAuthorization": True,
                "displayRequestDuration": True,
            },
        )
        # 将 Swagger UI 常用英文按钮替换为中文
        chinese_script = """
        <script>
        (function () {
          const dict = {
            "Authorize": "授权",
            "Available authorizations": "可用授权",
            "Close": "关闭",
            "Try it out": "试一试",
            "Cancel": "取消",
            "Execute": "执行",
            "Clear": "清除",
            "Responses": "响应",
            "Response body": "响应体",
            "Response headers": "响应头",
            "No response available": "暂无响应",
            "Server response": "服务器响应",
            "Request duration": "请求耗时",
            "Parameters": "参数",
            "Request body": "请求体",
            "Schemas": "数据模型",
            "Schema": "模型",
            "Example Value": "示例值",
            "Media type": "媒体类型",
            "Download": "下载",
            "Links": "链接",
            "No links": "无链接",
            "Filter by tag": "按标签筛选",
            "Loading...": "加载中…",
            "Failed to load API definition.": "加载接口定义失败。",
            "Fetch error": "请求错误",
            "logout": "退出授权",
            "Value:": "值：",
            "Username:": "用户名：",
            "Password:": "密码：",
            "Client credentials": "客户端凭证",
            "Password (OAuth2)": "密码模式 (OAuth2)",
            "Apply credentials": "应用凭证",
            "Authorized": "已授权",
            "Authorization Url": "授权地址",
            "Token Url": "令牌地址",
            "Flow": "流程",
            "In": "位置",
            "Name": "名称",
            "Description": "说明",
            "Required": "必填",
            "Code": "状态码",
            "Details": "详情",
            "Curl": "Curl 命令",
            "Request URL": "请求 URL"
          };

          function translateNode(node) {
            if (!node || node.nodeType !== Node.ELEMENT_NODE) return;
            if (node.childNodes && node.childNodes.length === 1 && node.childNodes[0].nodeType === Node.TEXT_NODE) {
              const text = node.textContent.trim();
              if (dict[text]) node.textContent = dict[text];
            }
            if (node.getAttribute) {
              ["title", "placeholder", "aria-label"].forEach((attr) => {
                const val = node.getAttribute(attr);
                if (val && dict[val]) node.setAttribute(attr, dict[val]);
              });
            }
          }

          function walk(root) {
            translateNode(root);
            root.querySelectorAll("*").forEach(translateNode);
          }

          const observer = new MutationObserver(() => walk(document.body));
          observer.observe(document.body, { childList: true, subtree: true, characterData: true });
          document.addEventListener("DOMContentLoaded", () => walk(document.body));
          setTimeout(() => walk(document.body), 800);
        })();
        </script>
        """
        content = html.body.decode("utf-8") if isinstance(html.body, bytes) else str(html.body)
        content = content.replace("</body>", chinese_script + "</body>")
        return HTMLResponse(content=content)

    @app.get("/redoc", include_in_schema=False)
    def redoc_docs() -> HTMLResponse:
        return get_redoc_html(
            openapi_url=app.openapi_url or "/openapi.json",
            title=f"{settings.app_name} · ReDoc 文档",
            redoc_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
        )

    app.include_router(api_router)
    return app


app = create_app()
