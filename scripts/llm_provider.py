# -*- coding: utf-8 -*-
"""正式 LLM provider 配置解析(MIMO / DeepSeek)。

配置链(每环缺一不可,任一环缺失都在解析点显式失败):
    provider → model ID → base URL → API key 环境变量 → request payload
             → response parser → error handling

设计要点:
- **密钥只经环境变量进入**,绝不写入本模块、绝不打印、绝不进产物。
  历史的 `data/.llm_config` 里的 `api_key=` 行仅作 legacy 兜底(读取后同样不打印)。
- **MIMO V2.6 PRO 正式 model ID = `mimo-v2.6-pro`**,来源不是猜测:
  实测 `GET https://api.xiaomimimo.com/v1/models` 返回 9 个模型含此项,
  且以该 model 发起的真实调用成功(见 AITutor-X
  `Docs/60_REPORTS/E2E-VERIFICATION-EXECUTION-REPORT.md` §MEDIUM-04)。
- **`mimo-x-pro-preview` = LEGACY TEST MODEL CONFIG**。该 ID 已被 live API 拒绝
  (`400 Unsupported model mimo-x-pro-preview`),不得再作为正式 provider/model;
  解析到它即 fail-closed 报错,而不是留给 HTTP 400。
- DeepSeek provider 能力保留:同一套 provider registry,走 `DEEPSEEK_*` 环境变量。
  DeepSeek 的正式 model ID 项目内**无权威值**,故不设默认、显式配置才解析(不猜测)。
"""
from __future__ import annotations

import os
from pathlib import Path

# ── 正式目标常量 ──────────────────────────────────────────────────────────
DEFAULT_PROVIDER = "mimo"
MIMO_V26_PRO_MODEL = "mimo-v2.6-pro"   # 正式 MIMO V2.6 PRO(实测 /v1/models 返回)

# 已废弃的测试 model ID。允许出现在历史 fixture / 历史审计脚本里,
# 但绝不允许作为活跃生产配置(见模块 docstring)。
LEGACY_TEST_MODEL_IDS = ("mimo-x-pro-preview",)

# 配置链完全不可用时的元数据兜底标签(非机密)。刻意不含任何 legacy 测试 model ID。
UNCONFIGURED_TAG = "unconfigured-llm-provider"

PROVIDER_ENV = "LLM_PROVIDER"

# ── provider registry ────────────────────────────────────────────────────
# default_model 为空字符串 = 项目内无权威 model ID,必须显式配置,禁止猜测。
PROVIDERS: dict[str, dict[str, str]] = {
    "mimo": {
        "api_key_env": "MIMO_API_KEY",
        "base_url_env": "MIMO_BASE_URL",
        "model_env": "MIMO_MODEL",
        "default_base_url": "https://api.xiaomimimo.com/v1",
        "default_model": MIMO_V26_PRO_MODEL,
    },
    "deepseek": {
        "api_key_env": "DEEPSEEK_API_KEY",
        "base_url_env": "DEEPSEEK_BASE_URL",
        "model_env": "DEEPSEEK_MODEL",
        "default_base_url": "https://api.deepseek.com",
        "default_model": "",
    },
}


class ProviderConfigError(RuntimeError):
    """provider 配置链任一环缺失/非法时显式抛出(fail-closed)。

    继承 RuntimeError;但凡是"配置文件/配置缺失"场景,消息里都会点名
    `data/.llm_config` 与对应环境变量,便于定位(H-01:不吞异常、不静默回退)。
    """


def legacy_config_path(root: Path) -> Path:
    return root / "data" / ".llm_config"


def read_legacy_file(root: Path) -> dict[str, str]:
    """读历史 `data/.llm_config`(k=v 行)。文件缺失返回空 dict,不在此处报错。

    该文件 gitignored(`*llm_config*`),故 CI runner 上常态缺失——
    确定性路径(渲染/校验/QC)不得依赖它(见 tests/test_no_config_import.py)。
    """
    path = legacy_config_path(root)
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            k, v = line.strip().split("=", 1)
            out[k.strip()] = v.strip()
    return out


def resolve_provider_name(env: dict[str, str] | None = None) -> str:
    env = os.environ if env is None else env
    name = (env.get(PROVIDER_ENV) or DEFAULT_PROVIDER).strip().lower()
    if name not in PROVIDERS:
        raise ProviderConfigError(
            f"未知 LLM provider {name!r};已知: {sorted(PROVIDERS)}")
    return name


def _resolve_field(env: dict[str, str], legacy: dict[str, str],
                   env_key: str, legacy_key: str, default: str) -> str:
    """字段解析优先级:环境变量 → legacy 配置文件 → provider 默认值。"""
    val = (env.get(env_key) or "").strip()
    if val:
        return val
    val = (legacy.get(legacy_key) or "").strip()
    if val:
        return val
    return default


def resolve(root: Path, env: dict[str, str] | None = None) -> dict[str, str]:
    """解析完整 provider 配置。返回 dict:
    provider / model / base_url / api_key / api_key_env。

    api_key 仅在返回值内供请求头使用,**调用方不得打印/落盘**。
    """
    env = os.environ if env is None else env
    provider = resolve_provider_name(env)
    spec = PROVIDERS[provider]
    legacy = read_legacy_file(root)
    legacy_note = f"(或 legacy data/.llm_config)"

    model = _resolve_field(env, legacy, spec["model_env"], "model",
                           spec["default_model"])
    base_url = _resolve_field(env, legacy, spec["base_url_env"], "base_url",
                              spec["default_base_url"])

    if not model:
        raise ProviderConfigError(
            f"provider {provider!r} 缺少 model ID:请设置环境变量 "
            f"{spec['model_env']} 或 data/.llm_config 的 model=。"
            "项目内无该 provider 的权威 model ID,不做猜测。")

    if model in LEGACY_TEST_MODEL_IDS:
        raise ProviderConfigError(
            f"model {model!r} 是 LEGACY TEST MODEL CONFIG(live API 已拒绝 "
            f"'Unsupported model');正式 provider/model 不得使用它。"
            f"正式目标 = {MIMO_V26_PRO_MODEL!r}"
            f"(环境变量 {spec['model_env']} 或 data/.llm_config)。")

    # 密钥:优先环境变量,其次 legacy 文件 api_key=。两者皆无 → 显式失败。
    api_key_env = spec["api_key_env"]
    api_key = (env.get(api_key_env) or "").strip()
    if not api_key:
        api_key = (legacy.get("api_key") or "").strip()
        api_key_env = f"{spec['api_key_env']} 或 data/.llm_config 的 api_key="
    if not api_key:
        raise ProviderConfigError(
            f"缺少 {provider} API 凭证:请设置环境变量 {spec['api_key_env']}"
            f" {legacy_note}。密钥只经环境变量/该文件进入,"
            "不写入代码、不写入产物、永不打印。")

    if not base_url:
        raise ProviderConfigError(
            f"provider {provider!r} 缺少 base URL:请设置 "
            f"{spec['base_url_env']} 或 data/.llm_config 的 base_url=。")

    return {
        "provider": provider,
        "model": model,
        "base_url": base_url.rstrip("/"),
        "api_key": api_key,
        "api_key_env": api_key_env,
    }


def default_model_tag(root: Path, env: dict[str, str] | None = None) -> str:
    """产物元数据里的模型名。非机密、非功能性:配置缺失时回退 provider 默认名。

    真正的 LLM 调用不走此函数——缺配置仍由 resolve() 显式失败。
    """
    env = os.environ if env is None else env
    try:
        return resolve(root, env)["model"]
    except ProviderConfigError:
        return PROVIDERS[resolve_provider_name(env)]["default_model"] \
            or UNCONFIGURED_TAG


def assert_no_legacy_model(model: str) -> None:
    """静态检查钩子:活跃配置的 model 不得是已废弃测试 ID。"""
    if model in LEGACY_TEST_MODEL_IDS:
        raise ProviderConfigError(
            f"活跃配置仍在使用 LEGACY TEST MODEL {model!r}")
