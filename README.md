# LinuxDynamicLibDepsAnalysis

用于扫描 Linux 本地动态库目录，解析 `.so` 之间的依赖关系，并生成一个可交互的 HTML 拓扑图。

当前实现聚焦于：
- Linux ELF 动态库依赖分析
- Mermaid 风格的依赖拓扑可视化
- 单文件 HTML 输出，便于分发和归档

## 项目结构

- `SOrder.py`
  命令行入口。只负责参数解析、调用分析模块、调用 HTML 渲染模块。
- `dependency_analyzer.py`
  依赖分析模块。负责扫描目录、提取 ELF 元数据、构建依赖图、识别循环依赖、整理报告数据。
- `html_report.py`
  HTML 报告渲染模块。负责把分析结果转换成自包含交互页面。
- `requirements-optional.txt`
  可选 Python 依赖列表。

## 功能特性

- 支持扫描一个或多个根目录
- 默认生成 HTML 报告，不输出 JSON
- 默认优先观察直接依赖，可按层级展开
- 支持按目标动态库切换焦点
- 点击图中节点可切换当前分析目标
- 支持隐藏循环依赖虚线
- 支持导出当前 SVG 图
- 底部状态栏显示未解析依赖和当前分析库摘要

## 环境要求

- Python 3.9+
- Linux 环境
- 系统中可用 `readelf`

默认不强制依赖第三方 Python 包。

## 安装

直接使用：

```bash
python3 SOrder.py --root /path/to/lib
```

如果你希望更稳定地解析 ELF 元数据，可以安装可选依赖：

```bash
pip install -r requirements-optional.txt
```

## 使用方式

基础用法：

```bash
python3 SOrder.py --root /path/to/lib
```

指定输出文件：

```bash
python3 SOrder.py --root /path/to/lib --output /tmp/deps.html
```

指定初始焦点库：

```bash
python3 SOrder.py --root /path/to/lib --focus libexample.so
```

仅扫描当前目录，不递归子目录：

```bash
python3 SOrder.py --root /path/to/lib --no-recursive
```

扫描多个目录：

```bash
python3 SOrder.py --root /path/to/lib --root /another/lib/dir
```

默认输出文件为：

```text
<common-root>/so_dependencies.html
```

## 页面交互说明

- 左上角工具条：
  选择目标库、最大层级、虚线开关、SVG 导出
- 主视图区：
  显示自上而下的依赖拓扑图
- 点击节点：
  切换当前焦点库并重新渲染
- 底部状态栏：
  左侧显示未解析依赖，右侧显示当前分析库摘要

## 解析后端

默认策略：

- 优先使用 `pyelftools`，如果已安装
- 否则回退到系统 `readelf`

当前项目主要针对 Linux ELF `.so` 文件。

不支持：

- Windows `.lib` / `.dll`
- macOS `.dylib`

如果要扩展到这些格式，需要补充对应的二进制格式解析逻辑。

## 可选依赖

- `pyelftools`
  Python 侧 ELF 解析
- Mermaid
  前端依赖图渲染，通过 CDN 加载

说明：

- Python 可选依赖写在 `requirements-optional.txt`
- Mermaid 当前由生成的 HTML 通过 CDN 引入
- 如果你需要完全离线打开 HTML，可以把前端脚本改成本地静态资源

## GitHub 上传前建议

建议不要提交以下内容：

- `__pycache__/`
- 本地生成的 HTML 报告
- 临时测试输出

本仓库已经提供 `.gitignore` 处理这些常见文件。

如果你准备公开仓库，建议额外补充：

- `LICENSE`
- GitHub Release 示例截图
- 一份最小测试样本目录

## 已验证命令

```bash
python3 -m py_compile SOrder.py dependency_analyzer.py html_report.py
python3 SOrder.py --root /lib/x86_64-linux-gnu --no-recursive --output so_dependencies_cytoscape.html --focus libc.so.6
```
