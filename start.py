"""
作业监督助手 - 一键启动脚本
启动后在 iPad 上通过局域网访问即可使用
"""

import http.server
import socketserver
import socket
import os
import sys
import webbrowser
import threading

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def get_local_ip():
    """获取本机局域网 IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    """静默 HTTP 处理器"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def log_message(self, format, *args):
        # 只显示重要日志
        if "200" not in str(args):
            super().log_message(format, *args)


def main():
    ip = get_local_ip()
    local_url = f"http://{ip}:{PORT}/homework-supervisor.html"

    print("=" * 50)
    print("  作业监督助手已启动")
    print("=" * 50)
    print()
    print(f"  iPad 访问地址: {local_url}")
    print()
    print("  使用方法:")
    print("  1. 确保 iPad 和电脑连接同一 WiFi")
    print("  2. 在 iPad Safari 中打开上面的地址")
    print("  3. 点击「开始使用」启动监督")
    print("  4. (可选) Safari 分享按钮 → 添加到主屏幕")
    print()
    print("  按 Ctrl+C 停止服务")
    print("=" * 50)

    # 自动打开浏览器
    webbrowser.open(f"http://localhost:{PORT}/homework-supervisor.html")

    with socketserver.TCPServer(("", PORT), QuietHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务已停止")


if __name__ == "__main__":
    main()
