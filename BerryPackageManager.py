import os;
import sys;
import requests;
import base64;
import time;
import random;
import subprocess;
from pathlib import Path;
from rich.console import Console;
from rich.table import Table;
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn;

console = Console();

# ================================
# Paths
# ================================
BERRY_DIR = Path("C:/Berry");
PKG_DIR = BERRY_DIR / "packages";
DEP_DIR = BERRY_DIR / "dependencies";
EXT_DIR = BERRY_DIR / "extracted";
ACCOUNT_FILE = BERRY_DIR / "account.txt";

# ================================
# Setup
# ================================
def setup_directories():
    for d in [BERRY_DIR, PKG_DIR, DEP_DIR, EXT_DIR]:
        d.mkdir(parents=True, exist_ok=True);

def get_hidden_input(prompt=""):
    import msvcrt;
    console.print(prompt, end="", style="bold cyan");
    pw = "";
    while True:
        ch = msvcrt.getwch();
        if ch in ('\r', '\n'):
            print();
            break;
        elif ch == '\x03':
            raise KeyboardInterrupt;
        elif ch == '\x08':
            if len(pw) > 0:
                pw = pw[:-1];
                console.print("\b \b", end="", style="bold cyan", flush=True);
        else:
            if 32 <= ord(ch) <= 126:
                pw += ch;
                console.print("*", end="", style="bold cyan", flush=True);
    return base64.b64encode(pw.encode()).decode();

def setup_account():
    if not ACCOUNT_FILE.exists():
        console.print("[bold cyan]== Account Creation Setup ==[/bold cyan]");
        username = input("username: ");
        passcode = get_hidden_input("passcode: ");
        confirm = get_hidden_input("confirm passcode: ");
        if passcode != confirm:
            console.print("[bold red]Passcodes do not match! Restart Berry.[/bold red]");
            sys.exit(1);
        with open(ACCOUNT_FILE, "w") as f:
            f.write(f"{username}\n{passcode}\n");
        console.print(f"[bold green]Welcome, {username}![/bold green]");
        return username;
    else:
        with open(ACCOUNT_FILE, "r") as f:
            return f.readline().strip();

# ================================
# Metadata Reader
# ================================
def read_metadata(pkg_path):
    metadata = {};
    try:
        with open(pkg_path, "r") as f:
            lines = f.readlines();
        in_meta = False;
        for line in lines:
            if line.strip() == "# ===METADATA===":
                in_meta = True;
                continue;
            if line.strip() == "# ===END METADATA===":
                break;
            if in_meta and ":" in line:
                key, val = line.strip("# ").split(":", 1);
                metadata[key.strip()] = val.strip();
    except Exception as e:
        console.print(f"[bold red]Failed to read metadata: {e}[/bold red]");
    return metadata;

# ================================
# Commands
# ================================
def fetch_package(package_name):
    url = f"https://raw.githubusercontent.com/Berry-Official/repos/main/{package_name}.bry";
    dest = PKG_DIR / f"{package_name}.bry";
    try:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn()) as progress:
            task = progress.add_task(f"Fetching {package_name}...", total=100);
            for i in range(0, 101, 20):
                time.sleep(0.2);
                progress.update(task, advance=20);
        r = requests.get(url);
        if r.status_code == 200:
            with open(dest, "w", encoding="utf-8") as f:
                f.write(r.text);
            console.print(f"[bold green]Fetched {package_name} from Berry-Official![/bold green]");
        else:
            console.print(f"[bold red]Error: Package not found on Berry-Official.[/bold red]");
    except Exception as e:
        console.print(f"[bold red]Error fetching package: {e}[/bold red]");

def rid_package(package_name):
    path = PKG_DIR / f"{package_name}.bry";
    if path.exists():
        path.unlink();
        console.print(f"[bold yellow]Removed {package_name}[/bold yellow]");
    else:
        console.print("[bold red]Package not installed[/bold red]");

def list_packages():
    table = Table(title="Installed Packages");
    table.add_column("Name", style="cyan");
    table.add_column("Version", style="green");
    table.add_column("Description", style="yellow");
    for pkg in PKG_DIR.glob("*.bry"):
        meta = read_metadata(pkg);
        table.add_row(
            meta.get("name", pkg.stem),
            meta.get("version", "unknown"),
            meta.get("description", "no description")
        );
    console.print(table);

def run_package(package_name):
    path = PKG_DIR / f"{package_name}.bry";
    if path.exists():
        ext = path.suffix.lower();
        try:
            if ext == ".py":
                subprocess.run([sys.executable, str(path)]);
            elif ext == ".js":
                subprocess.run(["node", str(path)]);
            elif ext == ".sh":
                subprocess.run(["bash", str(path)]);
            elif ext == ".bat" or ext == ".exe":
                subprocess.run([str(path)]);
            elif ext == ".bs":
                run_berry_script(path);
            else:
                console.print(f"[bold red]Cannot run files with {ext} extension[/bold red]");
                return;
            console.print(f"[bold green]Executed {package_name}![/bold green]");
        except Exception as e:
            console.print(f"[bold red]Execution error: {e}[/bold red]");
    else:
        console.print("[bold red]Package not installed[/bold red]");

def run_berry_script(path):
    # Simple line-by-line runner for .bs files
    try:
        with open(path, "r") as f:
            lines = f.readlines();
        for line in lines:
            line = line.strip();
            if line.startswith("print("):
                msg = line[6:-1];
                console.print(msg);
            elif line.startswith("shell("):
                cmd = line[6:-1];
                subprocess.run(cmd, shell=True);
        console.print("[bold green]BerryScript executed successfully![/bold green]");
    except Exception as e:
        console.print(f"[bold red]BerryScript runtime error: {e}[/bold red]");

def ping():
    console.print("[bold cyan]Berry is online![/bold cyan]");

def latest(package_name):
    path = PKG_DIR / f"{package_name}.bry";
    if path.exists():
        meta = read_metadata(path);
        console.print(f"[bold green]Latest version: {meta.get('version', 'unknown')}[/bold green]");
    else:
        console.print("[bold red]Package not installed[/bold red]");

def oldest(package_name):
    console.print(f"[bold yellow]Oldest version of {package_name} = 1.0.0[/bold yellow]");

def previews(package_name):
    path = PKG_DIR / f"{package_name}.bry";
    if path.exists():
        meta = read_metadata(path);
        console.print(f"[bold cyan]Preview: {meta.get('description', 'No preview')}[/bold cyan]");
    else:
        console.print("[bold red]Package not installed[/bold red]");

def add_to_path():
    path_str = str(BERRY_DIR);
    subprocess.run(f'setx PATH "%PATH%;{path_str}"', shell=True);
    console.print(f"[bold green]{BERRY_DIR} added to system PATH[/bold green]");

def delete_account():
    if ACCOUNT_FILE.exists():
        ACCOUNT_FILE.unlink();
        console.print("[bold yellow]Account deleted! Please create a new account.[/bold yellow]");

def clear_screen():
    os.system("cls" if os.name=="nt" else "clear");

def show_version():
    console.print("[bold cyan]Berry Package Manager v1.0.0 - The King Penguin[/bold cyan]");

# ================================
# CLI
# ================================
def berry_cli(username):
    while True:
        try:
            cmd = input(f"{username}> ").strip().split();
            if not cmd:
                continue;
            action = cmd[0];
            if action == "berry" and len(cmd) >= 2:
                sub = cmd[1];
                if sub == "fetch" and len(cmd) == 3:
                    fetch_package(cmd[2]);
                elif sub == "rid" and len(cmd) == 3:
                    rid_package(cmd[2]);
                elif sub == "list":
                    list_packages();
                elif sub == "run" and len(cmd) == 3:
                    run_package(cmd[2]);
                elif sub == "erase":
                    clear_screen();
                elif sub == "ping":
                    ping();
                elif sub == "latest" and len(cmd) == 3:
                    latest(cmd[2]);
                elif sub == "oldest" and len(cmd) == 3:
                    oldest(cmd[2]);
                elif sub == "previews" and len(cmd) == 3:
                    previews(cmd[2]);
                elif sub == "downgrade" and len(cmd) == 4:
                    console.print(f"[bold yellow]Attempting to downgrade {cmd[2]} to {cmd[3]}...[/bold yellow]");
                elif sub == "account" and len(cmd) >= 3:
                    if cmd[2] == "del":
                        delete_account();
                        username = setup_account();
                    elif cmd[2] == "new":
                        username = setup_account();
                elif sub == "addpath":
                    add_to_path();
                elif sub == "ver":
                    show_version();
                elif sub == "help":
                    console.print("[bold cyan]Commands:\n"
                                  "  berry fetch <pkg>;            Fetch & install a package\n"
                                  "  berry rid <pkg>;              Remove a package\n"
                                  "  berry list;                   List installed packages\n"
                                  "  berry run <pkg>;              Run a package\n"
                                  "  berry erase;                  Clear the screen\n"
                                  "  berry ping;                   Test connectivity\n"
                                  "  berry latest <pkg>;           Show latest version\n"
                                  "  berry oldest <pkg>;           Show oldest version\n"
                                  "  berry previews <pkg>;         Show preview/description\n"
                                  "  berry downgrade <pkg> <ver>; Downgrade a package\n"
                                  "  berry account del/new;        Delete or create account\n"
                                  "  berry addpath;                Add Berry folder to PATH\n"
                                  "  berry ver;                    Show version info[/bold cyan]\n"
                                  " Note: Don't use semicolons it will cause errors!");
                                  
                elif sub == "exit":
                    console.print("[bold yellow]Goodbye![/bold yellow]");
                    break;
                else:
                    console.print("[bold red]The command you typed was unrecognised. Use: berry help for a list of commands.[/bold red]");
            else:
                console.print("[bold red]The command you typed was unrecognised. Use: berry help for a list of commands.[/bold red]");
        except KeyboardInterrupt:
            break;

# ================================
# Main
# ================================
if __name__ == "__main__":
    setup_directories();
    username = setup_account();
    show_version();
    berry_cli(username);
