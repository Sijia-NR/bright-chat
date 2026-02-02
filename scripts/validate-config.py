#!/usr/bin/env python3
"""
Bright-Chat 配置验证脚本
Configuration Validation Script

用途: 验证环境变量和配置文件的正确性
Usage: python scripts/validate-config.py [--env-file .env] [--check-ports]
"""

import os
import sys
import socket
import argparse
from pathlib import Path
from typing import List, Tuple, Dict, Any


class Colors:
    """终端颜色"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


def print_success(message: str):
    """打印成功消息"""
    print(f"{Colors.GREEN}✓ {message}{Colors.NC}")


def print_error(message: str):
    """打印错误消息"""
    print(f"{Colors.RED}✗ {message}{Colors.NC}")


def print_warning(message: str):
    """打印警告消息"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.NC}")


def print_info(message: str):
    """打印信息消息"""
    print(f"{Colors.BLUE}ℹ {message}{Colors.NC}")


def check_port_available(port: int, host: str = 'localhost') -> bool:
    """检查端口是否可用"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            return result != 0  # 0 表示端口被占用
    except Exception as e:
        print_warning(f"检查端口 {port} 时出错: {e}")
        return True  # 出错时假设端口可用


def validate_port_range(port: int) -> bool:
    """验证端口范围"""
    return 1024 <= port <= 65535


def load_env_file(env_file: str) -> Dict[str, str]:
    """加载 .env 文件"""
    env_vars = {}
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过注释和空行
                if not line or line.startswith('#'):
                    continue
                # 解析键值对
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    except FileNotFoundError:
        print_error(f"环境变量文件不存在: {env_file}")
        return {}
    except Exception as e:
        print_error(f"加载环境变量文件失败: {e}")
        return {}

    return env_vars


def validate_required_vars(env_vars: Dict[str, str]) -> bool:
    """验证必需的环境变量"""
    required_vars = [
        'APP_NAME',
        'DB_HOST',
        'DB_PORT',
        'DB_USERNAME',
        'DB_PASSWORD',
        'DB_DATABASE',
        'JWT_SECRET_KEY',
    ]

    print("\n" + "=" * 50)
    print("验证必需的环境变量")
    print("=" * 50)

    all_valid = True
    for var in required_vars:
        value = env_vars.get(var)
        if value:
            # 检查是否是默认值或示例值
            if any(x in value.lower() for x in ['change', 'me', 'example', 'your-', 'changeme']):
                print_warning(f"{var}: 包含默认值,需要修改")
                all_valid = False
            else:
                print_success(f"{var}: 已设置")
        else:
            print_error(f"{var}: 未设置")
            all_valid = False

    return all_valid


def validate_jwt_secret(env_vars: Dict[str, str]) -> bool:
    """验证 JWT 密钥强度"""
    jwt_key = env_vars.get('JWT_SECRET_KEY', '')
    print("\n" + "=" * 50)
    print("验证 JWT 密钥强度")
    print("=" * 50)

    if len(jwt_key) < 32:
        print_error(f"JWT 密钥长度不足: {len(jwt_key)} 字符 (至少需要32字符)")
        return False

    if any(x in jwt_key.lower() for x in ['change', 'me', 'example', 'default']):
        print_error("JWT 密钥包含默认值,必须修改")
        return False

    print_success(f"JWT 密钥强度: {len(jwt_key)} 字符")
    return True


def validate_ports(env_vars: Dict[str, str], check_available: bool = False) -> bool:
    """验证端口配置"""
    port_vars = {
        'SERVER_PORT': '后端服务',
        'MYSQL_PORT': 'MySQL 数据库',
        'REDIS_PORT': 'Redis 缓存',
        'CHROMADB_PORT': 'ChromaDB 向量库',
        'BACKEND_PORT': 'Backend (Docker)',
        'AGENT_SERVICE_PORT': 'Agent Service',
        'FRONTEND_PORT': 'Frontend',
        'NGINX_HTTP_PORT': 'Nginx HTTP',
    }

    print("\n" + "=" * 50)
    print("验证端口配置")
    print("=" * 50)

    all_valid = True
    used_ports = []

    for var, description in port_vars.items():
        port_str = env_vars.get(var)
        if not port_str:
            print_warning(f"{description} ({var}): 未设置")
            continue

        try:
            port = int(port_str)

            # 验证端口范围
            if not validate_port_range(port):
                print_error(f"{description} ({var}): 端口 {port} 超出范围 (1024-65535)")
                all_valid = False
                continue

            # 检查端口重复
            if port in used_ports:
                print_error(f"{description} ({var}): 端口 {port} 重复使用")
                all_valid = False
                continue

            used_ports.append(port)

            # 检查端口可用性
            if check_available:
                if check_port_available(port):
                    print_success(f"{description} ({var}): 端口 {port} 可用")
                else:
                    print_warning(f"{description} ({var}): 端口 {port} 已被占用")
            else:
                print_success(f"{description} ({var}): 端口 {port}")

        except ValueError:
            print_error(f"{description} ({var}): 端口值无效 '{port_str}'")
            all_valid = False

    return all_valid


def validate_database_config(env_vars: Dict[str, str]) -> bool:
    """验证数据库配置"""
    print("\n" + "=" * 50)
    print("验证数据库配置")
    print("=" * 50)

    db_driver = env_vars.get('DB_DRIVER')
    if db_driver == 'mysql':
        print_success(f"数据库驱动: {db_driver}")

        db_host = env_vars.get('DB_HOST')
        db_port = env_vars.get('DB_PORT')
        db_name = env_vars.get('DB_DATABASE')

        print_info(f"数据库地址: {db_host}:{db_port}")
        print_info(f"数据库名称: {db_name}")

        return True
    else:
        print_warning(f"不支持的数据库驱动: {db_driver}")
        return False


def validate_llm_config(env_vars: Dict[str, str]) -> bool:
    """验证 LLM 配置"""
    print("\n" + "=" * 50)
    print("验证 LLM 配置")
    print("=" * 50)

    llm_provider = env_vars.get('LLM_PROVIDER')
    llm_model = env_vars.get('LLM_MODEL')
    llm_api_key = env_vars.get('LLM_API_KEY')

    print_info(f"LLM 提供商: {llm_provider}")
    print_info(f"LLM 模型: {llm_model}")

    if llm_api_key and any(x in llm_api_key.lower() for x in ['your-', 'change', 'example']):
        print_warning("LLM API Key 包含默认值,需要修改")
        return False

    if llm_api_key:
        print_success("LLM API Key: 已设置")
        return True
    else:
        print_warning("LLM API Key: 未设置")
        return False


def validate_security_config(env_vars: Dict[str, str]) -> bool:
    """验证安全配置"""
    print("\n" + "=" * 50)
    print("验证安全配置")
    print("=" * 50)

    app_debug = env_vars.get('APP_DEBUG', 'false').lower()
    app_env = env_vars.get('APP_ENV', 'development')

    # 检查生产环境配置
    if app_env == 'production':
        if app_debug == 'true':
            print_error("生产环境不应开启 DEBUG 模式")
            return False
        print_success("生产环境配置: DEBUG 已关闭")
    else:
        print_info(f"环境模式: {app_env}")

    # CORS 配置
    cors_origins = env_vars.get('CORS_ORIGINS', '')
    if cors_origins == '*' or 'all' in cors_origins.lower():
        print_warning("CORS 配置允许所有源,生产环境建议限制")
    else:
        print_success("CORS 配置: 已限制")

    # SSL
    ssl_verify = env_vars.get('SSL_VERIFY', 'false').lower()
    if ssl_verify == 'true':
        print_success("SSL 验证: 已启用")
    else:
        print_warning("SSL 验证: 未启用")

    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Bright-Chat 配置验证脚本')
    parser.add_argument(
        '--env-file',
        default='.env',
        help='环境变量文件路径 (默认: .env)'
    )
    parser.add_argument(
        '--check-ports',
        action='store_true',
        help='检查端口是否被占用'
    )
    parser.add_argument(
        '--production',
        action='store_true',
        help='验证生产环境配置'
    )

    args = parser.parse_args()

    print(f"\n{Colors.BLUE}{'=' * 50}{Colors.NC}")
    print(f"{Colors.BLUE}Bright-Chat 配置验证工具{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 50}{Colors.NC}")

    # 加载环境变量
    env_file = args.env_file
    if args.production:
        env_file = '.env.production'

    print(f"\n验证配置文件: {env_file}")
    env_vars = load_env_file(env_file)

    if not env_vars:
        print_error("无法加载环境变量文件")
        sys.exit(1)

    # 执行验证
    results = []

    results.append(("必需变量", validate_required_vars(env_vars)))
    results.append(("JWT密钥", validate_jwt_secret(env_vars)))
    results.append(("端口配置", validate_ports(env_vars, args.check_ports)))
    results.append(("数据库配置", validate_database_config(env_vars)))
    results.append(("LLM配置", validate_llm_config(env_vars)))
    results.append(("安全配置", validate_security_config(env_vars)))

    # 总结
    print("\n" + "=" * 50)
    print("验证总结")
    print("=" * 50)

    all_passed = True
    for name, passed in results:
        status = f"{Colors.GREEN}通过{Colors.NC}" if passed else f"{Colors.RED}失败{Colors.NC}"
        symbol = "✓" if passed else "✗"
        print(f"{symbol} {name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 50)

    if all_passed:
        print_success("所有验证通过!")
        print("\n下一步:")
        print("  1. 启动服务: docker-compose up -d")
        print("  2. 检查健康: curl http://localhost:9003/health")
        return 0
    else:
        print_error("部分验证失败,请检查配置")
        return 1


if __name__ == '__main__':
    sys.exit(main())
