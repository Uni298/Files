import os
import sys
import requests
import tarfile
import shutil
from urllib.request import urlretrieve
import zipfile

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
        print(f"❌ パッケージ情報取得失敗: {package_name} ({e})")
        return None

def download_tarball(url, dest_path):
    try:
        print(f"⬇️ ダウンロード中: {url}")
        urlretrieve(url, dest_path)
        print(f"✅ ダウンロード成功: {dest_path}")
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
                print(f"📁 配置成功: {extract_to}")
            else:
                print(f"⚠️ 解凍内容に 'package/' が見つかりませんでした")
        shutil.rmtree(temp_dir)
        os.remove(tar_path)
    except Exception as e:
        print(f"❌ 解凍・配置失敗: {e}")

def zip_package_folder(package_name, node_modules_dir, output_dir):
    folder_path = os.path.join(node_modules_dir, package_name)
    zip_name = f"{package_name}.zip"
    output_path = os.path.join(output_dir, zip_name)

    print(f"\n🗜 ZIPアーカイブ作成中: {output_path}")

    if not os.path.exists(folder_path):
        print(f"❌ フォルダが存在しません: {folder_path}")
        return

    os.makedirs(output_dir, exist_ok=True)

    try:
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, folder_path)
                    zipf.write(full_path, rel_path)
        print(f"✅ ZIP作成成功: {output_path}")
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

def main():
    print("📦 空白区切りで npm パッケージ名を入力（例: express discord.js -zip -out bot）")
    user_input = input(">> ").strip().split()

    # オプション解析
    should_zip = "-zip" in user_input
    out_dir = "./"  # デフォルト
    if "-out" in user_input:
        try:
            out_index = user_input.index("-out")
            out_dir = user_input[out_index + 1]
        except IndexError:
            print("❌ -out の後に出力先ディレクトリが必要です")
            return

    # node_modules の出力先
    node_modules_dir = os.path.join(out_dir, "node_modules")

    # パッケージ名だけ抽出
    packages = []
    skip_next = False
    for i, token in enumerate(user_input):
        if skip_next:
            skip_next = False
            continue
        if token == "-zip":
            continue
        elif token == "-out":
            skip_next = True
            continue
        else:
            packages.append(token)

    if not packages:
        print("❗ インストールするパッケージが指定されていません")
        return

    for i, pkg in enumerate(packages, 1):
        print(f"\n==== [{i}/{len(packages)}] {pkg} ====")
        success = install_package(pkg, node_modules_dir)
        if should_zip and success:
            zip_package_folder(pkg.split('/')[-1], node_modules_dir, out_dir)

    print(f"\n🎉 全処理が完了しました → {os.path.abspath(out_dir)}")

if __name__ == "__main__":
    main()
