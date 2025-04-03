import os
import shutil
import json
import tempfile
import zipfile
from tqdm import tqdm

# 检查依赖库
try:
    import requests
    import py7zr
    from tqdm import tqdm
except ImportError as e:
    print(f"\n! 缺少依赖库：{e}")
    print("请执行以下命令安装：")
    print("pip install requests py7zr tqdm")
    exit(1)


# 获取当前py文件所在目录的绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ==================== 工具函数 ====================
def print_step(title, step):
    """打印步骤标题"""
    print(f"\n{'='*30}")
    print(f"▶ 步骤{step}：{title}")
    print(f"{'='*30}")


def get_abs_path(*paths):
    """生成基于脚本目录的绝对路径"""
    return os.path.abspath(os.path.join(BASE_DIR, *paths))


def safe_create_dir(path):
    """安全创建目录，存在则忽略"""
    try:
        os.makedirs(path, exist_ok=True)
        print(f"✓ 目录已确认：{os.path.relpath(path, BASE_DIR)}")
    except Exception as e:
        print(f"✗ 创建目录失败：{e}")
        raise


def check_font_exists(font_dir):
    """检查字体目录是否包含符合条件的字体文件"""
    try:
        if not os.path.exists(font_dir):
            return False
            
        # 遍历字体目录查找符合条件的文件
        for filename in os.listdir(font_dir):
            lower_name = filename.lower()
            if lower_name.endswith('.otf') and 'bold' in lower_name:
                print(f"发现现有字体文件：{filename}")
                return True
        return False
    except Exception as e:
        print(f"字体检查失败：{e}")
        return False  # 出现异常视为需要下载


# ==================== 下载与解压 ====================
def download_file(url, filename):
    """带进度条的文件下载"""
    try:
        print(f"\n↓ 开始下载：{url}")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        
        with tqdm(total=total_size, unit='B', unit_scale=True, unit_divisor=1024) as pbar:
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        print(f"\n✓ 下载完成：{os.path.relpath(filename, BASE_DIR)}")
        return True
    except Exception as e:
        print(f"\n✗ 下载失败：{e}")
        return False


def extract_7z(archive_path, source_rel_path, dest_dir):
    """处理7z压缩包"""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"\n解压临时目录：{temp_dir}")
            
            with py7zr.SevenZipFile(archive_path, 'r') as z:
                z.extractall(temp_dir)
            
            source_path = os.path.join(temp_dir, *source_rel_path.split('/'))
            if not os.path.exists(source_path):
                raise FileNotFoundError(f"解压路径不存在：{source_path}")

            print(f"\n移动文件到：{os.path.relpath(dest_dir, BASE_DIR)}")
            if os.path.isdir(source_path):
                shutil.copytree(
                    source_path,
                    dest_dir,
                    dirs_exist_ok=True,
                    copy_function=shutil.copy2
                )
            else:
                shutil.copy2(source_path, dest_dir)
            
            print(f"✓ 文件移动完成")
            return True
    except Exception as e:
        print(f"\n✗ 7z解压失败：{e}")
        return False


def extract_zip(archive_path, dest_dir):
    """处理ZIP压缩包"""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"\n解压临时目录：{temp_dir}")
            
            with zipfile.ZipFile(archive_path, 'r') as z:
                z.extractall(temp_dir)
            
            # 查找目标字体文件
            def find_font(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        if file.lower().endswith('.otf') and "bold" in file.lower():
                            return os.path.join(root, file)
                return None
            
            if font_file := find_font(temp_dir):
                dest_path = os.path.join(dest_dir, os.path.basename(font_file))
                shutil.copy2(font_file, dest_path)
                print(f"\n✓ 字体文件已保存到：{os.path.relpath(dest_path, BASE_DIR)}")
                return True
            else:
                print("\n✗ 未找到符合条件的字体文件")
                return False
    except Exception as e:
        print(f"\n✗ ZIP解压失败：{e}")
        return False


# ==================== 主流程 ====================
def main():
    try:
        # 步骤1-2：创建目录结构
        print_step("初始化目录结构", "1-2")
        lang_dir = get_abs_path("LimbusCompany_Data", "Lang")
        lang1_dir = get_abs_path("LimbusCompany_Data", "Lang", "lang1")
        safe_create_dir(lang1_dir)

        # 步骤3：处理本地化资源
        print_step("下载本地化资源", 3)
        resource_url = "https://download.zeroasso.top/files/Resource/LimbusLocalize_Resource_latest.7z"
        resource_file = get_abs_path("LimbusLocalize_Resource_latest.7z")
        if download_file(resource_url, resource_file):
            if extract_7z(resource_file, "BepInEx/plugins/LLC/Localize/CN", lang1_dir):
                print("\n✓ 本地化资源安装成功")
            else:
                print("\n✗ 本地化资源安装失败")
            os.remove(resource_file)
            print(f"✓ 已清理资源压缩包")

        # 步骤4：创建字体目录
        print_step("创建字体目录", 4)
        font_dir = get_abs_path("LimbusCompany_Data", "Lang", "lang1", "Font")
        safe_create_dir(font_dir)

        # 步骤5：安装思源黑体
        print_step("安装思源黑体", 5)
        font_dir = get_abs_path("LimbusCompany_Data", "Lang", "lang1", "Font")
        
        # 先检查字体是否存在
        if check_font_exists(font_dir):
            print("\n✓ 检测到已有字体文件，跳过下载")
        else:
            font_url = "https://github.com/adobe-fonts/source-han-sans/releases/download/2.004R/SourceHanSansSC.zip"
            font_archive = get_abs_path("SourceHanSansSC.zip")
            if download_file(font_url, font_archive):
                if extract_zip(font_archive, font_dir):
                    print("\n✓ 字体安装成功")
                else:
                    print("\n✗ 字体安装失败")
                os.remove(font_archive)
                print(f"✓ 已清理字体压缩包")

        # 步骤6：配置文件
        print_step("生成配置文件", 6)
        config_path = get_abs_path("LimbusCompany_Data", "Lang", "config.json")
        if not os.path.exists(config_path):
            config = {"lang": "lang1"}
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            print(f"\n✓ 配置文件已创建：{os.path.relpath(config_path, BASE_DIR)}")
        else:
            print(f"\n✓ 配置文件已存在：{os.path.relpath(config_path, BASE_DIR)}")

        print("\n\n" + "="*30)
        print(f"✓✓✓ 所有操作已完成！工作目录：{BASE_DIR} ✓✓✓")
        print("="*30)

    except Exception as e:
        print("\n\n" + "!"*30)
        print(f"! 严重错误：{e}")
        print("!"*30)
        print("请检查：")
        print(f"1. 当前工作目录：{BASE_DIR}")
        print("2. 磁盘空间是否充足")
        print("3. 文件读写权限")


if __name__ == "__main__":
    main()
