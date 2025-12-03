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
<style>
  *{box-sizing:border-box}
  body{font-family:system-ui;background:#0b0d12;color:#e9eef7;margin:0}
  .wrap{max-width:880px;margin:48px auto;padding:24px}
  .card{background:#121722;border:1px solid #1e2636;border-radius:12px;padding:20px;box-shadow:0 6px 20px rgba(0,0,0,.25)}
  h1{font-size:22px;margin:0 0 16px}
  label{display:block;margin:14px 0 6px;color:#aab6cf}
  input{width:100%;padding:10px 12px;border:1px solid #283248;border-radius:10px;background:#0f1320;color:#cfe1ff;outline:none}
  input::placeholder{color:#6b7893}
  .row{display:flex;gap:16px}
  .row .col{flex:1}
  button{padding:10px 16px;border:0;border-radius:10px;background:#2a72ff;color:#fff;font-weight:600;cursor:pointer}
  button:disabled{opacity:.6;cursor:not-allowed}
  .actions{margin-top:16px;display:flex;gap:12px}
  .err{margin-top:12px;color:#ff6b6b}
  .section{margin-top:18px}
  .section h2{font-size:18px;margin:0 0 10px}
  .section .body{background:#0f1320;border:1px solid #283248;border-radius:10px;padding:14px}
  .list{margin:0;padding-left:18px}
  .badge{display:inline-block;padding:2px 8px;border-radius:8px;background:#182037;border:1px solid #283248;margin-right:8px;color:#aab6cf}
  .toolbar{display:flex;gap:8px;margin-top:12px}
  .hidden{display:none}
  .copy{margin-left:8px;padding:6px 10px;border-radius:8px;background:#182037;color:#aab6cf;border:1px solid #283248}
  .prog{margin-top:16px;background:#0f1320;border:1px solid #283248;border-radius:10px;padding:12px}
  .bar{height:10px;background:#182037;border-radius:8px;overflow:hidden}
  .fill{height:100%;width:0;background:linear-gradient(90deg,#2a72ff,#22d3ee);transition:width .35s ease}
  .pct{margin-top:8px;color:#aab6cf;font-size:13px}
  .hint{color:#8fa1c5;font-size:13px;margin-top:6px}
  .footer{margin-top:12px;color:#6b7893;font-size:12px}
</style>
<div class=wrap>
  <div class=card>
    <h1>输入仓库路径或 GitHub 地址</h1>
    <form id=f>
      <div class=row>
        <div class=col>
          <label>本地路径</label>
          <input name=path placeholder="/Users/me/projects/repo">
        </div>
        <div class=col>
          <label>GitHub 地址</label>
          <input name=repo_url placeholder="https://github.com/owner/repo">
          <div class=hint>示例：<code>https://github.com/DayuanJiang/next-ai-draw-io</code></div>
        </div>
      </div>
      <div class=actions>
        <button id=btn type=submit>分析</button>
        <button type=button id=demo>填入示例</button>
      </div>
      <div id=err class=err></div>
    </form>
    <div id=report></div>
    <div id=progressBox class="prog hidden">
      <div class=bar><div id=progressFill class=fill></div></div>
      <div id=progressPct class=pct>0%</div>
    </div>
    <div class=toolbar>
      <button id=toggleRaw class=copy>展开详细数据</button>
      <button id=copySteps class=copy>复制部署命令</button>
    </div>
    <div id=raw class="section hidden"><h2>原始解析数据（高级）</h2><div class=body><pre id=rawPre style="margin:0"></pre></div></div>
    <div class=footer>如仓库为私有，请先在本机配置 SSH 或 PAT。</div>
  </div>
  
  <div style="height:16px"></div>
  <div class=card>
    <h1>说明</h1>
    <div class=hint>分析结果以自然语言报告形式呈现，包含项目简介、能力分析、健康度、跨平台、部署步骤、运行方式、结构分析、风险与总结。</div>
  </div>
</div>
<script>
  const f=document.getElementById('f');
  const btn=document.getElementById('btn');
  const report=document.getElementById('report');
  const err=document.getElementById('err');
  const demo=document.getElementById('demo');
  const toggleRaw=document.getElementById('toggleRaw');
  const copySteps=document.getElementById('copySteps');
  const raw=document.getElementById('raw');
  const rawPre=document.getElementById('rawPre');
  demo.addEventListener('click', function(){ f.repo_url.value='https://github.com/DayuanJiang/next-ai-draw-io'; });
  function sanitizeRepo(u){
    try{ u = u.trim(); }catch(e){}
    u = u.split('`').join('');
    return u.replace(/\?[^#]*/,'');
  }
  function renderReport(j){
    const files=(j && j.parse && j.parse.files_found) || {};
    const present=Object.keys(files).filter(function(k){ return files[k]; });
    const lang=(j && j.project && j.project.language) || '未知';
    const start=(j && j.run && j.run.start) || '';
    const deps=(j && j.project && j.project.dependencies) || [];
    const pyVer=(j && j.project && j.project.python_required) || null;
    const nodeVer=(j && j.project && j.project.node_required) || null;
    const gpu=(j && j.project && j.project.gpu_required) ? '需要': '不需要';
    const arm=(j && j.project && j.project.arm_supported===true)? '支持' : ((j && j.project && j.project.arm_supported===false)? '可能不支持' : '未知');
    let score=60; if(start) score+=15; if(pyVer||nodeVer) score+=10; if(present.length>3) score+=5; if((j && j.project && j.project.gpu_required) && (j && j.project && j.project.arm_supported===false)) score-=15; if(score>100) score=100; if(score<0) score=0;
    const ok = !!start;
    const src = (j && j.source) || {};
    function list(items){ var s='<ul class=list>'; items.forEach(function(x){ s+='<li>'+x+'</li>'; }); return s+'</ul>'; }
    function section(title, body){ return '<div class=section><h2>'+title+'</h2><div class=body>'+body+'</div></div>'; }
    var html='';
    html+=section('【1】项目简介', '用途：根据仓库内容自动识别项目类型与运行方式，并生成本地部署计划。<br>类型：'+lang+' 项目或混合仓库。<br>亮点：自动提取启动命令、依赖与平台兼容性；支持本地报告展示。<br>价值：减少环境踩坑，让用户以人类易读的报告方式快速理解并部署。');
    var badges = present.length ? present.map(function(x){ return '<span class=badge>'+x+'</span>'; }).join(' ') : '未发现关键文件';
    html+=section('【2】项目能力分析', '核心功能：识别语言与版本、提取依赖与启动命令、生成部署计划。<br>辅助功能：文件存在性检查、ARM/GPU 需求判断、端口与运行方式提示。<br>核心流程：输入路径/URL → 解析 → 生成计划 → 展示报告。<br>检测到的关键文件：'+badges+' ');
    html+=section('【3】项目健康度 & 可运行性', '结论：'+(ok? '✔ 项目可正常运行（已识别启动命令）' : '❌ 项目可能无法直接运行（未识别启动命令）')+'<br>健康度评分：'+score+'/100');
    html+=section('【4】跨平台可运行性', 'Mac ARM：'+arm+'；GPU：'+gpu+'。<br>一般情况下，Node/Python 项目在 macOS/Linux/Windows 均可运行；如存在特定二进制或驱动需求需按仓库说明调整。');
    var repo = src.clone_url || src.repo_url || '';
    let steps='';
    var repoName = repo ? repo.split('/').pop().replace('.git','') : '<repo>';
    if(lang==='node'){
      steps = 'git clone '+(repo || '<repo>')+'<br>cd '+repoName+'<br>npm install<br>npm start';
    } else if(lang==='python'){
      steps = 'git clone '+(repo || '<repo>')+'<br>cd '+repoName+'<br>pip install -r requirements.txt<br>python main.py';
    } else if(lang==='docker'){
      steps = 'git clone '+(repo || '<repo>')+'<br>cd '+repoName+'<br>docker-compose up';
    } else {
      steps = 'git clone '+(repo || '<repo>')+'<br>cd '+repoName+'<br>按 README 指南执行安装与启动';
    }
    var doc = '准备：确认已安装必要工具（Node/Python/Docker）。如为私有仓库，请预先配置 SSH 或 PAT。<br>执行：按下方命令逐步执行。若出现依赖或网络问题，请参考问题与解决方案。';
    html+=section('【5】部署步骤（可直接执行）', doc+'<br><br>'+steps);
    html+=section('【6】服务运行方式 & 使用说明', '启动命令：'+(start || '未识别，请参考 README 或 package.json/scripts')+'<br>默认端口：如为 Web 服务，通常为 3000/8000/5173 等，以项目实际为准。');
    const fkeys = Object.keys(files);
    html+=section('【7】项目结构分析（简述）', fkeys.length? list(fkeys.map(function(k){ return k+'：'+(files[k]? '存在' : '缺失'); })) : '未检测到结构信息');
    var issues = [];
    if(!ok){ issues.push('未识别启动命令：在 README 或 package.json 中明确启动方式，或在根目录添加 main.py/app.py'); }
    if(!(deps && deps.length) && lang!=='docker'){ issues.push('未检测到依赖文件：建议补充 requirements.txt 或 package.json 以便可重复安装'); }
    if(gpu==='需要' && arm==='可能不支持'){ issues.push('GPU 与 ARM 兼容性：在 Mac ARM 上建议切换到 CPU/MPS 模式或选择兼容包'); }
    issues.push('端口占用：若启动失败提示端口占用，修改端口或关闭占用进程后重试');
    issues.push('私有仓库：拉取失败请配置 SSH 密钥或 PAT，并确认网络代理');
    var fixes = list([
      'Pip 安装失败：切换国内源（如清华），尝试 universal2 轮子，安装缺失的 brew 包',
      'Node 版本不符：使用 nvm 切换到要求版本（如 Node 18），再重新安装依赖',
      'Docker 不可用：安装 Docker Desktop 或改用本地 venv/uv 运行路径',
      '模型/资源缺失：根据 README 下载到指定目录并在配置文件中声明路径'
    ]);
    html+=section('【8】可能遇到的问题与解决方案', (issues.length? list(issues):'暂无明显风险') + '<br><br>通用解决方案：'+fixes);
    html+=section('【9】总结', '该仓库已可被解析并生成人类可读报告；部署难度取决于依赖与启动脚本完整度。适合快速理解与本地验证，如需生产部署建议补充容器化与配置向导。');
    report.innerHTML=html;
    raw.classList.add('hidden');
    rawPre.textContent=JSON.stringify(j,null,2);
    copySteps.onclick=function(){
      try{ navigator.clipboard.writeText(steps.replace(/<br>/g,"\\n")); }catch(e){}
    };
  }
  function setProgress(p,label){
    try{
      var box=document.getElementById('progressBox');
      var fill=document.getElementById('progressFill');
      var pct=document.getElementById('progressPct');
      box.classList.remove('hidden');
      fill.style.width=Math.max(0,Math.min(100,p))+'%';
      pct.textContent=(Math.max(0,Math.min(100,p)))+'%'+(label?(' · '+label):'');
    }catch(e){}
  }
  toggleRaw.addEventListener('click', function(){
    if(raw.classList.contains('hidden')){ raw.classList.remove('hidden'); toggleRaw.textContent='收起详细数据'; }
    else{ raw.classList.add('hidden'); toggleRaw.textContent='展开详细数据'; }
  });
  f.addEventListener('submit', function(e){
    e.preventDefault();
    err.textContent=''; report.innerHTML='';
    setProgress(5,'准备');
    const path=f.path.value.trim();
    const repo=sanitizeRepo(f.repo_url.value.trim());
    const q=new URLSearchParams();
    if(path) q.set('path',path);
    if(repo) q.set('repo_url',repo);
    if(!path && !repo){ err.textContent='请填写本地路径或有效的 GitHub 地址'; return; }
    btn.disabled=true; btn.textContent='分析中...';
    var ticking=true;
    var t1=setInterval(function(){ if(!ticking) return; var p=document.getElementById('progressFill').style.width; setProgress(Math.min(90, (parseInt(p)||5)+8),'解析仓库'); }, 400);
    fetch('/analyze?'+q.toString())
      .then(function(r){
        const ct=(r.headers && r.headers.get && r.headers.get('content-type')) || '';
        if(!r.ok){ throw new Error('请求失败：'+r.status); }
        if(ct.indexOf('application/json')>=0){ return r.json(); }
        return r.text().then(function(t){ throw new Error('服务器返回非JSON：'+t.slice(0,120)); });
      })
      .then(function(j){
        ticking=false; clearInterval(t1); setProgress(95,'生成计划');
        if(j.error){ err.textContent=j.error; } else { renderReport(j); }
        setTimeout(function(){ setProgress(100,'完成'); }, 300);
      })
      .catch(function(ex){ err.textContent=String(ex); setProgress(0,'失败'); })
      .finally(function(){ btn.disabled=false; btn.textContent='分析'; });
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
        self.send_header("Cache-Control", "no-store")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        path_only = parsed.path or "/"
        if path_only == "/" or path_only.startswith("/index"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Pragma", "no-cache")
            html = INDEX_HTML.encode("utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
            return

        if path_only.startswith("/analyze"):
            qs = parse_qs(parsed.query)
            path = (qs.get("path") or [""])[0]
            repo_url = (qs.get("repo_url") or [""])[0]
            try:
                root = path
                if not root and repo_url:
                    u = repo_url.strip().strip("`")
                    p = urlparse(u)
                    if p.netloc.endswith("github.com"):
                        seg = [s for s in p.path.split("/") if s]
                        if len(seg) >= 2:
                            u = f"https://github.com/{seg[0]}/{seg[1]}.git"
                    root = safe_clone(u)
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
                    "source": {
                        "source_path": root,
                        "repo_url": repo_url,
                        "clone_url": (u if repo_url else None)
                    }
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
    while True:
        try:
            srv = HTTPServer(("127.0.0.1", port), Handler)
            break
        except OSError as e:
            msg = str(e).lower()
            if "address already in use" in msg or "errno 48" in msg:
                port += 1
                continue
            raise
    print(f"http://localhost:{port}/")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
