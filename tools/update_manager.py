#!/usr/bin/env python3

import os
import re
import subprocess
import sys
import time
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMessageBox


REPO_DIR = Path(
    os.environ.get(
        "PAINETESTERI_REPO",
        str(Path.home() / "painetesteri_hmi"),
    )
).expanduser()

STATE_DIR = Path.home() / ".local" / "share" / "painetesteri_hmi"
LAST_GOOD_COMMIT_FILE = STATE_DIR / "last_good_commit"
SERVICE_NAME = os.environ.get("PAINETESTERI_SERVICE", "painetestaus.service")

COMMIT_RE = re.compile(r"^[0-9a-fA-F]{40}$")


class MaintenanceError(RuntimeError):
    pass


def run_command(args, cwd=None, timeout=30, check=True):
    try:
        result = subprocess.run(
            args,
            cwd=str(cwd) if cwd else None,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise MaintenanceError(
            f"Komento aikakatkaistiin: {' '.join(args)}"
        ) from exc
    except OSError as exc:
        raise MaintenanceError(
            f"Komentoa ei voitu suorittaa: {' '.join(args)}\n{exc}"
        ) from exc

    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        if detail:
            raise MaintenanceError(detail)
        raise MaintenanceError(
            f"Komento epäonnistui ({result.returncode}): {' '.join(args)}"
        )

    return result


def git(*args, timeout=30, check=True):
    return run_command(
        ["git", *args],
        cwd=REPO_DIR,
        timeout=timeout,
        check=check,
    )


def short_commit(commit):
    return commit[:8]


def require_repository():
    if not REPO_DIR.is_dir():
        raise MaintenanceError(
            f"Ohjelmahakemistoa ei löytynyt:\n{REPO_DIR}"
        )

    result = git("rev-parse", "--is-inside-work-tree")
    if result.stdout.strip() != "true":
        raise MaintenanceError(
            f"Hakemisto ei ole Git-repositorio:\n{REPO_DIR}"
        )


def require_main_branch():
    result = git("branch", "--show-current")
    branch = result.stdout.strip()

    if branch != "main":
        raise MaintenanceError(
            "Päivitys/palautus keskeytettiin.\n\n"
            f"Aktiivinen Git-haara on '{branch or 'detached HEAD'}', ei 'main'."
        )


def require_clean_worktree():
    result = git("status", "--porcelain")
    dirty = result.stdout.strip()

    if dirty:
        preview = "\n".join(dirty.splitlines()[:8])
        if len(dirty.splitlines()) > 8:
            preview += "\n..."

        raise MaintenanceError(
            "Päivitys/palautus keskeytettiin, koska Raspilla on "
            "paikallisia Git-muutoksia. Mitään ei muutettu.\n\n"
            f"{preview}"
        )


def current_commit():
    commit = git("rev-parse", "HEAD").stdout.strip()
    if not COMMIT_RE.fullmatch(commit):
        raise MaintenanceError("Nykyistä Git-versiota ei voitu tunnistaa.")
    return commit


def origin_main_commit():
    commit = git("rev-parse", "origin/main").stdout.strip()
    if not COMMIT_RE.fullmatch(commit):
        raise MaintenanceError("GitHubin main-versiota ei voitu tunnistaa.")
    return commit


def write_last_good_commit(commit):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    temp_file = LAST_GOOD_COMMIT_FILE.with_suffix(".tmp")
    temp_file.write_text(commit + "\n", encoding="utf-8")
    os.replace(temp_file, LAST_GOOD_COMMIT_FILE)


def read_last_good_commit():
    if not LAST_GOOD_COMMIT_FILE.exists():
        raise MaintenanceError(
            "Palautettavaa versiota ei ole vielä tallennettu.\n\n"
            "Tiedosto syntyy automaattisesti ensimmäisen tämän työkalun "
            "kautta tehdyn päivityksen yhteydessä."
        )

    commit = LAST_GOOD_COMMIT_FILE.read_text(encoding="utf-8").strip()

    if not COMMIT_RE.fullmatch(commit):
        raise MaintenanceError(
            "Tallennettu palautusversio on virheellinen."
        )

    probe = git("cat-file", "-e", f"{commit}^{{commit}}", check=False)
    if probe.returncode != 0:
        raise MaintenanceError(
            "Tallennettua palautuscommittia ei löydy tästä Git-repositoriosta."
        )

    return commit


def reset_to(commit):
    git("reset", "--hard", commit, timeout=30)


def restart_service():
    restart = run_command(
        ["sudo", "-n", "systemctl", "restart", SERVICE_NAME],
        timeout=30,
        check=False,
    )

    if restart.returncode != 0:
        detail = (restart.stderr or restart.stdout or "").strip()
        if "password" in detail.lower():
            raise MaintenanceError(
                "Palvelun uudelleenkäynnistys vaatii sudo-salasanan.\n\n"
                "Kosketuskäyttöä varten systemctl-restartille täytyy sallia "
                "salasanaton sudo."
            )
        raise MaintenanceError(
            "Palvelun uudelleenkäynnistys epäonnistui."
            + (f"\n\n{detail}" if detail else "")
        )

    for _ in range(10):
        active = run_command(
            ["systemctl", "is-active", "--quiet", SERVICE_NAME],
            timeout=5,
            check=False,
        )
        if active.returncode == 0:
            return
        time.sleep(0.5)

    status = run_command(
        ["systemctl", "status", SERVICE_NAME, "--no-pager", "--lines=8"],
        timeout=10,
        check=False,
    )
    detail = (status.stdout or status.stderr or "").strip()

    raise MaintenanceError(
        f"{SERVICE_NAME} ei jäänyt aktiiviseksi."
        + (f"\n\n{detail}" if detail else "")
    )


def configure_message_box(box):
    box.setWindowFlags(
        box.windowFlags()
        | Qt.WindowStaysOnTopHint
    )
    box.setStyleSheet(
        """
        QMessageBox {
            background-color: white;
        }
        QMessageBox QLabel {
            min-width: 720px;
            font-size: 24px;
            line-height: 1.25;
        }
        QMessageBox QPushButton {
            min-width: 210px;
            min-height: 72px;
            padding: 8px 18px;
            font-size: 22px;
            font-weight: 600;
        }
        """
    )


def show_info(title, text):
    box = QMessageBox()
    configure_message_box(box)
    box.setIcon(QMessageBox.Information)
    box.setWindowTitle(title)
    box.setText(text)
    box.setStandardButtons(QMessageBox.Ok)
    box.button(QMessageBox.Ok).setText("SULJE")
    box.exec_()


def show_error(title, text):
    box = QMessageBox()
    configure_message_box(box)
    box.setIcon(QMessageBox.Critical)
    box.setWindowTitle(title)
    box.setText(text)
    box.setStandardButtons(QMessageBox.Ok)
    box.button(QMessageBox.Ok).setText("SULJE")
    box.exec_()


def ask(title, text, yes_text):
    box = QMessageBox()
    configure_message_box(box)
    box.setIcon(QMessageBox.Question)
    box.setWindowTitle(title)
    box.setText(text)
    box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    box.button(QMessageBox.Yes).setText(yes_text)
    box.button(QMessageBox.No).setText("PERUUTA")
    box.setDefaultButton(QMessageBox.No)
    return box.exec_() == QMessageBox.Yes


def ask_immediate_rollback(current, previous, reason):
    box = QMessageBox()
    configure_message_box(box)
    box.setIcon(QMessageBox.Critical)
    box.setWindowTitle("Päivityksen käynnistys epäonnistui")
    box.setText(
        "Uusi Git-versio asennettiin, mutta painetestauspalvelu ei "
        "käynnistynyt oikein.\n\n"
        f"Uusi versio: {short_commit(current)}\n"
        f"Palautettava: {short_commit(previous)}\n\n"
        f"{reason}\n\n"
        "Palautetaanko edellinen versio heti?"
    )
    box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    box.button(QMessageBox.Yes).setText("PALAUTA HETI")
    box.button(QMessageBox.No).setText("JÄTÄ NYKYISEKSI")
    box.setDefaultButton(QMessageBox.Yes)
    return box.exec_() == QMessageBox.Yes


def update_program():
    require_repository()
    require_main_branch()
    require_clean_worktree()

    before = current_commit()

    git("fetch", "origin", "main", timeout=90)
    target = origin_main_commit()

    if target == before:
        show_info(
            "Painetesteri",
            "Ohjelma on jo ajan tasalla.\n\n"
            f"Nykyinen versio: {short_commit(before)}",
        )
        return

    ancestor = git(
        "merge-base",
        "--is-ancestor",
        before,
        target,
        check=False,
    )

    if ancestor.returncode != 0:
        raise MaintenanceError(
            "Päivitys keskeytettiin, koska nykyinen versio ei ole "
            "GitHubin main-haaran suora edeltäjä.\n\n"
            "Mitään ei muutettu."
        )

    if not ask(
        "Päivitä painetesteri",
        "GitHubissa on uusi ohjelmaversio.\n\n"
        f"Nykyinen: {short_commit(before)}\n"
        f"Uusi: {short_commit(target)}\n\n"
        "Nykyinen versio tallennetaan palautusta varten. "
        "Päivitetäänkö ohjelma?",
        "PÄIVITÄ",
    ):
        return

    write_last_good_commit(before)
    reset_to(target)

    try:
        restart_service()
    except MaintenanceError as exc:
        if ask_immediate_rollback(
            current=target,
            previous=before,
            reason=str(exc),
        ):
            try:
                reset_to(before)
                restart_service()
            except MaintenanceError as rollback_exc:
                raise MaintenanceError(
                    "Automaattinen palautus epäonnistui.\n\n"
                    f"{rollback_exc}"
                ) from rollback_exc

            show_info(
                "Edellinen versio palautettu",
                "Päivitys peruttiin ja edellinen ohjelmaversio "
                "palautettiin onnistuneesti.\n\n"
                f"Käytössä: {short_commit(before)}",
            )
            return

        raise

    show_info(
        "Päivitys onnistui",
        "Painetesterin ohjelma päivitettiin ja palvelu käynnistyi.\n\n"
        f"Uusi versio: {short_commit(target)}\n"
        f"Palautusversio: {short_commit(before)}",
    )


def rollback_program():
    require_repository()
    require_main_branch()
    require_clean_worktree()

    current = current_commit()
    target = read_last_good_commit()

    if current == target:
        show_info(
            "Painetesteri",
            "Palautusversio on jo käytössä.\n\n"
            f"Nykyinen versio: {short_commit(current)}",
        )
        return

    if not ask(
        "Palauta edellinen versio",
        "Palautetaanko ennen viimeisintä päivitystä käytössä ollut "
        "ohjelmaversio?\n\n"
        f"Nykyinen: {short_commit(current)}\n"
        f"Palautettava: {short_commit(target)}",
        "PALAUTA",
    ):
        return

    reset_to(target)

    try:
        restart_service()
    except MaintenanceError as exc:
        # Jos myös palautettu versio ei käynnisty, palauta Git takaisin siihen
        # committiin, joka oli käytössä ennen rollback-painallusta.
        reset_to(current)
        try:
            restart_service()
        except MaintenanceError:
            pass

        raise MaintenanceError(
            "Palautettu versio ei käynnistynyt oikein, joten Git palautettiin "
            "takaisin lähtöversioon.\n\n"
            f"{exc}"
        ) from exc

    show_info(
        "Palautus onnistui",
        "Edellinen ohjelmaversio palautettiin ja palvelu käynnistyi.\n\n"
        f"Käytössä: {short_commit(target)}",
    )


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {"update", "rollback"}:
        raise SystemExit(
            "Käyttö: update_manager.py update|rollback"
        )

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app = QApplication(sys.argv)
    app.setApplicationName("Painetesterin ylläpito")

    try:
        if sys.argv[1] == "update":
            update_program()
        else:
            rollback_program()

    except MaintenanceError as exc:
        show_error("Toiminto epäonnistui", str(exc))
        sys.exit(1)

    except Exception as exc:
        show_error(
            "Odottamaton virhe",
            f"Toiminto keskeytettiin.\n\n{exc}",
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
