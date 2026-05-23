"""
TradeTrend MVP kurulum scripti.
Sanal ortam oluşturur, paketleri yükler ve temel kontrolü yapar.
"""

import subprocess
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(BASE_DIR, "venv")


def run(cmd: str, check: bool = True) -> int:
    print(f"  $ {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=BASE_DIR)
    if check and result.returncode != 0:
        print(f"  ❌ Hata (kod {result.returncode})")
        sys.exit(result.returncode)
    return result.returncode


def main():
    print("=" * 55)
    print("  TradeTrend MVP — Kurulum Başlıyor")
    print("=" * 55)

    # 1. Sanal ortam
    if not os.path.exists(VENV_DIR):
        print("\n1️⃣  Sanal ortam oluşturuluyor...")
        run(f"{sys.executable} -m venv venv")
    else:
        print("\n1️⃣  Sanal ortam zaten mevcut.")

    # 2. pip yükselt
    print("\n2️⃣  pip güncelleniyor...")
    pip = os.path.join(VENV_DIR, "Scripts", "pip") if os.name == "nt" else os.path.join(VENV_DIR, "bin", "pip")
    run(f'"{pip}" install --upgrade pip -q')

    # 3. Bağımlılıkları yükle
    print("\n3️⃣  Bağımlılıklar yükleniyor (bu birkaç dakika sürebilir)...")
    run(f'"{pip}" install -r requirements.txt -q')

    # 4. .env dosyası
    env_file = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(env_file):
        print("\n4️⃣  .env dosyası oluşturuluyor...")
        with open(os.path.join(BASE_DIR, ".env.example")) as f:
            content = f.read()
        with open(env_file, "w") as f:
            f.write(content)
        print("  ⚠️  .env dosyasını kendi ayarlarınızla düzenleyin!")
    else:
        print("\n4️⃣  .env dosyası zaten mevcut.")

    # 5. Demo testi
    print("\n5️⃣  Demo pipeline testi...")
    python = os.path.join(VENV_DIR, "Scripts", "python") if os.name == "nt" else os.path.join(VENV_DIR, "bin", "python")
    run(f'"{python}" run_pipeline.py --demo')

    print("\n" + "=" * 55)
    print("  ✅ Kurulum tamamlandı!")
    print("=" * 55)
    print("\nSonraki adımlar:")
    print(f"  1. .env dosyasını düzenle: {env_file}")
    print("  2. PostgreSQL kur ve DATABASE_URL'i güncelle")
    print("  3. Dashboard başlat:")
    print(f"     {python} -m streamlit run dashboard/streamlit_app.py")
    print()


if __name__ == "__main__":
    main()
