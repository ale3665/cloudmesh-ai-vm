import pathlib
import shutil
import subprocess


def ssh_key(tmp_path):
    key_path = tmp_path / "id_rsa"
    pub_key_path = tmp_path / "id_rsa.pub"
    result = subprocess.run(
        ["ssh-keygen", "-t", "rsa", "-b", "2048", "-f", str(key_path), "-N", ""],
        check=True,
        capture_output=True,
        text=True,
    )
    return str(key_path), str(pub_key_path), result.stdout


# Create a real temporary directory to act as tmp_path
tmp_dir = pathlib.Path("./tmp_ssh_test")
tmp_dir.mkdir(exist_ok=True)

try:
    priv, pub, output = ssh_key(tmp_dir)
    print("--- Subprocess Stdout ---")
    print(output)
    print("--- Return Values ---")
    print(f"Private Key Path: {priv}")
    print(f"Public Key Path: {pub}")

    print("\n--- Public Key Content ---")
    with open(pub, "r") as f:
        print(f.read())
finally:
    # Cleanup
    shutil.rmtree(tmp_dir)
