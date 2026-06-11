# utils/system_time_sync.py
from datetime import datetime
import subprocess


MIN_VALID_YEAR = 2024
MAX_VALID_YEAR = 2099


def build_valid_result_datetime(year, month, day, hours, minutes, seconds):
    """
    Muodostaa ForTest-tuloksen aikakentistä datetime-olion.
    Palauttaa None, jos kentät eivät muodosta järkevää päivämäärää/kellonaikaa.
    """
    try:
        year = int(year)
        month = int(month)
        day = int(day)
        hours = int(hours)
        minutes = int(minutes)
        seconds = int(seconds)

        if year < MIN_VALID_YEAR or year > MAX_VALID_YEAR:
            return None

        return datetime(year, month, day, hours, minutes, seconds)
    except Exception:
        return None


def sync_system_time_from_fortest_result(result_datetime):
    """
    Asettaa Raspberryn järjestelmäajan ForTestin tulosajan mukaan.

    Vaatii käytännössä sudo-oikeuden ilman salasanaa komennolle:
    /usr/bin/date tai /bin/date riippuen Raspberry Pi OS -asennuksesta.

    sudo -n estää ohjelmaa jäämästä odottamaan salasanaa.
    """
    if result_datetime is None:
        return False, "ForTest-aika ei ole kelvollinen"

    time_text = result_datetime.strftime("%Y-%m-%d %H:%M:%S")

    commands = [
        ["sudo", "-n", "/usr/bin/date", "-s", time_text],
        ["sudo", "-n", "/bin/date", "-s", time_text],
    ]

    last_error = ""

    for command in commands:
        try:
            completed = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=3,
            )

            if completed.returncode == 0:
                return True, f"Raspberryn aika asetettu ForTest-tuloksesta: {time_text}"

            last_error = (completed.stderr or completed.stdout or "").strip()
        except FileNotFoundError:
            last_error = f"Komentoa ei löydy: {command[2]}"
        except subprocess.TimeoutExpired:
            last_error = "Ajan asetus aikakatkaistiin"
        except Exception as e:
            last_error = str(e)

    if not last_error:
        last_error = "tuntematon virhe"

    return False, f"Raspberryn ajan asetus epäonnistui: {last_error}"
