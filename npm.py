import os
import sys
import tarfile
import shutil
import requests
import zipfile
from urllib.request import urlretrieve

def fetch_tarball_url(package_name):
    try:
        print(f"🔍 パッケージ情報取得中: {package_name}")
        res = requests.get(f"https://registry.npmjs.org/{package_name}")
        res.raise_for_status()
        data = res.json()
        latest_version = data["dist-tags"]["latest"]
        tarball_url = data["versions"][latest_version]["dist"]["tarball"]
        return tarball_url
    except Exception as e:
        print(f"❌ {package_name} の取得に失敗: {e}")
        return None

def download_tarball(url, dest_path):
    try:
        print(f"⬇️ ダウンロード中: {url}")
        urlretrieve(url, dest_path)
        print(f"✅ ダウンロード完了: {dest_path}")
        return True
    except Exception as e:
        print(f"❌ ダウンロード失敗: {e}")
        return False

def extract_tarball(tar_path, extract_to):
    try:
        print(f"📦 解凍中: {tar_path}")
        with tarfile.open(tar_path, "r:gz") as tar:
            temp_dir = "__temp_extract__"
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            tar.extractall(temp_dir)

            pkg_path = os.path.join(temp_dir, "package")
            if os.path.exists(pkg_path):
                if os.path.exists(extract_to):
                    shutil.rmtree(extract_to)
                shutil.move(pkg_path, extract_to)
                print(f"📁 展開先: {extract_to}")
            else:
                print("⚠️ package フォルダが見つかりません")
        shutil.rmtree(temp_dir)
        os.remove(tar_path)
    except Exception as e:
        print(f"❌ 解凍エラー: {e}")

def zip_package_folder(package_name, node_modules_dir, output_dir):
    folder_path = os.path.join(node_modules_dir, package_name)
    zip_path = os.path.join(output_dir, f"{package_name}.zip")

    print(f"🗜 圧縮中: {zip_path}")

    if not os.path.exists(folder_path):
        print(f"❌ 圧縮対象が存在しません: {folder_path}")
        return

    os.makedirs(output_dir, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, folder_path)
                    zipf.write(full_path, rel_path)
        print(f"✅ ZIP作成完了: {zip_path}")
    except Exception as e:
        print(f"❌ ZIP作成失敗: {e}")

def install_package(package_name, node_modules_dir):
    tarball_url = fetch_tarball_url(package_name)
    if not tarball_url:
        return False

    filename = f"{package_name.replace('/', '_')}.tgz"
    dest_dir = os.path.join(node_modules_dir, package_name.split('/')[-1])
    os.makedirs(node_modules_dir, exist_ok=True)

    if download_tarball(tarball_url, filename):
        extract_tarball(filename, dest_dir)
        return True
    return False

def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="NPMライブラリ自動ダウンローダー")
    parser.add_argument("-p", "--packages", nargs="+", required=True, help="インストールするnpmパッケージ群")
    parser.add_argument("-o", "--output", default=".", help="出力先ディレクトリ")
    parser.add_argument("-z", "--zip", action="store_true", help="ZIPファイルとしても出力")
    return parser.parse_args()

def main():
    args = parse_args()

    out_dir = args.output
    node_modules_dir = os.path.join(out_dir, "node_modules")
    os.makedirs(node_modules_dir, exist_ok=True)

    for i, pkg in enumerate(args.packages, 1):
        print(f"\n==== [{i}/{len(args.packages)}] {pkg} ====")
        success = install_package(pkg, node_modules_dir)
        if success and args.zip:
            zip_package_folder(pkg.split('/')[-1], node_modules_dir, out_dir)

    print(f"\n🎉 完了: 出力先 → {os.path.abspath(out_dir)}")

if __name__ == "__main__":
    main()
