import json
import os
import sys
import tempfile
import subprocess
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler

from src.autodeploy.repo_parser import parse_project
from src.autodeploy.env_manager import plan_environment
from src.autodeploy.runner import build_run


INDEX_HTML = """
<!doctype html>
<html lang=zh>
<meta charset=utf-8>
<title>AIautogithub 本地分析</title>
<style>body{font-family:system-ui;margin:24px}input,button{font-size:16px;padding:8px}pre{background:#f6f8fa;padding:12px;overflow:auto;border:1px solid #ddd}</style>
<h2>输入仓库路径或 GitHub 地址</h2>
<form id=f>
  <label>本地路径: <input name=path style="width:420px"></label>
  <br><br>
  <label>GitHub 地址: <input name=repo_url style="width:420px" placeholder="https://github.com/user/repo"></label>
  <br><br>
  <button type=submit>分析</button>
</form>
<h3>结果</h3>
<pre id=out></pre>
<script>
  const f=document.getElementById('f');
  f.addEventListener('submit', async (e)=>{
    e.preventDefault();
    const path=f.path.value.trim();
    const repo=f.repo_url.value.trim();
    const q=new URLSearchParams();
    if(path) q.set('path',path);
    if(repo) q.set('repo_url',repo);
    const r=await fetch('/analyze?'+q.toString());
    const j=await r.json();
    out.textContent=JSON.stringify(j,null,2);
  });
</script>
"""


def safe_clone(url: str) -> str:
    tmp = tempfile.mkdtemp(prefix="aiag-")
    try:
        subprocess.run(["git", "clone", "--depth", "1", url, tmp], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return tmp
    except Exception as e:
        raise RuntimeError(f"Git clone 失败: {e}")


class Handler(BaseHTTPRequestHandler):
    def _json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/index"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            html = INDEX_HTML.encode("utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
            return

        if self.path.startswith("/analyze"):
            qs = parse_qs(urlparse(self.path).query)
            path = (qs.get("path") or [""])[0]
            repo_url = (qs.get("repo_url") or [""])[0]
            try:
                root = path
                if not root and repo_url:
                    root = safe_clone(repo_url)
                if not root:
                    return self._json({"error": "需要提供 path 或 repo_url"}, 400)
                spec, result = parse_project(root)
                plan = plan_environment(spec)
                run = build_run(spec, plan)
                return self._json({
                    "project": spec.__dict__,
                    "parse": {
                        "files_found": result.files_found,
                        "warnings": result.warnings,
                        "suggestions": result.suggestions,
                    },
                    "plan": plan.__dict__,
                    "run": run,
                })
            except Exception as e:
                return self._json({"error": str(e)}, 500)

        self.send_response(404)
        self.end_headers()


def main():
    port = 5173
    if "--port" in sys.argv:
        try:
            i = sys.argv.index("--port")
            port = int(sys.argv[i+1])
        except Exception:
            pass
    srv = HTTPServer(("127.0.0.1", port), Handler)
    print(f"http://localhost:{port}/")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
