"""Painetesterin paikallinen tapahtumaloki ja valinnainen GitHub-synkronointi.

Ei kirjoita lähdekoodin git-työpuuhun. Lokeissa ei ole sarjanumeroita,
mittaustuloksia, käyttäjätunnuksia tai vapaamuotoista tekstisisältöä.
Repositorion ollessa JULKINEN myös diagnostics-haaraan viedyt lokit
ovat julkisia. Automaattinen lähetys aktivoituu vain erillisellä tokenilla.
"""

import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

REPOSITORY = "akiriik/paintetesteri_hmi_raspi_remote"
UPLOAD_BRANCH = "diagnostics"
UPLOAD_INTERVAL_SECONDS = 300
MAX_FILE_BYTES = 1024 * 1024

DEFAULT_DIRECTORY = Path.home() / ".local" / "share" / "painetesteri_hmi" / "runtime_logs"
DEFAULT_TOKEN_FILE = Path.home() / ".config" / "painetesteri_hmi" / "github_token"

# Vain etukäteen valitut kentät. Älä tallenna raakaa ForTest-tulosta,
# valmistettavaa tuotetta, käyttäjätietoja tai Modbus-rekisteritaulukoita.
ALLOWED_KEYS = frozenset({
    "station", "program", "phase", "action", "reason", "status",
    "previous_status", "jig_status", "jig_error", "owner", "success",
    "running", "pending_start", "waiting_result", "manual_busy",
    "auto_busy", "pressure_release", "opta_connected",
    "for_test_connected", "elapsed_ms", "register", "value",
    "command", "generation", "release_ready", "error_code",
})

_logger = None
_logger_lock = threading.Lock()


def _safe_string(value):
    # Ei vapaamuotoisia sarjanumeroita tai mittaustuloksia.
    if not isinstance(value, str):
        return None
    value = value[:80]
    if re.fullmatch(r"[A-Za-z0-9_.:\-]{1,80}", value):
        return value
    return None


def _sanitize_fields(fields):
    data = {}
    for key, value in fields.items():
        if key not in ALLOWED_KEYS or value is None:
            continue
        if type(value) in (bool, int):
            data[key] = value
        elif isinstance(value, str):
            safe = _safe_string(value)
            if safe is not None:
                data[key] = safe
    return data


class RuntimeDiagnostics:
    def __init__(
        self, directory=None, token_file=None, upload_interval=UPLOAD_INTERVAL_SECONDS,
        start_thread=True,
    ):
        self.directory = Path(directory or DEFAULT_DIRECTORY)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.token_file = Path(token_file or DEFAULT_TOKEN_FILE)
        self.upload_interval = upload_interval
        # Julkisessa repossa ei julkaista koneen nimeä.
        self.device = "unit-" + hashlib.sha256(
            socket.gethostname().encode("utf-8")
        ).hexdigest()[:12]
        self._write_lock = threading.RLock()
        self._stop = threading.Event()
        self._wake_upload = threading.Event()
        self._uploaded_hashes_path = self.directory / "uploaded_hashes.json"
        self._uploaded_hashes = self._load_uploaded_hashes()
        self._thread = None
        self._last_upload_attempt = 0.0

        if start_thread:
            self._thread = threading.Thread(
                target=self._upload_loop,
                name="painetesteri-diagnostic-upload",
                daemon=True,
            )
            self._thread.start()

    def _load_uploaded_hashes(self):
        try:
            data = json.loads(self._uploaded_hashes_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def record(self, event, **fields):
        try:
            safe_event = _safe_string(event)
            if safe_event is None:
                return
            now = datetime.now(timezone.utc)
            payload = {
                "utc": now.isoformat(timespec="milliseconds"),
                "event": safe_event,
                **_sanitize_fields(fields),
            }
            data = json.dumps(payload, ensure_ascii=True, separators=(",", ":")) + "\n"
            path = self.directory / (now.strftime("%Y%m%d-%H") + ".jsonl")
            with self._write_lock:
                with path.open("a", encoding="utf-8") as handle:
                    handle.write(data)
                    handle.flush()
                    # Vikatapahtumat säilyvät paremmin myös sähkökatkossa.
                    if "error" in safe_event or "denied" in safe_event or "timeout" in safe_event:
                        os.fsync(handle.fileno())
            if "error" in safe_event or "denied" in safe_event or "timeout" in safe_event:
                self._wake_upload.set()
        except Exception as exc:
            print(f"Diagnostiikkalokin kirjoitusvirhe: {exc}")

    def _token(self):
        try:
            metadata = self.token_file.stat()
            if metadata.st_mode & 0o077:
                return None  # Tunniste ei saa näkyä muille koneen käyttäjille.
            token = self.token_file.read_text(encoding="utf-8").strip()
            return token if token.startswith(("github_pat_", "ghp_")) else None
        except OSError:
            return None

    @staticmethod
    def _github_request(url, token, method="GET", data=None):
        headers = {
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "painetesteri-hmi-diagnostics",
        }
        if data is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(data, separators=(",", ":")).encode("utf-8")
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(request, timeout=12) as response:
            return json.loads(response.read().decode("utf-8"))

    def _upload_file(self, file_path, token):
        # Ota talteen yksi konsistentti tilannekuva ilman ulkoista lukitusta
        # koko HTTP-pyynnön ajaksi. Samanaikaiset uudet rivit lähtevät
        # seuraavassa lähetyksessä.
        with self._write_lock:
            content = file_path.read_bytes()
        if not content or len(content) > MAX_FILE_BYTES:
            return False

        digest = hashlib.sha256(content).hexdigest()
        if self._uploaded_hashes.get(file_path.name) == digest:
            return True

        date, hour = file_path.stem.split("-")
        remote_path = f"runtime-logs/{self.device}/{date}/{hour}.jsonl"
        url = (
            f"https://api.github.com/repos/{REPOSITORY}/contents/"
            + urllib.parse.quote(remote_path, safe="/")
        )

        remote_sha = None
        try:
            info = self._github_request(url + "?ref=" + UPLOAD_BRANCH, token)
            remote_sha = info.get("sha")
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise

        request_data = {
            "message": f"diagnostics: {self.device} {date} {hour}",
            "branch": UPLOAD_BRANCH,
            "content": base64.b64encode(content).decode("ascii"),
        }
        if remote_sha:
            request_data["sha"] = remote_sha

        self._github_request(url, token, method="PUT", data=request_data)
        self._uploaded_hashes[file_path.name] = digest
        self._save_upload_state()
        return True

    def _save_upload_state(self):
        temp = self._uploaded_hashes_path.with_suffix(".tmp")
        temp.write_text(
            json.dumps(self._uploaded_hashes, sort_keys=True),
            encoding="utf-8",
        )
        os.replace(temp, self._uploaded_hashes_path)

    def upload_once(self):
        token = self._token()
        if not token:
            return False

        # Uusin tunti ensin ja aiemmat lähettämättömät tunnit vähitellen.
        # Tokenin lisääminen myöhemmin ei hukkaa vanhoja paikallisia lokeja.
        files = sorted(
            self.directory.glob("????????-??.jsonl"),
            key=lambda file: file.name,
            reverse=True,
        )
        recent = files[:2]
        backlog = [
            file for file in reversed(files[2:])
            if self._uploaded_hashes.get(file.name)
            != hashlib.sha256(file.read_bytes()).hexdigest()
        ]
        for file_path in recent + backlog[:10]:
            try:
                self._upload_file(file_path, token)
            except Exception as exc:
                print(f"Diagnostiikan GitHub-siirto epäonnistui: {type(exc).__name__}")
                return False
        return True

    def _upload_loop(self):
        while not self._stop.is_set():
            self._wake_upload.wait(self.upload_interval)
            self._wake_upload.clear()
            if self._stop.is_set():
                break

            # Vikatilanteiden jatkuvat tapahtumat eivät saa aiheuttaa
            # GitHubiin satoja committeja tai tiheää verkko-liikennettä.
            now = time.monotonic()
            if now - self._last_upload_attempt < 60.0:
                continue
            self._last_upload_attempt = now
            self.upload_once()

    def close(self):
        self._stop.set()
        self._wake_upload.set()


def configure_runtime_diagnostics(**kwargs):
    global _logger
    with _logger_lock:
        if _logger is None:
            _logger = RuntimeDiagnostics(**kwargs)
        return _logger


def record_event(event, **fields):
    logger = _logger
    if logger is not None:
        logger.record(event, **fields)


def close_runtime_diagnostics():
    global _logger
    with _logger_lock:
        if _logger is not None:
            _logger.close()
            _logger = None
